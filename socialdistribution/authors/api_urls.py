from django.urls import path
from .api_views import (
    AuthorDetailView, 
    AuthorFQIDView, 
    AuthorListView, 
    followers_list_api,
    followers_detail_api,
    ExploreAuthorsView,
)
from . import api_views

app_name = "authors_api"

urlpatterns = [
    # Authors list
    path('authors/', AuthorListView.as_view(), name='authors-list'),

    # Explore (local only)
    path('authors/explore/', api_views.ExploreAuthorsView.as_view(), name='explore-authors'),
    
    path(
        'authors/<path:author_fqid>/', 
        AuthorFQIDView.as_view(), 
        name='author-fqid-detail'
    ),
    
    # Single author by UUID
    path('authors/<uuid:pk>/', AuthorDetailView.as_view(), name='author-detail'),
    
    
    # Follow/unfollow
    path('authors/follow/', api_views.api_follow_author, name='api-follow'),
    path('authors/<uuid:author_id>/follow-status/', api_views.check_follow_status, name='follow-status'),
    path('authors/<uuid:author_id>/unfollow/', api_views.api_unfollow_author, name='api-unfollow'),
    
    # Followers
    path(
        "authors/<uuid:author_id>/followers",
        followers_list_api,
        name="followers-list-api",
    ),
    path(
        "authors/<uuid:author_id>/followers/<path:foreign_author_fqid>",
        followers_detail_api,
        name="followers-detail-api",
    ),
    
    # Following
    path(
        "authors/<uuid:author_id>/following",
        api_views.following_list_api,
        name="following-list-api",
    ),
    path(
        "authors/<uuid:author_id>/following/<path:foreign_author_fqid>",
        api_views.following_detail_api,
        name="following-detail-api",
    ),
]