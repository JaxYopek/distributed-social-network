from django.urls import path
from .api_views import AuthorDetailView

app_name = "authors_api"

urlpatterns = [
    path('author/<uuid:pk>/', AuthorDetailView.as_view(), name='author-detail'),
]
