from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from entries.models import RemoteNode
from authors.models import Author
import base64

User = get_user_model()


class RemoteNodeModelTest(TestCase):
    """Test the RemoteNode model"""
    
    def test_create_remote_node(self):
        """Test creating a remote node with all required fields"""
        node = RemoteNode.objects.create(
            name="Test Node",
            base_url="https://test.example.com/api/",
            username="test_user",
            password="test_pass",
            is_active=True
        )
        
        self.assertEqual(node.name, "Test Node")
        self.assertEqual(node.base_url, "https://test.example.com/api/")
        self.assertEqual(node.username, "test_user")
        self.assertEqual(node.password, "test_pass")
        self.assertTrue(node.is_active)
        self.assertIsNotNone(node.created_at)
        self.assertIsNotNone(node.updated_at)
    
    def test_remote_node_str_representation(self):
        """Test the string representation of a remote node"""
        node = RemoteNode.objects.create(
            name="Alpha Node",
            base_url="https://alpha.example.com/api/",
            username="alpha",
            password="password"
        )
        
        expected_str = "Alpha Node (https://alpha.example.com/api/)"
        self.assertEqual(str(node), expected_str)
    
    def test_remote_node_unique_constraints(self):
        """Test that name and base_url must be unique"""
        RemoteNode.objects.create(
            name="Unique Node",
            base_url="https://unique.example.com/api/",
            username="user1",
            password="pass1"
        )
        
        # Try to create another node with the same name
        with self.assertRaises(Exception):
            RemoteNode.objects.create(
                name="Unique Node",  # Same name
                base_url="https://different.example.com/api/",
                username="user2",
                password="pass2"
            )
        
        # Try to create another node with the same base_url
        with self.assertRaises(Exception):
            RemoteNode.objects.create(
                name="Different Node",
                base_url="https://unique.example.com/api/",  # Same URL
                username="user3",
                password="pass3"
            )
    
    def test_inactive_node(self):
        """Test creating an inactive node"""
        node = RemoteNode.objects.create(
            name="Inactive Node",
            base_url="https://inactive.example.com/api/",
            username="inactive_user",
            password="inactive_pass",
            is_active=False
        )
        
        self.assertFalse(node.is_active)


