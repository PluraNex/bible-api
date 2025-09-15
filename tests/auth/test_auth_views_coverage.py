"""
Coverage improvement tests for auth views.
Tests AuthenticationStatusView and DeveloperRegistrationAPIView.
"""
import pytest
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.models import APIKey


@pytest.mark.auth
class AuthViewsCoverageTest(TestCase):
    """Test auth views for coverage improvement."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser")
        self.api_key = APIKey.objects.create(name="Test Key", user=self.user, scopes=["read"])

    def test_authentication_status_authenticated(self):
        """Test authentication status endpoint with authenticated user."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        response = self.client.get("/api/v1/auth/status/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data["authenticated"])
        self.assertIsNotNone(data["user"])
        self.assertEqual(data["api_key_status"], "active")

    def test_authentication_status_unauthenticated(self):
        """Test authentication status endpoint without authentication."""
        response = self.client.get("/api/v1/auth/status/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertFalse(data["authenticated"])
        self.assertIsNone(data["user"])
        self.assertEqual(data["api_key_status"], "required")

    def test_developer_registration_valid_data(self):
        """Test developer registration with valid data."""
        registration_data = {
            "first_name": "John",
            "last_name": "Developer",
            "email": "john@example.com",
            "organization": "Test Org",
        }

        response = self.client.post("/api/v1/auth/register/", registration_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn("api_key", data)
        self.assertIn("examples", data)
        self.assertEqual(data["name"], "John")
        self.assertEqual(data["email"], "john@example.com")

    def test_developer_registration_invalid_data(self):
        """Test developer registration with invalid data to cover error path."""
        invalid_data = {"first_name": "", "email": "invalid-email"}  # Invalid - required field  # Invalid email format

        response = self.client.post("/api/v1/auth/register/", invalid_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.json())
