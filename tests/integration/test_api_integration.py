"""Integration tests for Bible API endpoints."""

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.models import (
    APIKey,
    BookName,
    CanonicalBook,
    CrossReference,
    Language,
    Testament,
    Theme,
    Verse,
    VerseTheme,
    Version,
)


class BibleAPIIntegrationTest(TestCase):
    """Integration tests for Bible API endpoints."""

    def setUp(self):
        """Set up comprehensive test data."""
        self.client = APIClient()

        # Create users and API keys
        self.user1 = User.objects.create_user(username="user1", email="user1@test.com")
        self.user2 = User.objects.create_user(username="user2", email="user2@test.com")

        # API key with read permissions
        self.api_key_read = APIKey.objects.create(name="Read Key", user=self.user1, scopes=["read"])

        # API key with full permissions
        self.api_key_full = APIKey.objects.create(name="Full Key", user=self.user2, scopes=["read", "write", "admin"])

        # Create languages
        self.english = Language.objects.create(code="en", name="English")
        self.portuguese = Language.objects.create(code="pt", name="Portuguese")

        # Create testaments
        self.old_testament = Testament.objects.create(name="Old Testament")
        self.new_testament = Testament.objects.create(name="New Testament")

        # Create canonical books
        self.genesis = CanonicalBook.objects.create(
            osis_code="Gen", canonical_order=1, testament=self.old_testament, chapter_count=50
        )

        self.john = CanonicalBook.objects.create(
            osis_code="John", canonical_order=43, testament=self.new_testament, chapter_count=21
        )

        # Create book names
        BookName.objects.create(canonical_book=self.genesis, language=self.english, name="Genesis", abbreviation="Gen")

        BookName.objects.create(canonical_book=self.john, language=self.english, name="John", abbreviation="Jn")

        BookName.objects.create(canonical_book=self.john, language=self.portuguese, name="João", abbreviation="Jo")

        # Create versions
        self.kjv = Version.objects.create(name="King James Version", code="EN_KJV", language=self.english)

        self.nvi = Version.objects.create(name="Nova Versão Internacional", code="PT_NVI", language=self.portuguese)

        # Create verses
        self.verse_john_3_16_kjv = Verse.objects.create(
            book=self.john,
            version=self.kjv,
            chapter=3,
            number=16,
            text="For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
        )

        self.verse_john_3_17_kjv = Verse.objects.create(
            book=self.john,
            version=self.kjv,
            chapter=3,
            number=17,
            text="For God sent not his Son into the world to condemn the world; but that the world through him might be saved.",
        )

        self.verse_john_3_16_nvi = Verse.objects.create(
            book=self.john,
            version=self.nvi,
            chapter=3,
            number=16,
            text="Porque Deus tanto amou o mundo que deu o seu Filho Unigênito, para que todo o que nele crer não pereça, mas tenha a vida eterna.",
        )

        # Create theme and associate with verse
        self.love_theme = Theme.objects.create(name="Love", description="Verses about God's love")
        VerseTheme.objects.create(verse=self.verse_john_3_16_kjv, theme=self.love_theme)
        VerseTheme.objects.create(verse=self.verse_john_3_16_nvi, theme=self.love_theme)

        # Create cross reference
        self.cross_ref = CrossReference.objects.create(
            from_book=self.john,
            from_chapter=3,
            from_verse=16,
            to_book=self.john,
            to_chapter=3,
            to_verse_start=17,
            to_verse_end=17,
        )

    def tearDown(self):
        """Clean up after each test."""
        cache.clear()

    def test_complete_verse_workflow(self):
        """Test complete workflow: books -> chapters -> verses -> details."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_read.key}")

        # 1. Get all books
        books_response = self.client.get("/api/v1/bible/books/")
        self.assertEqual(books_response.status_code, status.HTTP_200_OK)
        books_data = books_response.json()
        self.assertGreaterEqual(len(books_data["results"]), 2)

        # 2. Find John in the results
        john_book = next((b for b in books_data["results"] if b["name"] == "John"), None)
        self.assertIsNotNone(john_book)

        # 3. Get verses from John chapter 3
        verses_response = self.client.get("/api/v1/bible/verses/by-chapter/John/3/")
        self.assertEqual(verses_response.status_code, status.HTTP_200_OK)
        verses_data = verses_response.json()
        self.assertEqual(len(verses_data["results"]), 2)

        # 4. Get details of John 3:16
        verse_detail_response = self.client.get(f"/api/v1/bible/verses/{self.verse_john_3_16_kjv.id}/")
        self.assertEqual(verse_detail_response.status_code, status.HTTP_200_OK)
        verse_detail_data = verse_detail_response.json()
        self.assertEqual(verse_detail_data["text"], self.verse_john_3_16_kjv.text)

    def test_api_consistency_and_pagination(self):
        """Test API consistency and pagination across endpoints."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_read.key}")

        # Test book list pagination
        response = self.client.get("/api/v1/bible/books/?page_size=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertIn("pagination", data)

        # Test verses pagination
        response = self.client.get("/api/v1/bible/verses/by-chapter/John/3/?page_size=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertIn("pagination", data)

    def test_authentication_and_authorization(self):
        """Test authentication and authorization mechanisms."""
        # Test without authentication
        response = self.client.get("/api/v1/bible/books/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test with invalid API key
        self.client.credentials(HTTP_AUTHORIZATION="Api-Key invalid-key")
        response = self.client.get("/api/v1/bible/books/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test with valid API key
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_read.key}")
        response = self.client.get("/api/v1/bible/books/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cross_reference_navigation(self):
        """Test cross-reference navigation functionality."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_read.key}")

        # Get cross references for John 3:16
        response = self.client.get(f"/api/v1/bible/cross-references/verse/{self.verse_john_3_16_kjv.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertGreaterEqual(len(data["results"]), 1)

        # Verify cross reference details
        cross_ref = data["results"][0]
        self.assertEqual(cross_ref["to_chapter"], 3)
        self.assertEqual(cross_ref["to_verse_start"], 17)

    def test_theme_based_verse_discovery(self):
        """Test theme-based verse discovery."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_read.key}")

        # Get verses by theme
        response = self.client.get(f"/api/v1/bible/verses/by-theme/{self.love_theme.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertGreaterEqual(len(data["results"]), 2)

        # Verify verses are associated with the theme
        verse_ids = [v["id"] for v in data["results"]]
        self.assertIn(self.verse_john_3_16_kjv.id, verse_ids)
        self.assertIn(self.verse_john_3_16_nvi.id, verse_ids)

    def test_version_filtering_and_localization(self):
        """Test version filtering and localization."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_read.key}")

        # Get KJV version of John 3:16
        response = self.client.get(f"/api/v1/bible/verses/by-chapter/John/3/?version={self.kjv.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        kjv_verse = next((v for v in data["results"] if v["number"] == 16), None)
        self.assertIsNotNone(kjv_verse)
        self.assertIn("whosoever believeth", kjv_verse["text"])

        # Get NVI version of John 3:16
        response = self.client.get(f"/api/v1/bible/verses/by-chapter/John/3/?version={self.nvi.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        nvi_verse = next((v for v in data["results"] if v["number"] == 16), None)
        self.assertIsNotNone(nvi_verse)
        self.assertIn("nele crer", nvi_verse["text"])

    def test_error_handling_and_edge_cases(self):
        """Test error handling and edge cases."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key_read.key}")

        # Test invalid book reference
        response = self.client.get("/api/v1/bible/books/InvalidBook/info/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Test invalid verse ID
        response = self.client.get("/api/v1/bible/verses/999999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Test invalid theme ID - may return empty results instead of 404
        response = self.client.get("/api/v1/bible/verses/by-theme/999999/")
        # Accept either 404 or 200 with empty results
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            self.assertEqual(data.get("count", 0), 0)  # Should have no results
        else:
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Test invalid cross-reference request - may return empty results instead of 404
        response = self.client.get("/api/v1/bible/cross-references/verse/999999/")
        # Accept either 404 or 200 with empty results
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            self.assertEqual(data.get("count", 0), 0)  # Should have no results
        else:
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class BibleAPICacheIntegrationTest(TestCase):
    """Integration tests for Bible API cache behavior."""

    def setUp(self):
        """Set up test data for cache tests."""
        self.client = APIClient()

        # Create user and API key
        self.user = User.objects.create_user(username="cache_test_user")
        self.api_key = APIKey.objects.create(name="Cache Test Key", user=self.user, scopes=["read"])

        # Create test data
        self.testament = Testament.objects.create(name="Test Testament")
        self.book = CanonicalBook.objects.create(
            osis_code="Test", canonical_order=1, testament=self.testament, chapter_count=10
        )
        self.language = Language.objects.create(code="en", name="English")
        BookName.objects.create(canonical_book=self.book, language=self.language, name="Test Book", abbreviation="TB")

    def test_cache_behavior_consistency(self):
        """Test that cache behaves consistently across requests."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

        # Make first request
        response1 = self.client.get("/api/v1/bible/books/Test/info/")
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        data1 = response1.json()

        # Make second request (should hit cache)
        response2 = self.client.get("/api/v1/bible/books/Test/info/")
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        data2 = response2.json()

        # Responses should be identical
        self.assertEqual(data1, data2)
