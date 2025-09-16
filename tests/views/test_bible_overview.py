"""
Tests for Bible overview view.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.models import APIKey, CanonicalBook, Language, Testament, Version


class BibleOverviewViewTest(TestCase):
    """Tests for BibleOverview view."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(username="overview_user")
        self.api_key = APIKey.objects.create(name="Overview Key", user=self.user, scopes=["read"])

        # Create test data for overview
        self.language = Language.objects.create(code="en-test", name="English Test")
        self.testament = Testament.objects.create(id=94, name="Test Testament")

        # Create a few books
        for i in range(3):
            CanonicalBook.objects.create(
                osis_code=f"TestBook{i}", canonical_order=980 + i, testament=self.testament, chapter_count=10 + i
            )

        # Create a version
        Version.objects.create(name="Test Version", code="TEST_VER", language=self.language)

    def test_overview_requires_auth(self):
        """Test that overview endpoint requires authentication."""
        response = self.client.get("/api/v1/bible/overview/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_overview_success(self):
        """Test successful overview response."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        response = self.client.get("/api/v1/bible/overview/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Verify response structure
        self.assertIn("api_name", data)
        self.assertEqual(data["api_name"], "Bible API")
        self.assertIn("version", data)
        self.assertEqual(data["version"], "1.0.0")
        self.assertIn("description", data)
        self.assertIn("endpoints", data)

        # Verify endpoints structure
        endpoints = data["endpoints"]
        self.assertIn("books", endpoints)
        self.assertIn("verses", endpoints)
        self.assertIn("auth", endpoints)
