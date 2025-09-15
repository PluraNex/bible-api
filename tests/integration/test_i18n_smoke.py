"""
Smoke tests for i18n functionality across Bible API endpoints.

Tests basic language resolution, fallback behavior, and response consistency
for Books, Verses, and Versions endpoints.
"""

from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import connection
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.models import (
    APIKey,
    BookName,
    CanonicalBook,
    Language,
    Testament,
    Verse,
    Version,
)


class I18nSmokeTestCase(TestCase):
    """Smoke tests for i18n functionality."""

    def setUp(self):
        """Set up comprehensive multilingual test data."""
        self.client = APIClient()

        # Create user and API key
        self.user = User.objects.create_user(username="i18n_user")
        self.api_key = APIKey.objects.create(name="I18n Key", user=self.user, scopes=["read"])

        # Create languages (base and regional)
        self.en_lang = Language.objects.create(code="en", name="English")
        self.pt_lang = Language.objects.create(code="pt", name="Portuguese")
        self.pt_br_lang = Language.objects.create(code="pt-BR", name="Portuguese (Brazil)")
        self.es_lang = Language.objects.create(code="es", name="Spanish")

        # Create testament and canonical books
        self.new_testament = Testament.objects.create(name="New Testament")

        self.john = CanonicalBook.objects.create(
            osis_code="John", canonical_order=43, testament=self.new_testament, chapter_count=21
        )

        self.genesis = CanonicalBook.objects.create(
            osis_code="Gen", canonical_order=1, testament=self.new_testament, chapter_count=50
        )

        # Create book names for different languages
        # John book names
        BookName.objects.create(
            canonical_book=self.john,
            language=self.en_lang,
            name="John",
            abbreviation="Jn",
            version=None,  # Default name
        )
        BookName.objects.create(
            canonical_book=self.john,
            language=self.pt_lang,
            name="João",
            abbreviation="Jo",
            version=None,  # Default name
        )
        BookName.objects.create(
            canonical_book=self.john,
            language=self.pt_br_lang,
            name="João (Brasil)",
            abbreviation="Jo-BR",
            version=None,  # Default name
        )

        # Genesis book names
        BookName.objects.create(
            canonical_book=self.genesis, language=self.en_lang, name="Genesis", abbreviation="Gen", version=None
        )
        BookName.objects.create(
            canonical_book=self.genesis, language=self.pt_lang, name="Gênesis", abbreviation="Gn", version=None
        )

        # Create versions
        self.kjv = Version.objects.create(
            name="King James Version", code="EN_KJV", language=self.en_lang, is_active=True
        )

        self.nvi = Version.objects.create(
            name="Nova Versão Internacional", code="PT_NVI", language=self.pt_lang, is_active=True
        )

        self.nvi_br = Version.objects.create(
            name="Nova Versão Internacional (Brasil)",
            code="PT_BR_NVI",
            language=self.pt_br_lang,
            is_active=True,
        )

        # Create some verses for testing
        self.verse_john_kjv = Verse.objects.create(
            book=self.john,
            version=self.kjv,
            chapter=3,
            number=16,
            text="For God so loved the world...",
        )

        self.verse_john_nvi = Verse.objects.create(
            book=self.john,
            version=self.nvi,
            chapter=3,
            number=16,
            text="Porque Deus tanto amou o mundo...",
        )

    def tearDown(self):
        """Clean up after each test."""
        cache.clear()

    def _count_queries(self, func):
        """Helper to count database queries."""
        with self.assertNumQueries(0):
            pass
        initial_queries = len(connection.queries)
        func()
        final_queries = len(connection.queries)
        return final_queries - initial_queries

    def _authenticate(self):
        """Helper to authenticate client."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")


class BooksI18nSmokeTest(I18nSmokeTestCase):
    """Smoke tests for Books i18n functionality."""

    def test_books_list_with_lang_pt(self):
        """Books list with lang=pt should return Portuguese names."""
        self._authenticate()

        response = self.client.get("/api/v1/bible/books/?lang=pt")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("results", data)

        # Find John book in results
        john_book = next((b for b in data["results"] if b["osis_code"] == "John"), None)
        self.assertIsNotNone(john_book, "John book should be in results")
        self.assertEqual(john_book["name"], "João", "Book name should be in Portuguese")

    def test_books_list_with_lang_en(self):
        """Books list with lang=en should return English names."""
        self._authenticate()

        response = self.client.get("/api/v1/bible/books/?lang=en")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        john_book = next((b for b in data["results"] if b["osis_code"] == "John"), None)
        self.assertIsNotNone(john_book)
        self.assertEqual(john_book["name"], "John", "Book name should be in English")

    def test_books_list_fallback_regional_to_base(self):
        """Books list with lang=pt-PT should fallback to base pt."""
        self._authenticate()

        response = self.client.get("/api/v1/bible/books/?lang=pt-PT")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        john_book = next((b for b in data["results"] if b["osis_code"] == "John"), None)
        self.assertIsNotNone(john_book)
        self.assertEqual(john_book["name"], "João", "Should fallback to base Portuguese")

    def test_books_list_fallback_unknown_to_english(self):
        """Books list with unknown language should fallback to English."""
        self._authenticate()

        response = self.client.get("/api/v1/bible/books/?lang=fr")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        john_book = next((b for b in data["results"] if b["osis_code"] == "John"), None)
        self.assertIsNotNone(john_book)
        self.assertEqual(john_book["name"], "John", "Should fallback to English")

    def test_books_list_with_accept_language_header(self):
        """Books list should respect Accept-Language header when no lang param."""
        self._authenticate()

        response = self.client.get("/api/v1/bible/books/", HTTP_ACCEPT_LANGUAGE="pt-BR,pt;q=0.9,en;q=0.8")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        john_book = next((b for b in data["results"] if b["osis_code"] == "John"), None)
        self.assertIsNotNone(john_book)
        # Should resolve to pt-BR first, then pt
        self.assertIn(john_book["name"], ["João (Brasil)", "João"])

    def test_books_detail_with_i18n(self):
        """Book detail should respect language parameter."""
        self._authenticate()

        response = self.client.get("/api/v1/bible/books/John/info/?lang=pt")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data["name"], "João")
        self.assertEqual(data["osis_code"], "John")

    def test_books_404_for_unknown_book(self):
        """Unknown book should return 404 regardless of language."""
        self._authenticate()

        response = self.client.get("/api/v1/bible/books/UnknownBook/info/?lang=pt")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_books_payload_structure(self):
        """Books response should have expected payload structure."""
        self._authenticate()

        response = self.client.get("/api/v1/bible/books/?lang=pt")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("results", data)
        self.assertIn("pagination", data)

        if data["results"]:
            book = data["results"][0]
            required_fields = ["id", "name", "osis_code", "order", "chapter_count"]
            for field in required_fields:
                self.assertIn(field, book, f"Book should have {field} field")


class VersesI18nSmokeTest(I18nSmokeTestCase):
    """Smoke tests for Verses i18n functionality."""

    def test_verses_by_chapter_with_lang_pt(self):
        """Verses by chapter should use Portuguese book names with lang=pt."""
        self._authenticate()

        response = self.client.get("/api/v1/bible/verses/by-chapter/John/3/?lang=pt")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("results", data)

        if data["results"]:
            verse = data["results"][0]
            # Should include book info with Portuguese name
            self.assertIn("book_name", verse)
            self.assertEqual(verse["book_name"], "João")

    def test_verses_with_default_version_for_language(self):
        """Verses should use appropriate default version for language."""
        self._authenticate()

        # Request verses in Portuguese - should use NVI version
        response = self.client.get("/api/v1/bible/verses/by-chapter/John/3/?lang=pt")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        if data["results"]:
            verse = data["results"][0]
            # Should be Portuguese text from NVI
            self.assertIn("Porque Deus tanto amou", verse["text"])

    def test_verses_with_explicit_version(self):
        """Verses should respect explicit version parameter."""
        self._authenticate()

        response = self.client.get(f"/api/v1/bible/verses/by-chapter/John/3/?version={self.kjv.id}&lang=pt")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        if data["results"]:
            verse = data["results"][0]
            # Text should be English (KJV) but book name Portuguese
            self.assertIn("For God so loved", verse["text"])
            self.assertEqual(verse["book_name"], "João")

    def test_verses_404_for_unknown_book(self):
        """Verses for unknown book should return 404."""
        self._authenticate()

        response = self.client.get("/api/v1/bible/verses/by-chapter/UnknownBook/1/?lang=pt")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_verses_payload_structure(self):
        """Verses response should have expected structure."""
        self._authenticate()

        response = self.client.get("/api/v1/bible/verses/by-chapter/John/3/?lang=pt")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("results", data)
        self.assertIn("pagination", data)

        if data["results"]:
            verse = data["results"][0]
            required_fields = ["id", "text", "number", "chapter", "book_name", "version_code"]
            for field in required_fields:
                self.assertIn(field, verse, f"Verse should have {field} field")


class VersionsI18nSmokeTest(I18nSmokeTestCase):
    """Smoke tests for Versions i18n functionality."""

    def test_versions_default_with_lang_pt(self):
        """Versions default endpoint should return Portuguese version for lang=pt."""
        self._authenticate()

        response = self.client.get("/api/v1/bible/versions/default/?lang=pt")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data["language"], "pt")
        self.assertEqual(data["abbreviation"], "NVI")

    def test_versions_default_with_lang_en(self):
        """Versions default endpoint should return English version for lang=en."""
        self._authenticate()

        response = self.client.get("/api/v1/bible/versions/default/?lang=en")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data["language"], "en")
        self.assertEqual(data["abbreviation"], "KJV")

    def test_versions_default_fallback_base_to_regional(self):
        """Versions default should fallback from base to regional when needed."""
        # Remove base Portuguese version to test fallback
        self.nvi.delete()

        self._authenticate()

        response = self.client.get("/api/v1/bible/versions/default/?lang=pt")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data["language"], "pt-BR")  # Should fallback to regional
        self.assertEqual(data["abbreviation"], "NVI")

    def test_versions_default_fallback_regional_to_base(self):
        """Versions default should fallback from regional to base."""
        self._authenticate()

        response = self.client.get("/api/v1/bible/versions/default/?lang=pt-PT")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data["language"], "pt")  # Should fallback to base Portuguese
        self.assertEqual(data["abbreviation"], "NVI")

    def test_versions_default_fallback_to_english(self):
        """Versions default should fallback to English for unknown languages."""
        self._authenticate()

        response = self.client.get("/api/v1/bible/versions/default/?lang=fr")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data["language"], "en")  # Should fallback to English
        self.assertEqual(data["abbreviation"], "KJV")

    def test_versions_default_404_no_active_versions(self):
        """Versions default should return 404 when no active versions exist."""
        # Make all versions inactive
        Version.objects.update(is_active=False)

        self._authenticate()

        response = self.client.get("/api/v1/bible/versions/default/?lang=pt")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        data = response.json()
        self.assertEqual(data["code"], "version_not_found")

    def test_versions_list_with_language_filter(self):
        """Versions list should respect language filter."""
        self._authenticate()

        response = self.client.get("/api/v1/bible/versions/?language=pt")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        # Should only return Portuguese versions
        for version in data["results"]:
            self.assertEqual(version["language"], "pt")

    def test_versions_payload_structure(self):
        """Versions response should have expected structure."""
        self._authenticate()

        response = self.client.get("/api/v1/bible/versions/default/?lang=pt")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        required_fields = ["id", "name", "code", "abbreviation", "language", "description", "is_active"]
        for field in required_fields:
            self.assertIn(field, data, f"Version should have {field} field")


class I18nPerformanceSmokeTest(I18nSmokeTestCase):
    """Performance smoke tests for i18n functionality."""

    def test_books_list_no_n_plus_1_queries(self):
        """Books list should not have N+1 query problems."""
        self._authenticate()

        def make_request():
            response = self.client.get("/api/v1/bible/books/?lang=pt")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            return response

        # Query count should be reasonable (not proportional to book count)
        query_count = self._count_queries(make_request)
        self.assertLess(query_count, 10, "Books list should not have excessive queries")

    def test_verses_list_no_n_plus_1_queries(self):
        """Verses list should not have N+1 query problems."""
        self._authenticate()

        def make_request():
            response = self.client.get("/api/v1/bible/verses/by-chapter/John/3/?lang=pt")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            return response

        query_count = self._count_queries(make_request)
        self.assertLess(query_count, 10, "Verses list should not have excessive queries")

    def test_response_times_reasonable(self):
        """Response times should be reasonable for i18n endpoints."""
        self._authenticate()

        import time

        # Books endpoint
        start_time = time.time()
        response = self.client.get("/api/v1/bible/books/?lang=pt")
        books_time = time.time() - start_time
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(books_time, 1.0, "Books endpoint should respond in < 1s")

        # Versions default endpoint
        start_time = time.time()
        response = self.client.get("/api/v1/bible/versions/default/?lang=pt")
        versions_time = time.time() - start_time
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(versions_time, 0.5, "Versions default should respond in < 0.5s")


class I18nEdgeCasesSmokeTest(I18nSmokeTestCase):
    """Edge cases and error handling for i18n functionality."""

    def test_malformed_lang_parameter(self):
        """Malformed language parameters should be handled gracefully."""
        self._authenticate()

        # Empty lang parameter
        response = self.client.get("/api/v1/bible/books/?lang=")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Very long lang parameter
        response = self.client.get("/api/v1/bible/books/?lang=" + "x" * 100)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Special characters
        response = self.client.get("/api/v1/bible/books/?lang=pt-BR@#$%")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_consistency_across_endpoints(self):
        """Language resolution should be consistent across endpoints."""
        self._authenticate()

        # Same language parameter should resolve consistently
        books_response = self.client.get("/api/v1/bible/books/John/info/?lang=pt")
        versions_response = self.client.get("/api/v1/bible/versions/default/?lang=pt")

        self.assertEqual(books_response.status_code, status.HTTP_200_OK)
        self.assertEqual(versions_response.status_code, status.HTTP_200_OK)

        books_data = books_response.json()
        versions_data = versions_response.json()

        # Both should resolve to same language context
        self.assertEqual(books_data["name"], "João")
        self.assertEqual(versions_data["language"], "pt")

    def test_case_sensitivity_language_codes(self):
        """Language codes should be handled with appropriate case sensitivity."""
        self._authenticate()

        # Test different cases
        response_lower = self.client.get("/api/v1/bible/books/?lang=pt")
        response_upper = self.client.get("/api/v1/bible/books/?lang=PT")
        response_mixed = self.client.get("/api/v1/bible/books/?lang=Pt")

        self.assertEqual(response_lower.status_code, status.HTTP_200_OK)
        self.assertEqual(response_upper.status_code, status.HTTP_200_OK)
        self.assertEqual(response_mixed.status_code, status.HTTP_200_OK)

        # Behavior should be consistent (case-sensitive matching to DB)
        lower_data = response_lower.json()
        upper_data = response_upper.json()

        john_lower = next((b for b in lower_data["results"] if b["osis_code"] == "John"), None)
        john_upper = next((b for b in upper_data["results"] if b["osis_code"] == "John"), None)

        # Both 'pt' and 'PT' should match (case-insensitive)
        self.assertEqual(john_lower["name"], "João")
        self.assertEqual(john_upper["name"], "João")  # Case-insensitive match
