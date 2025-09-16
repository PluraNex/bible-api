"""
API tests for themes endpoints.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.models import (
    APIKey,
    CanonicalBook,
    Language,
    Testament,
    Theme,
    Verse,
    VerseTheme,
    Version,
)


class ThemesApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="themes_user")
        self.api_key = APIKey.objects.create(name="Themes Key", user=self.user, scopes=["read"])

        # Create test data
        self.language_en = Language.objects.create(name="English", code="en")
        self.testament_old = Testament.objects.create(name="OLD", description="Old Testament")
        self.testament_new = Testament.objects.create(name="NEW", description="New Testament")

        self.book_gen = CanonicalBook.objects.create(
            osis_code="Gen", canonical_order=1, testament=self.testament_old, chapter_count=50
        )
        self.book_matt = CanonicalBook.objects.create(
            osis_code="Matt", canonical_order=40, testament=self.testament_new, chapter_count=28
        )

        self.version = Version.objects.create(language=self.language_en, code="EN_TEST", name="Test Version")

        self.verse1 = Verse.objects.create(
            book=self.book_gen,
            version=self.version,
            chapter=1,
            number=1,
            text="In the beginning God created the heavens and the earth.",
        )
        self.verse2 = Verse.objects.create(
            book=self.book_matt,
            version=self.version,
            chapter=1,
            number=1,
            text="The genealogy of Jesus Christ, the son of David, the son of Abraham.",
        )

        self.t1 = Theme.objects.create(name="Faith", description="Trust and belief in God")
        self.t2 = Theme.objects.create(name="Love", description="Divine and human love")
        self.t3 = Theme.objects.create(name="Creation", description="God's creation of the world")

        # Create theme-verse associations
        VerseTheme.objects.create(theme=self.t1, verse=self.verse1)
        VerseTheme.objects.create(theme=self.t2, verse=self.verse2)
        VerseTheme.objects.create(theme=self.t3, verse=self.verse1)

    def test_requires_auth(self):
        self.assertEqual(self.client.get("/api/v1/bible/themes/").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_and_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        lst = self.client.get("/api/v1/bible/themes/")
        self.assertEqual(lst.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(lst.json().get("results", [])), 2)

        detail = self.client.get(f"/api/v1/bible/themes/{self.t1.id}/detail/")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.json().get("name"), "Faith")

    def test_theme_search(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

        # Test successful search
        response = self.client.get("/api/v1/bible/themes/search/?q=faith")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()
        self.assertGreater(len(results), 0)

        # Test search with limit
        response = self.client.get("/api/v1/bible/themes/search/?q=creation&limit=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        # Test missing query parameter
        response = self.client.get("/api/v1/bible/themes/search/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_theme_statistics(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

        # Test successful statistics
        response = self.client.get(f"/api/v1/bible/themes/{self.t1.id}/statistics/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data["theme_id"], self.t1.id)
        self.assertEqual(data["theme_name"], "Faith")
        self.assertGreaterEqual(data["verse_count"], 1)
        self.assertGreaterEqual(data["book_count"], 1)
        self.assertIn("top_books", data)
        self.assertIn("testament_distribution", data)

        # Test not found
        response = self.client.get("/api/v1/bible/themes/99999/statistics/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_theme_analysis_by_book(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

        # Test analysis by OSIS code
        response = self.client.get("/api/v1/bible/themes/analysis/by-book/Gen/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data["book_osis_code"], "Gen")
        self.assertEqual(data["canonical_order"], 1)
        self.assertIn("theme_distribution", data)
        self.assertIn("chapter_analysis", data)
        self.assertGreaterEqual(data["total_themed_verses"], 1)

        # Test not found
        response = self.client.get("/api/v1/bible/themes/analysis/by-book/NonExistent/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_theme_progression(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

        # Test successful progression
        response = self.client.get(f"/api/v1/bible/themes/{self.t1.id}/progression/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data["theme_id"], self.t1.id)
        self.assertEqual(data["theme_name"], "Faith")
        self.assertIn("progression_data", data)
        self.assertIn("testament_summary", data)
        self.assertIn("peak_books", data)

        # Test theme with no verses
        theme_empty = Theme.objects.create(name="Empty Theme")
        response = self.client.get(f"/api/v1/bible/themes/{theme_empty.id}/progression/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_concept_map(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

        # Test successful concept mapping
        response = self.client.get("/api/v1/bible/themes/concept-map/Faith/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data["concept"], "Faith")
        self.assertIn("related_themes", data)
        self.assertIn("co_occurrence_data", data)
        self.assertIn("strength_metrics", data)
        self.assertIn("verse_examples", data)

        # Test concept not found
        response = self.client.get("/api/v1/bible/themes/concept-map/NonExistentConcept/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_theme_endpoints_authentication(self):
        """Test that all theme endpoints require authentication."""
        endpoints = [
            "/api/v1/bible/themes/search/?q=faith",
            f"/api/v1/bible/themes/{self.t1.id}/statistics/",
            "/api/v1/bible/themes/analysis/by-book/Gen/",
            f"/api/v1/bible/themes/{self.t1.id}/progression/",
            "/api/v1/bible/themes/concept-map/Faith/",
        ]

        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED, f"Endpoint {endpoint} should require auth"
            )

    def test_theme_endpoints_response_structure(self):
        """Test that all endpoints return properly structured responses."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

        # Test search response structure
        response = self.client.get("/api/v1/bible/themes/search/?q=faith")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), list)

        # Test statistics response structure
        response = self.client.get(f"/api/v1/bible/themes/{self.t1.id}/statistics/")
        data = response.json()
        required_fields = [
            "theme_id",
            "theme_name",
            "verse_count",
            "book_count",
            "version_count",
            "top_books",
            "testament_distribution",
        ]
        for field in required_fields:
            self.assertIn(field, data)

        # Test analysis response structure
        response = self.client.get("/api/v1/bible/themes/analysis/by-book/Gen/")
        data = response.json()
        required_fields = [
            "book_name",
            "book_osis_code",
            "canonical_order",
            "theme_distribution",
            "chapter_analysis",
            "total_themed_verses",
            "total_book_verses",
            "coverage_percentage",
        ]
        for field in required_fields:
            self.assertIn(field, data)

        # Test progression response structure
        response = self.client.get(f"/api/v1/bible/themes/{self.t1.id}/progression/")
        data = response.json()
        required_fields = ["theme_id", "theme_name", "progression_data", "testament_summary", "peak_books"]
        for field in required_fields:
            self.assertIn(field, data)

        # Test concept map response structure
        response = self.client.get("/api/v1/bible/themes/concept-map/Faith/")
        data = response.json()
        required_fields = ["concept", "related_themes", "co_occurrence_data", "strength_metrics", "verse_examples"]
        for field in required_fields:
            self.assertIn(field, data)
