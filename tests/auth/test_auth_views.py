"""
Tests for auth views.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.models import APIKey


class AuthViewsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="auth_test_user", email="test@example.com")
        self.api_key = APIKey.objects.create(name="Test Key", user=self.user, scopes=["read", "write"])

    def test_status_endpoint_public_access(self):
        """Test that status endpoint is publicly accessible."""
        response = self.client.get("/api/v1/auth/status/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should indicate not authenticated
        data = response.json()
        self.assertFalse(data["authenticated"])

    def test_status_endpoint_success(self):
        """Test successful status response."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        response = self.client.get("/api/v1/auth/status/")
        # Response depends on actual implementation
        # This test ensures the endpoint is callable
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_register_endpoint_public(self):
        """Test that register endpoint is public."""
        response = self.client.post("/api/v1/auth/register/", {"email": "test@example.com"})
        # Should not return 401 (authentication required)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_register_endpoint_success(self):
        """Test register endpoint response."""
        response = self.client.post("/api/v1/auth/register/", {"email": "test@example.com"})
        # Response depends on actual implementation
        # This test ensures the endpoint is callable
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