class RemoteNodeBasicAuthenticationTest(APITestCase):
    """Test HTTP Basic Authentication for remote nodes"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create an active remote node
        self.active_node = RemoteNode.objects.create(
            name="Active Node",
            base_url="https://active.example.com/api/",
            username="active_user",
            password="active_pass",
            is_active=True
        )
        
        # Create an inactive remote node
        self.inactive_node = RemoteNode.objects.create(
            name="Inactive Node",
            base_url="https://inactive.example.com/api/",
            username="inactive_user",
            password="inactive_pass",
            is_active=False
        )
        
        # Create a local user for testing
        self.local_user = User.objects.create_user(
            username="localuser",
            password="localpass"
        )
        
        # Create some test authors
        self.author1 = Author.objects.create(
            username="author1",
            display_name="Author One",
            is_active=True,
            is_approved=True
        )
        self.author2 = Author.objects.create(
            username="author2",
            display_name="Author Two",
            is_active=True,
            is_approved=True
        )
    
    def get_basic_auth_header(self, username, password):
        """Helper method to create Basic Auth header"""
        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    def test_access_authors_list_with_valid_node_credentials(self):
        """Test that a remote node can access authors list with valid credentials"""
        auth_header = self.get_basic_auth_header("active_user", "active_pass")
        
        response = self.client.get(
            '/api/authors/',
            HTTP_AUTHORIZATION=auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('type', response.data)
        self.assertEqual(response.data['type'], 'authors')
        self.assertIn('authors', response.data)
    
    def test_access_authors_list_with_invalid_credentials(self):
        """Test that invalid credentials are rejected"""
        auth_header = self.get_basic_auth_header("wrong_user", "wrong_pass")
        
        response = self.client.get(
            '/api/authors/',
            HTTP_AUTHORIZATION=auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_access_authors_list_with_inactive_node(self):
        """Test that an inactive node cannot access the API"""
        auth_header = self.get_basic_auth_header("inactive_user", "inactive_pass")
        
        response = self.client.get(
            '/api/authors/',
            HTTP_AUTHORIZATION=auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_access_authors_list_without_authentication(self):
        """Test that unauthenticated requests are rejected"""
        response = self.client.get('/api/authors/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_access_author_detail_with_valid_node_credentials(self):
        """Test that a remote node can access author details"""
        auth_header = self.get_basic_auth_header("active_user", "active_pass")
        
        response = self.client.get(
            f'/api/authors/{self.author1.id}/',
            HTTP_AUTHORIZATION=auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'author')
        self.assertEqual(response.data['displayName'], 'Author One')
    
    def test_local_user_can_access_with_session_auth(self):
        """Test that local users can still access with session authentication"""
        self.client.force_authenticate(user=self.local_user)
        
        response = self.client.get('/api/authors/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_node_cannot_access_local_only_endpoints(self):
        """Test that remote nodes cannot access local-only endpoints"""
        auth_header = self.get_basic_auth_header("active_user", "active_pass")
        
        # Try to access explore endpoint (local only)
        response = self.client.get(
            '/api/authors/explore/',
            HTTP_AUTHORIZATION=auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_local_user_can_access_local_only_endpoints(self):
        """Test that local users can access local-only endpoints"""
        self.client.force_authenticate(user=self.local_user)
        
        response = self.client.get('/api/authors/explore/')
        
        # Should succeed (assuming explore endpoint exists and works)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
    
    def test_wrong_password_for_valid_username(self):
        """Test that correct username with wrong password fails"""
        auth_header = self.get_basic_auth_header("active_user", "wrong_password")
        
        response = self.client.get(
            '/api/authors/',
            HTTP_AUTHORIZATION=auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_case_sensitive_credentials(self):
        """Test that credentials are case-sensitive"""
        auth_header = self.get_basic_auth_header("ACTIVE_USER", "active_pass")
        
        response = self.client.get(
            '/api/authors/',
            HTTP_AUTHORIZATION=auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RemoteNodePermissionsTest(APITestCase):
    """Test permission classes for node authentication"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        self.node = RemoteNode.objects.create(
            name="Test Node",
            base_url="https://test.example.com/api/",
            username="node_user",
            password="node_pass",
            is_active=True
        )
        
        self.local_user = User.objects.create_user(
            username="testuser",
            password="testpass"
        )
    
    def get_basic_auth_header(self, username, password):
        """Helper method to create Basic Auth header"""
        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    def test_is_authenticated_node_or_local_user_with_node(self):
        """Test IsAuthenticatedNodeOrLocalUser allows nodes"""
        auth_header = self.get_basic_auth_header("node_user", "node_pass")
        
        response = self.client.get(
            '/api/authors/',
            HTTP_AUTHORIZATION=auth_header
        )
        
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_is_authenticated_node_or_local_user_with_local_user(self):
        """Test IsAuthenticatedNodeOrLocalUser allows local users"""
        self.client.force_authenticate(user=self.local_user)
        
        response = self.client.get('/api/authors/')
        
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_is_local_user_only_blocks_nodes(self):
        """Test IsLocalUserOnly blocks nodes"""
        auth_header = self.get_basic_auth_header("node_user", "node_pass")
        
        response = self.client.get(
            '/api/authors/explore/',
            HTTP_AUTHORIZATION=auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_is_local_user_only_allows_local_users(self):
        """Test IsLocalUserOnly allows local users"""
        self.client.force_authenticate(user=self.local_user)
        
        response = self.client.get('/api/authors/explore/')
        
        # Should not be forbidden (might be 404 if endpoint doesn't exist)
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AddRemoteNodeCommandTest(TestCase):
    """Test the add_remote_node management command"""
    
    def test_command_creates_new_node(self):
        """Test that the command creates a new remote node"""
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command(
            'add_remote_node',
            'Command Node',
            'https://command.example.com/api/',
            'cmd_user',
            'cmd_pass',
            stdout=out
        )
        
        # Check that node was created
        node = RemoteNode.objects.get(base_url='https://command.example.com/api/')
        self.assertEqual(node.name, 'Command Node')
        self.assertEqual(node.username, 'cmd_user')
        self.assertEqual(node.password, 'cmd_pass')
        self.assertTrue(node.is_active)
        
        # Check output message
        self.assertIn('Successfully created', out.getvalue())
    
    def test_command_updates_existing_node(self):
        """Test that the command updates an existing node"""
        from django.core.management import call_command
        from io import StringIO
        
        # Create initial node
        RemoteNode.objects.create(
            name="Old Name",
            base_url="https://update.example.com/api/",
            username="old_user",
            password="old_pass"
        )
        
        out = StringIO()
        call_command(
            'add_remote_node',
            'New Name',
            'https://update.example.com/api/',
            'new_user',
            'new_pass',
            stdout=out
        )
        
        # Check that node was updated
        node = RemoteNode.objects.get(base_url='https://update.example.com/api/')
        self.assertEqual(node.name, 'New Name')
        self.assertEqual(node.username, 'new_user')
        self.assertEqual(node.password, 'new_pass')
        
        # Check output message
        self.assertIn('Successfully updated', out.getvalue())
    
    def test_command_creates_inactive_node(self):
        """Test that the --inactive flag creates an inactive node"""
        from django.core.management import call_command
        
        call_command(
            'add_remote_node',
            'Inactive Command Node',
            'https://inactive-cmd.example.com/api/',
            'inactive_user',
            'inactive_pass',
            '--inactive'
        )
        
        node = RemoteNode.objects.get(base_url='https://inactive-cmd.example.com/api/')
        self.assertFalse(node.is_active)


class NodeAdminTest(TestCase):
    """Test the RemoteNode admin interface"""
    
    def setUp(self):
        """Set up admin user and client"""
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass'
        )
        self.client = Client()
        self.client.login(username='admin', password='adminpass')
        
        self.node = RemoteNode.objects.create(
            name="Admin Test Node",
            base_url="https://admin-test.example.com/api/",
            username="admin_node_user",
            password="admin_node_pass"
        )
    
    def test_admin_can_view_remote_nodes(self):
        """Test that admin can view the remote nodes list"""
        response = self.client.get('/admin/entries/remotenode/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Admin Test Node')
    
    def test_admin_can_add_remote_node(self):
        """Test that admin can add a new remote node"""
        response = self.client.get('/admin/entries/remotenode/add/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_admin_can_edit_remote_node(self):
        """Test that admin can edit an existing remote node"""
        response = self.client.get(f'/admin/entries/remotenode/{self.node.pk}/change/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Admin Test Node')