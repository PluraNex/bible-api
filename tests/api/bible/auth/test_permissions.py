"""
Tests for authentication and permissions.
"""
from unittest.mock import Mock

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APITestCase

from bible.apps.auth.permissions import HasAPIScopes
from bible.models import APIKey


class HasAPIScopesTest(TestCase):
    """Test HasAPIScopes permission class."""

    def setUp(self):
        self.permission = HasAPIScopes()
        self.user = User.objects.create_user(username="testuser")
        self.api_key = APIKey.objects.create(name="Test Key", user=self.user, scopes=["read", "write"])

    def test_no_required_scopes_allows_access(self):
        """Test that views with no required_scopes allow access."""
        request = Mock()
        request.user = self.user
        request.auth = self.api_key

        view = Mock()
        view.required_scopes = []

        self.assertTrue(self.permission.has_permission(request, view))

    def test_unauthenticated_user_denied_with_scopes(self):
        """Test that unauthenticated users are denied when scopes required."""
        request = Mock()
        request.user = None

        view = Mock()
        view.required_scopes = ["read"]

        self.assertFalse(self.permission.has_permission(request, view))

    def test_authenticated_user_without_api_key_denied(self):
        """Test that user without API key is denied."""
        request = Mock()
        request.user = self.user
        request.user.is_authenticated = True
        request.auth = None

        view = Mock()
        view.required_scopes = ["read"]

        self.assertFalse(self.permission.has_permission(request, view))

    def test_api_key_with_required_scope_allowed(self):
        """Test that API key with required scope is allowed."""
        request = Mock()
        request.user = self.user
        request.user.is_authenticated = True
        request.auth = self.api_key

        view = Mock()
        view.required_scopes = ["read"]

        self.assertTrue(self.permission.has_permission(request, view))

    def test_api_key_missing_required_scope_denied(self):
        """Test that API key missing required scope is denied."""
        request = Mock()
        request.user = self.user
        request.user.is_authenticated = True
        request.auth = self.api_key

        view = Mock()
        view.required_scopes = ["admin"]  # api_key only has 'read', 'write'

        self.assertFalse(self.permission.has_permission(request, view))

    def test_api_key_with_multiple_required_scopes_allowed(self):
        """Test that API key with all required scopes is allowed."""
        request = Mock()
        request.user = self.user
        request.user.is_authenticated = True
        request.auth = self.api_key

        view = Mock()
        view.required_scopes = ["read", "write"]

        self.assertTrue(self.permission.has_permission(request, view))

    def test_api_key_missing_one_of_multiple_scopes_denied(self):
        """Test that API key missing one of multiple required scopes is denied."""
        request = Mock()
        request.user = self.user
        request.user.is_authenticated = True
        request.auth = self.api_key

        view = Mock()
        view.required_scopes = ["read", "write", "admin"]

        self.assertFalse(self.permission.has_permission(request, view))

    def test_object_permission_delegates_to_has_permission(self):
        """Test that object permission uses same logic as has_permission."""
        request = Mock()
        request.user = self.user
        request.user.is_authenticated = True
        request.auth = self.api_key

        view = Mock()
        view.required_scopes = ["read"]

        obj = Mock()

        # Should return same result as has_permission
        has_perm = self.permission.has_permission(request, view)
        has_obj_perm = self.permission.has_object_permission(request, view, obj)

        self.assertEqual(has_perm, has_obj_perm)


class VersionsEndpointsPermissionIntegrationTest(APITestCase):
    """Integration tests for versions endpoints with HasAPIScopes."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser")

    def test_versions_list_without_api_key_denied(self):
        """Test that versions list requires API key."""
        response = self.client.get("/api/v1/bible/versions/")
        self.assertEqual(response.status_code, 401)
        # Verify WWW-Authenticate header is present
        self.assertIn("WWW-Authenticate", response.headers)
        self.assertEqual(response.headers["WWW-Authenticate"], "Api-Key")

    def test_versions_list_with_read_scope_allowed(self):
        """Test that versions list works with read scope."""
        api_key = APIKey.objects.create(name="Test Key", user=self.user, scopes=["read"])

        response = self.client.get("/api/v1/bible/versions/", HTTP_AUTHORIZATION=f"Api-Key {api_key.key}")
        self.assertEqual(response.status_code, 200)

    def test_versions_list_without_read_scope_denied(self):
        """Test that versions list denied without read scope."""
        api_key = APIKey.objects.create(name="Test Key", user=self.user, scopes=["write"])  # Missing 'read' scope

        response = self.client.get("/api/v1/bible/versions/", HTTP_AUTHORIZATION=f"Api-Key {api_key.key}")
        self.assertEqual(response.status_code, 403)

    def test_version_detail_without_read_scope_denied(self):
        """Test that version detail denied without read scope."""
        api_key = APIKey.objects.create(name="Test Key", user=self.user, scopes=["write"])  # Missing 'read' scope

        response = self.client.get("/api/v1/bible/versions/KJV/", HTTP_AUTHORIZATION=f"Api-Key {api_key.key}")
        self.assertEqual(response.status_code, 403)

    def test_version_detail_with_read_scope_allowed(self):
        """Test that version detail works with read scope."""
        # Note: This test will fail until we have actual Version objects
        # but it tests the permission logic
        api_key = APIKey.objects.create(name="Test Key", user=self.user, scopes=["read"])

        response = self.client.get("/api/v1/bible/versions/KJV/", HTTP_AUTHORIZATION=f"Api-Key {api_key.key}")
        # Expecting 404 (not found) rather than 403 (forbidden)
        # which means permission passed but object doesn't exist
        self.assertIn(response.status_code, [200, 404])
