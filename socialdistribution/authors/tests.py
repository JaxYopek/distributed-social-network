from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from authors.models import Author
from entries.models import Entry, Visibility


class AuthorProfileViewTests(TestCase):
    def setUp(self):
        self.author = Author.objects.create_user(
            username="janedoe",
            password="testpass123",
            display_name="Jane Doe",
            github="https://github.com/janedoe",
            profile_image="https://example.com/avatar.png",
        )
        self.public_entry = Entry.objects.create(
            title="Public Post",
            description="Visible to everyone",
            content="Public content",
            author=self.author,
            visibility=Visibility.PUBLIC,
        )
        self.private_entry = Entry.objects.create(
            title="Friends Post",
            description="For friends only",
            content="Private content",
            author=self.author,
            visibility=Visibility.FRIENDS,
        )

    def test_profile_page_renders_public_information(self):
        url = reverse("authors:profile_detail", args=[self.author.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "authors/profile_detail.html")
        self.assertContains(response, self.author.display_name)
        self.assertContains(response, self.public_entry.title)
        self.assertNotContains(response, self.private_entry.title)

    def test_get_absolute_url_points_to_profile(self):
        self.assertEqual(
            self.author.get_absolute_url(),
            reverse("authors:profile_detail", args=[self.author.id]),
        )

class AuthorAPITests(TestCase):
    '''
    All tests for the author APIs
    '''
    def setUp(self):
        self.client = APIClient()
        self.user1 = Author.objects.create_user(
            username='john',
            password='pass123',
            display_name='John Doe',
            github='https://github.com/john',
            is_approved=True
        )
        self.user2 = Author.objects.create_user(
            username='jane',
            password='passwd1234',
            display_name='Jane Smith',
            github='https://github.com/jane',
            is_approved=True
        )
    def test_get_author_profile(self):
        """
        Test: As an author, I want a public page with my profile information
        API: GET /api/authors/{AUTHOR_ID}/
        """
        # Make request
        response = self.client.get(f'/api/authors/{self.user1.id}/')
        
        # Assert status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Assert response structure
        self.assertEqual(response.data['type'], 'author')
        self.assertEqual(response.data['displayName'], 'John Doe')
        self.assertEqual(response.data['github'], 'https://github.com/john')
        self.assertIn('id', response.data)
        self.assertIn('host', response.data)

    def test_get_all_profiles(self):
        """
        Test: Getting all profiles from the node
        API: GET /api/authors/
        """
        # Make request
        response = self.client.get(f'/api/authors/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
        # Check pagination structure
        self.assertIn('results', response.data)
               
        # Should have 2 authors
        authors_list = response.data['results']
        self.assertEqual(len(authors_list), 2)
        
        # Check that all authors have required fields
        for author in authors_list:
            self.assertEqual(author['type'], 'author')
            self.assertIn('id', author)
            self.assertIn('displayName', author)
            self.assertIn('host', author)
            self.assertIn('github', author)
            self.assertIn('profileImage', author)
        
        # Check that both users display names exist in the results
        display_names = [a['displayName'] for a in authors_list]
        self.assertIn('John Doe', display_names) 
        self.assertIn('Jane Smith', display_names)


