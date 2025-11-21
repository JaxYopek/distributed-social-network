from rest_framework import serializers
from django.urls import reverse
from .models import Entry
from authors.serializers import AuthorSerializer
from rest_framework import serializers
from django.urls import reverse
from .models import Entry, Comment
from authors.serializers import AuthorSerializer

class EntrySerializer(serializers.ModelSerializer):
    """
    Serializer for the Entry model, used in the API to convert Entry instances
    to JSON and vice versa. Includes nested author information.
    """
    type = serializers.CharField(default="entry", read_only=True)
    id = serializers.SerializerMethodField()
    web = serializers.SerializerMethodField()
    author = AuthorSerializer(read_only=True)
    contentType = serializers.ChoiceField(
        source='content_type',  # Maps to model's content_type field
        choices=Entry.CONTENT_TYPE_CHOICES,
        required=False
    )
    comments = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()

    class Meta:
        """
        Used to determine which model and fields of the model to serialize
        """
        model = Entry
        fields = [
            "type",
            "id",
            "web",
            "title",
            "description",
            "contentType",
            "content",
            "visibility",
            "published",
            "author",
            "comments",
            "likes",
        ]

    def get_id(self, obj):
        """
        Generate full URL for the API endpoint of the entry
        """
        request = self.context.get("request")
        return request.build_absolute_uri(
            reverse("api:entry-detail", args=[obj.id])
        )

    def get_web(self, obj):
        """
        Generates the URL for the HTML page of the entry
        """
        request = self.context.get("request")
        return request.build_absolute_uri(
            reverse("entries:view_entry", args=[obj.id])
        )

    

    def get_likes(self, obj):
        request = self.context.get("request")
        likes_qs = obj.liked_by.all()
        page = int(request.query_params.get("like_page", 1)) if request else 1
        size = int(request.query_params.get("like_size", 50)) if request else 50
        start = (page - 1) * size
        end = start + size
        entry_api_url = self.get_id(obj)
        entry_html_url = self.get_web(obj)
        likes_url = (
            request.build_absolute_uri(reverse("api:entry-likes", args=[obj.id]))
            if request
            else ""
        )
        likes_page = likes_qs[start:end]
        src = []
        for author in likes_page:
            like_id = f"{likes_url}{author.id}/" if likes_url else ""
            src.append(
                {
                    "type": "like",
                    "author": AuthorSerializer(
                        author, context={"request": request}
                    ).data,
                    "published": obj.updated,
                    "id": like_id,
                    "object": entry_html_url,
                }
            )
        return {
            "type": "likes",
            "web": entry_html_url,
            "id": likes_url,
            "page_number": page,
            "size": size,
            "count": likes_qs.count(),
            "src": src,
        }
    
    def get_comments(self, obj):
        request = self.context.get("request")

        # All visible comments for this entry
        comments_qs = obj.comments.select_related("author").order_by("created_at")
        comments_data = CommentSerializer(
            comments_qs, many=True, context=self.context
        ).data

        # HTML + API URLs
        entry_html_url = self.get_web(obj)
        comments_api_url = (
            request.build_absolute_uri(
                reverse("api:entry-comments", args=[obj.id])
            )
            if request
            else ""
        )

        count = len(comments_data)

        return {
            "type": "comments",
            "web": entry_html_url,
            "id": comments_api_url,
            "page_number": 1,
            "size": count,
            "count": count,
            "src": comments_data,
        }


class CommentSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default="comment", read_only=True)
    id = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    comment = serializers.CharField(source="content")
    contentType = serializers.CharField(source="content_type", default="text/plain")
    published = serializers.DateTimeField(source="created_at", read_only=True)
    entry = serializers.SerializerMethodField()
    web = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["type", "id", "author", "comment", "contentType", "published", "entry", "web"]

    def get_id(self, obj):
        """Returns the full API URL for this comment via commented endpoint"""
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(
                f"/api/authors/{obj.author.id}/commented/{obj.id}"
            )
        return f"http://localhost:8000/api/authors/{obj.author.id}/commented/{obj.id}"

    def get_author(self, obj):
        """Returns full author object per spec"""
        from authors.serializers import AuthorSerializer
        request = self.context.get("request")
        return AuthorSerializer(obj.author, context={"request": request}).data

    def get_entry(self, obj):
        """Returns the full entry URL"""
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(
                f"/api/authors/{obj.entry.author.id}/entries/{obj.entry.id}/"
            )
        return f"http://localhost:8000/api/authors/{obj.entry.author.id}/entries/{obj.entry.id}/"

    def get_web(self, obj):
        """Returns HTML URL to view the entry (where comment appears)"""
        request = self.context.get("request")
        if request:
            # Could also be a dedicated comment view URL if you have one
            return request.build_absolute_uri(f"/entries/{obj.entry.id}/")
        return f"http://localhost:8000/entries/{obj.entry.id}/"
