from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
import base64
import binascii
from urllib.parse import unquote
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.db.models import Q
from django.urls import reverse
from .models import Entry, Visibility, Comment
from authors.models import FollowRequestStatus, Author
from authors.serializers import AuthorSerializer
from .serializers import EntrySerializer, CommentSerializer


def resolve_author_or_404(identifier: str) -> Author:
    decoded = unquote(identifier).strip()
    candidates = []
    if decoded:
        candidates.append(decoded)

    trimmed = decoded.rstrip("/")
    if trimmed and trimmed not in candidates:
        candidates.append(trimmed)

    if "/" in trimmed:
        last_segment = trimmed.split("/")[-1]
        if last_segment and last_segment not in candidates:
            candidates.append(last_segment)

    for candidate in candidates:
        if not candidate:
            continue
        try:
            return Author.objects.get(id=candidate)
        except (Author.DoesNotExist, ValueError):
            continue

    raise Http404("Author not found")


LIKE_ID_SEPARATOR = "|"


def encode_like_identifier(object_type: str, object_id: str, author_id: str) -> str:
    raw_value = f"{object_type}{LIKE_ID_SEPARATOR}{object_id}{LIKE_ID_SEPARATOR}{author_id}"
    return base64.urlsafe_b64encode(raw_value.encode("utf-8")).decode("ascii").rstrip("=")


def decode_like_identifier(identifier: str) -> tuple[str, str, str]:
    padding = "=" * (-len(identifier) % 4)
    try:
        raw_value = base64.urlsafe_b64decode((identifier + padding).encode("ascii")).decode("utf-8")
        object_type, object_id, author_id = raw_value.split(LIKE_ID_SEPARATOR)
    except (ValueError, UnicodeDecodeError, binascii.Error):
        raise Http404("Like not found")
    return object_type, object_id, author_id


class LikeSerializerMixin:
    def _liker_display_name(self, author: Author) -> str:
        for attr in ("display_name", "username", "first_name"):
            value = getattr(author, attr, None)
            if value:
                return value
        return str(author)

    def _serialize_author(self, request, author: Author) -> dict:
        return AuthorSerializer(author, context={"request": request}).data

    def _build_entry_like_object(self, request, entry: Entry, liker: Author) -> dict:
        object_url = request.build_absolute_uri(reverse("api:entry-detail", args=[entry.id]))
        like_identifier = encode_like_identifier("entry", str(entry.id), str(liker.id))
        like_id = request.build_absolute_uri(reverse("api:liked-detail", args=[like_identifier]))
        entry_title = getattr(entry, "title", "") or "an entry"
        summary = f"{self._liker_display_name(liker)} likes {entry_title}"
        return {
            "type": "Like",
            "id": like_id,
            "summary": summary,
            "author": self._serialize_author(request, liker),
            "object": object_url,
        }

    def _build_comment_like_object(self, request, comment: Comment, liker: Author) -> dict:
        object_url = request.build_absolute_uri(reverse("api:comment-detail", args=[comment.id]))
        like_identifier = encode_like_identifier("comment", str(comment.id), str(liker.id))
        like_id = request.build_absolute_uri(reverse("api:liked-detail", args=[like_identifier]))
        entry_title = getattr(comment.entry, "title", "")
        target = f"a comment on {entry_title}" if entry_title else "a comment"
        summary = f"{self._liker_display_name(liker)} likes {target}"
        return {
            "type": "Like",
            "id": like_id,
            "summary": summary,
            "author": self._serialize_author(request, liker),
            "object": object_url,
        }

    def _retrieve_like_object(self, request, like_identifier: str, expected_author_id: str | None = None) -> dict:
        object_type, object_id, author_id = decode_like_identifier(like_identifier)
        liker = get_object_or_404(Author, id=author_id)
        if expected_author_id is not None and str(liker.id) != str(expected_author_id):
            raise Http404("Like not found")

        if object_type == "entry":
            target = get_object_or_404(Entry, id=object_id)
            if not target.liked_by.filter(id=liker.id).exists():
                raise Http404("Like not found")
            return self._build_entry_like_object(request, target, liker)

        if object_type == "comment":
            target = get_object_or_404(Comment, id=object_id)
            if not target.liked_by.filter(id=liker.id).exists():
                raise Http404("Like not found")
            return self._build_comment_like_object(request, target, liker)

        raise Http404("Like not found")


class PublicEntriesListView(generics.ListAPIView):
    serializer_class = EntrySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return (
            Entry.objects.filter(visibility=Visibility.PUBLIC)
            .select_related("author")
            .order_by("-published")
        )


class EntryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/entries/<uuid:entry_id>/
    Returns a single entry if visible to the requester.
    """
    permission_classes = [permissions.AllowAny]

    def get_object(self, entry_id):
        """
        Retrieves the entry object from the database and returns it unless incorrect visibility
        """
        entry = get_object_or_404(Entry, id=entry_id)

        if entry.visibility == "DELETED":
            raise Http404("Entry not found")

        if entry.visibility == Visibility.FRIENDS and (
            not self.request.user.is_authenticated
            or entry.author != self.request.user
            and not entry.author.follow_requests_sent.filter(
                followee=self.request.user, status=FollowRequestStatus.APPROVED
            ).exists()
        ):
            raise Http404("Entry not found")

        return entry

    def get(self, request, entry_id):
        entry = self.get_object(entry_id)
        serializer = EntrySerializer(entry, context={"request": request})
        return Response(serializer.data)


class MyEntriesListView(generics.ListCreateAPIView):
    """
    GET /api/author/<uuid:author_id>/entries/
    POST /api/author/<uuid:author_id>/entries/
    """
    serializer_class = EntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Entry.objects.filter(author=self.request.user)
            .exclude(visibility="DELETED")
            .order_by("-published")
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={"request": request})
        return Response({"type": "entries", "src": serializer.data})


class EntryEditDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET / PUT / DELETE /api/entries/<uuid:entry_id>/edit/
    Only the author can edit or delete their entry.
    """
    serializer_class = EntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        entry_id = self.kwargs.get("entry_id")
        entry = get_object_or_404(Entry, id=entry_id, author=self.request.user)

        if entry.visibility == "DELETED":
            raise Http404("Entry not found")

        return entry


