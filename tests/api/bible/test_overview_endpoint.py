"""
Tests for Bible API overview endpoint.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.models import APIKey


class BibleOverviewEndpointTest(TestCase):
    """Tests for /api/v1/bible/overview/ endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser")
        self.api_key = APIKey.objects.create(name="Test Key", user=self.user, scopes=["read"])

    def test_overview_endpoint_requires_authentication(self):
        """Test overview endpoint requires API key authentication."""
        response = self.client.get("/api/v1/bible/overview/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_overview_endpoint_with_valid_api_key(self):
        """Test overview endpoint with valid API key."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        response = self.client.get("/api/v1/bible/overview/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data["api_name"], "Bible API")
        self.assertEqual(data["version"], "1.0.0")
        self.assertIn("description", data)
        self.assertIn("endpoints", data)

        endpoints = data["endpoints"]
        self.assertIn("books", endpoints)
        self.assertIn("verses", endpoints)
        self.assertIn("auth", endpoints)

    def test_overview_endpoint_with_invalid_api_key(self):
        """Test overview endpoint with invalid API key."""
        self.client.credentials(HTTP_AUTHORIZATION="Api-Key invalid-key")
        response = self.client.get("/api/v1/bible/overview/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_overview_endpoint_response_structure(self):
        """Test overview endpoint response has expected structure."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        response = self.client.get("/api/v1/bible/overview/")

        data = response.json()
        expected_keys = ["api_name", "version", "description", "endpoints"]
        for key in expected_keys:
            self.assertIn(key, data)

        endpoint_keys = ["books", "verses", "auth"]
        for key in endpoint_keys:
            self.assertIn(key, data["endpoints"])
