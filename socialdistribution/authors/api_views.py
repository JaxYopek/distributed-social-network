from rest_framework import generics, permissions
from authors.models import Author
from authors.serializers import AuthorSerializer

class AuthorDetailView(generics.RetrieveAPIView):
    """
    Used to retreive the author detials and serialize them
    Accessible to anyone (Accounts are public)
    """
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [permissions.AllowAny]