class EntryLikesListView(LikeSerializerMixin, APIView):
    """
    GET /api/entries/<uuid:entry_id>/likes/
    Returns a paginated list of authors who liked the entry.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, entry_id):
        entry = get_object_or_404(Entry, id=entry_id)
        if not entry.can_view(request.user):
            raise Http404("Entry not found")

        page = max(1, int(request.query_params.get("page", 1)))
        size = max(1, int(request.query_params.get("size", 5)))
        start = (page - 1) * size
        end = start + size

        likes_qs = entry.liked_by.all()
        count = likes_qs.count()
        likes_page = likes_qs[start:end]

        likes_api_url = request.build_absolute_uri(reverse("api:entry-likes", args=[entry.id]))
        entry_html_url = request.build_absolute_uri(reverse("entries:view_entry", args=[entry.id]))

        src = [self._build_entry_like_object(request, entry, author) for author in likes_page]

        return Response(
            {
                "type": "likes",
                "web": entry_html_url,
                "id": likes_api_url,
                "page_number": page,
                "size": size,
                "count": count,
                "src": src,
            }
        )


class AuthorEntryLikesListView(LikeSerializerMixin, APIView):
    '''
    GET /api/author/<uuid:author_id>/entries/<uuid:entry_id>/likes/
    Returns a paginated list of authors who liked the entry.
    '''
    permission_classes = [permissions.AllowAny]

    def get(self, request, author_id, entry_id):
        entry = get_object_or_404(Entry, id=entry_id, author__id=author_id)
        if not entry.can_view(request.user):
            raise Http404("Entry not found")

        page = max(1, int(request.query_params.get("page", 1)))
        size = max(1, int(request.query_params.get("size", 5)))
        start = (page - 1) * size
        end = start + size

        likes_qs = entry.liked_by.all()
        count = likes_qs.count()
        likes_page = likes_qs[start:end]

        likes_api_url = request.build_absolute_uri(
            reverse("api:author-entry-likes", args=[entry.author.id, entry.id])
        )
        entry_html_url = request.build_absolute_uri(reverse("entries:view_entry", args=[entry.id]))

        src = [self._build_entry_like_object(request, entry, author) for author in likes_page]

        return Response(
            {
                "type": "likes",
                "web": entry_html_url,
                "id": likes_api_url,
                "page_number": page,
                "size": size,
                "count": count,
                "src": src,
            }
        )


class CommentLikesListView(LikeSerializerMixin, APIView):
    '''
    GET /api/entries/<uuid:entry_id>/comments/<uuid:comment_id>/likes/
    Returns a paginated list of authors who liked the comment.
    '''
    permission_classes = [permissions.AllowAny]

    def get(self, request, author_id, entry_id, comment_id):
        entry = get_object_or_404(Entry, id=entry_id, author__id=author_id)
        if not entry.can_view(request.user):
            raise Http404("Comment not found")
        comment = get_object_or_404(Comment, id=comment_id, entry=entry)

        page = max(1, int(request.query_params.get("page", 1)))
        size = max(1, int(request.query_params.get("size", 5)))
        start = (page - 1) * size
        end = start + size

        likes_qs = comment.liked_by.all()
        count = likes_qs.count()
        likes_page = likes_qs[start:end]

        likes_api_url = request.build_absolute_uri(
            reverse(
                "api:author-entry-comment-likes",
                args=[entry.author.id, entry.id, comment.id],
            )
        )
        entry_html_url = request.build_absolute_uri(reverse("entries:view_entry", args=[entry.id]))

        src = [self._build_comment_like_object(request, comment, author) for author in likes_page]

        return Response(
            {
                "type": "likes",
                "web": entry_html_url,
                "id": likes_api_url,
                "page_number": page,
                "size": size,
                "count": count,
                "src": src,
            }
        )


class AuthorLikedListView(LikeSerializerMixin, APIView):
    '''
    GET /api/author/<uuid:author_id>/liked/
    Returns a paginated list of all likes made by the author.
    '''
    permission_classes = [permissions.AllowAny]

    def get_author(self, identifier: str) -> Author:
        return resolve_author_or_404(identifier)

    def get(self, request, author_id):
        liker = self.get_author(str(author_id))
        return self._build_response(request, liker)

    def _build_response(self, request, liker: Author) -> Response:
        page = max(1, int(request.query_params.get("page", 1)))
        size = max(1, int(request.query_params.get("size", 10)))
        start = (page - 1) * size
        end = start + size

        entry_likes = (
            Entry.objects.filter(liked_by=liker)
            .select_related("author")
            .order_by("-published")
        )
        comment_likes = (
            Comment.objects.filter(liked_by=liker)
            .select_related("entry", "entry__author")
            .order_by("-created_at")
        )

        items = [self._build_entry_like_object(request, entry, liker) for entry in entry_likes]
        items.extend(
            self._build_comment_like_object(request, comment, liker) for comment in comment_likes
        )

        count = len(items)
        src = items[start:end]

        liked_api_url = request.build_absolute_uri(reverse("api:author-liked", args=[liker.id]))

        return Response(
            {
                "type": "likes",
                "id": liked_api_url,
                "page_number": page,
                "size": size,
                "count": count,
                "src": src,
            }
        )


class AuthorLikedFQIDView(AuthorLikedListView):
    '''
    GET /api/author/fqid/<path:author_fqid>/liked/
    Returns a paginated list of all likes made by the author.
    '''
    def get(self, request, author_fqid):
        liker = self.get_author(author_fqid)
        return self._build_response(request, liker)


class AuthorLikedDetailView(LikeSerializerMixin, APIView):
    '''
    GET /api/author/<uuid:author_id>/liked/<str:like_id>/
    Retrieves a specific like made by the author.
    '''
    permission_classes = [permissions.AllowAny]

    def get(self, request, author_id, like_id):
        liker = resolve_author_or_404(str(author_id))
        like_object = self._retrieve_like_object(request, like_id, expected_author_id=liker.id)
        return Response(like_object)


class LikeDetailView(LikeSerializerMixin, APIView):
    '''
    GET /api/liked/<str:like_id>/
    Retrieves a specific like by its identifier.
    '''
    permission_classes = [permissions.AllowAny]

    def get(self, request, like_id):
        like_object = self._retrieve_like_object(request, like_id)
        return Response(like_object)


class EntryCommentsListCreateView(generics.ListCreateAPIView):
    """
    GET /api/entries/<entry_id>/comments/
    POST /api/entries/<entry_id>/comments/
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    _entry = None

    def get_entry(self):
        if self._entry is not None:
            return self._entry
        entry = get_object_or_404(Entry, id=self.kwargs["entry_id"])
        if not entry.can_view(self.request.user):
            raise Http404("Entry not found")
        self._entry = entry
        return entry

    def get_queryset(self):
        entry = self.get_entry()
        comments = entry.comments.select_related("author")
        if (
            entry.visibility == Visibility.FRIENDS
            and self.request.user.is_authenticated
            and self.request.user != entry.author
        ):
            comments = comments.filter(author__in=[self.request.user, entry.author])
        return comments.order_by("created_at")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(
            queryset, many=True, context=self.get_serializer_context()
        )
        entry_url = request.build_absolute_uri(reverse("api:entry-detail", args=[self.get_entry().id]))
        return Response({"type": "comments", "entry": entry_url, "comments": serializer.data})

    def perform_create(self, serializer):
        entry = self.get_entry()
        if not self.request.user.is_authenticated:
            raise Http404("Entry not found")
        serializer.save(entry=entry, author=self.request.user)


class CommentDetailView(generics.RetrieveAPIView):
    """
    GET /api/comments/<comment_id>/
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        comment = get_object_or_404(
            Comment.objects.select_related("entry", "author"),
            id=self.kwargs["comment_id"],
        )
        entry = comment.entry
        if not entry.can_view(self.request.user):
            raise Http404("Comment not found")
        if (
            entry.visibility == Visibility.FRIENDS
            and self.request.user != entry.author
            and self.request.user != comment.author
        ):
            raise Http404("Comment not found")
        return comment


class CommentLikeView(APIView):
    """
    POST /api/comments/<comment_id>/like/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, comment_id):
        comment = get_object_or_404(
            Comment.objects.select_related("entry"),
            id=comment_id,
        )
        entry = comment.entry
        if not entry.can_view(request.user):
            raise Http404("Comment not found")
        if (
            entry.visibility == Visibility.FRIENDS
            and request.user not in {entry.author, comment.author}
        ):
            raise Http404("Comment not found")

        comment.liked_by.add(request.user)
        serializer = CommentSerializer(comment, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)