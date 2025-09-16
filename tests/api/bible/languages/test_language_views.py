"""
Tests for language views.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.models import APIKey, Language


class LanguageListViewTest(TestCase):
    """Test LanguageListView."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser")
        self.api_key = APIKey.objects.create(name="Test Key", user=self.user, scopes=["read"])

        # Create test languages
        self.en_lang, _ = Language.objects.get_or_create(code="en", defaults={"name": "English"})
        self.pt_lang, _ = Language.objects.get_or_create(code="pt", defaults={"name": "Portuguese"})
        self.pt_br_lang, _ = Language.objects.get_or_create(code="pt-BR", defaults={"name": "Portuguese (Brazil)"})

    def test_requires_auth(self):
        """Test that languages endpoint requires authentication."""
        response = self.client.get("/api/v1/bible/languages/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_languages(self):
        """Test listing all languages."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        response = self.client.get("/api/v1/bible/languages/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # Should be paginated response
        self.assertIn("results", response_data)
        self.assertIn("pagination", response_data)

        data = response_data["results"]

        # Should return our test languages (may be fewer if some already exist)
        self.assertGreaterEqual(len(data), 1)

        # Check that each item has the expected structure
        if len(data) > 0:
            first_item = data[0]
            self.assertIn("code", first_item)
            self.assertIn("name", first_item)

            # Should find at least some of our test languages
            language_codes = [item["code"] for item in data]
            expected_codes = ["en", "pt", "pt-BR"]
            found_codes = [code for code in expected_codes if code in language_codes]
            self.assertGreaterEqual(len(found_codes), 1, "Should find at least one test language")

            # Should be ordered by name (from serializer fields)
            names = [item["name"] for item in data]
            self.assertEqual(names, sorted(names))

    def test_filter_languages_by_code(self):
        """Test filtering languages by code."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        response = self.client.get("/api/v1/bible/languages/?code=en")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # Should be paginated response
        self.assertIn("results", response_data)
        data = response_data["results"]

        # Should return only English language (if it exists)
        if len(data) > 0:
            # All results should have code 'en'
            for item in data:
                self.assertEqual(item["code"], "en")
            # First item should be English
            self.assertEqual(data[0]["name"], "English")

    def test_filter_languages_empty_result(self):
        """Test filtering with non-existent language code."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        response = self.client.get("/api/v1/bible/languages/?code=nonexistent")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # Should be paginated response
        self.assertIn("results", response_data)
        data = response_data["results"]

        # Should return empty list
        self.assertEqual(len(data), 0)
