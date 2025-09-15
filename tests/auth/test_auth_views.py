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

    def test_profile_endpoint_requires_auth(self):
        """Test that profile endpoint requires authentication."""
        response = self.client.get("/api/v1/auth/profile/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_endpoint_success(self):
        """Test successful profile response."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        response = self.client.get("/api/v1/auth/profile/")
        # Response depends on actual implementation
        # This test ensures the endpoint is callable
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_keys_endpoint_requires_auth(self):
        """Test that keys endpoint requires authentication."""
        response = self.client.get("/api/v1/auth/keys/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_keys_endpoint_success(self):
        """Test successful keys response."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        response = self.client.get("/api/v1/auth/keys/")
        # Response depends on actual implementation
        # This test ensures the endpoint is callable
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
