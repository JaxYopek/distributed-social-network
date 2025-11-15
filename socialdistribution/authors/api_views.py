from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes as drf_permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from django.urls import reverse
import requests
from requests.auth import HTTPBasicAuth
from authors.models import Author, FollowRequest, FollowRequestStatus
from authors.serializers import AuthorSerializer


class AuthorDetailView(generics.RetrieveAPIView):
    """
    GET /api/author/<id>
    Used to retreive the author detials and serialize them
    Accessible to anyone (Accounts are public)
    """
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [permissions.AllowAny]

class AuthorListView(generics.ListAPIView):
    """
    GET /api/authors/
    Returns a list of all authors (public accounts).
    """
    queryset = Author.objects.all().order_by("id") 
    serializer_class = AuthorSerializer 
    permission_classes = [permissions.AllowAny]
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Return in spec format with "authors" key
        return Response({
            "type": "authors",
            "authors": serializer.data
        })
    
class ExploreAuthorsView(APIView):
    """
    GET /api/authors/explore/
    Returns all local authors + authors from connected remote nodes
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from entries.models import RemoteNode
        
        local_authors = Author.objects.filter(is_active=True).order_by("id")
        local_serializer = AuthorSerializer(local_authors, many=True, context={'request': request})
        
        remote_authors = []
        connected_nodes = RemoteNode.objects.filter(is_active=True)
        
        for node in connected_nodes:            
            try:
                # Check if username/password are actually empty
                auth = None
                if node.username and node.password:
                    auth = HTTPBasicAuth(node.username, node.password)
                    print(f"   Using auth: YES")
                else:
                    print(f"   Using auth: NO")
                
                response = requests.get(
                    f"{node.base_url.rstrip('/')}/api/authors/",
                    auth=auth,
                    timeout=5
                )
                
                if response.ok:
                    data = response.json()
                    authors = data.get('authors', [])
                    
                    for author in authors:
                        author['_node_name'] = node.name
                        author['_is_remote'] = True
                    
                    remote_authors.extend(authors)
                else:
                    print(f"   ❌ Response not OK: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Exception: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        return Response({
            'type': 'authors',
            'local': local_serializer.data,
            'remote': remote_authors,
            'all': local_serializer.data + remote_authors
        })
@api_view(['POST'])
@drf_permission_classes([permissions.IsAuthenticated])
def api_follow_author(request):
    """
    POST /api/authors/follow/
    API endpoint for following local or remote authors
    Body: { "author_id": "full URL of author to follow" }
    """
    target_author_url = request.data.get('author_id', '').rstrip('/')
    
    if not target_author_url:
        return Response(
            {'detail': 'author_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if it's a local follow (just the UUID) or remote (full URL)
    current_host = request.build_absolute_uri('/').rstrip('/')
    
    # Handle if they sent just a UUID (from your existing UI)
    if not target_author_url.startswith('http'):
        # Local author by UUID
        try:
            target_author = Author.objects.get(id=target_author_url)
            
            follow_req, created = FollowRequest.objects.get_or_create(
                follower=request.user,
                followee=target_author,
                defaults={'status': FollowRequestStatus.PENDING}
            )
            
            return Response({
                'detail': 'Follow request sent',
                'created': created
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
        except Author.DoesNotExist:
            return Response(
                {'detail': 'Author not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    # It's a full URL - check if local or remote
    if target_author_url.startswith(current_host):
        # LOCAL but with full URL
        try:
            target_author_id = target_author_url.split('/')[-1]
            target_author = Author.objects.get(id=target_author_id)
            
            follow_req, created = FollowRequest.objects.get_or_create(
                follower=request.user,
                followee=target_author,
                defaults={'status': FollowRequestStatus.PENDING}
            )
            
            return Response({
                'detail': 'Follow request sent (local)',
                'created': created
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
        except Author.DoesNotExist:
            return Response(
                {'detail': 'Author not found'},
                status=status.HTTP_404_NOT_FOUND
            )
@api_view(['POST'])
@drf_permission_classes([permissions.IsAuthenticated])
def api_follow_author(request):
    """
    POST /api/authors/follow/
    API endpoint for following local or remote authors
    Body: { "author_id": "full URL of author to follow" }
    """
    target_author_url = request.data.get('author_id', '').rstrip('/')
    
    if not target_author_url:
        return Response(
            {'detail': 'author_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if it's a local follow (just the UUID) or remote (full URL)
    current_host = request.build_absolute_uri('/').rstrip('/')
    
    # Handle if they sent just a UUID (from your existing UI)
    if not target_author_url.startswith('http'):
        # Local author by UUID
        try:
            target_author = Author.objects.get(id=target_author_url)
            
            follow_req, created = FollowRequest.objects.get_or_create(
                follower=request.user,
                followee=target_author,
                defaults={'status': FollowRequestStatus.PENDING}
            )
            
            return Response({
                'detail': 'Follow request sent',
                'created': created
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
        except Author.DoesNotExist:
            return Response(
                {'detail': 'Author not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    # It's a full URL - check if local or remote
    if target_author_url.startswith(current_host):
        # LOCAL but with full URL
        try:
            target_author_id = target_author_url.split('/')[-1]
            target_author = Author.objects.get(id=target_author_id)
            
            follow_req, created = FollowRequest.objects.get_or_create(
                follower=request.user,
                followee=target_author,
                defaults={'status': FollowRequestStatus.PENDING}
            )
            
            return Response({
                'detail': 'Follow request sent (local)',
                'created': created
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
        except Author.DoesNotExist:
            return Response(
                {'detail': 'Author not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    else:
        # REMOTE AUTHOR - send to their inbox
        from entries.models import RemoteNode
        
        # Build current user's author URL manually (avoid reverse() issues)
        current_user_url = request.build_absolute_uri(f'/api/authors/{request.user.id}/')
        
        actor_data = {
            'type': 'author',
            'id': current_user_url,
            'displayName': getattr(request.user, 'display_name', None) or request.user.username,
            'host': request.build_absolute_uri('/api/'),
            'github': getattr(request.user, 'github', ''),
            'profileImage': getattr(request.user, 'profile_image', ''),
        }
        
        follow_request_data = {
            'type': 'follow',
            'summary': f"{actor_data['displayName']} wants to follow you",
            'actor': actor_data,
            'object': {
                'type': 'author',
                'id': target_author_url,
            }
        }
        
        # Find the remote node
        inbox_url = f"{target_author_url}/inbox/"
        
        remote_node = None
        for node in RemoteNode.objects.filter(is_active=True):
            if target_author_url.startswith(node.base_url.rstrip('/')):
                remote_node = node
                break
        
        if not remote_node:
            return Response(
                {'detail': 'Remote node not configured'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Send to remote inbox
            response = requests.post(
                inbox_url,
                json=follow_request_data,
                auth=HTTPBasicAuth(remote_node.username, remote_node.password) if remote_node.username else None,
                timeout=10
            )
            
            if response.ok:
                # Store locally
                remote_author, _ = Author.objects.get_or_create(
                    id=target_author_url,
                    defaults={
                        'username': f"remote_{target_author_url.split('/')[-1][:20]}",
                        'display_name': 'Remote Author',
                        'is_active': False,
                    }
                )
                
                follow_req, created = FollowRequest.objects.get_or_create(
                    follower=request.user,
                    followee=remote_author,
                    defaults={'status': FollowRequestStatus.PENDING}
                )
                
                return Response({
                    'detail': 'Follow request sent to remote node',
                    'created': created
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'detail': 'Failed to send to remote node',
                    'remote_status': response.status_code,
                    'remote_response': response.text[:200]
                }, status=status.HTTP_502_BAD_GATEWAY)
        
        except requests.exceptions.RequestException as e:
            return Response({
                'detail': f'Connection error: {str(e)}'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)