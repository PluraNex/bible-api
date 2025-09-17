"""
API tests for cross-references endpoints.
"""
from django.contrib.auth.models import User
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


class CrossRefsApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="xrefs_user")
        self.api_key = APIKey.objects.create(name="Xrefs Key", user=self.user, scopes=["read"])

        language = Language.objects.create(code="en-test", name="English Test")
        testament = Testament.objects.create(id=97, name="Test Testament")
        book = CanonicalBook.objects.create(
            osis_code="TestPss", canonical_order=919, testament=testament, chapter_count=150
        )
        BookName.objects.create(
            canonical_book=book,
            language=language,
            name="Test Psalms",
            abbreviation="TPsa",
        )
        version = Version.objects.create(name="Test KJV", code="TEST_KJV", language=language)

        self.v1 = Verse.objects.create(book=book, version=version, chapter=1, number=1, text="Blessed is the man...")
        self.v2 = Verse.objects.create(book=book, version=version, chapter=1, number=2, text="But his delight...")

        self.crossref_primary = CrossReference.objects.create(
            from_book=book,
            from_chapter=1,
            from_verse=1,
            to_book=book,
            to_chapter=1,
            to_verse_start=2,
            to_verse_end=2,
            source="manual",
            confidence=0.92,
        )
        self.crossref_secondary = CrossReference.objects.create(
            from_book=book,
            from_chapter=1,
            from_verse=1,
            to_book=book,
            to_chapter=1,
            to_verse_start=2,
            to_verse_end=2,
            source="openbible",
            confidence=0.35,
        )

        self.theme = Theme.objects.create(name="Faith")
        VerseTheme.objects.create(verse=self.v1, theme=self.theme)

    def _auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

    def test_requires_auth(self):
        self.client.credentials()
        resp = self.client.get(
            "/api/v1/bible/cross-references/for/",
            {"ref": "TPsa 1:1"},
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_crossrefs_for_endpoint(self):
        self._auth()
        resp = self.client.get(
            "/api/v1/bible/cross-references/for/",
            {"ref": "TPsa 1:1"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        payload = resp.json()
        self.assertIn("summary", payload)
        self.assertEqual(payload["summary"]["total"], 2)
        self.assertEqual(payload["summary"]["sources"].get("manual"), 1)
        self.assertEqual(payload["summary"]["sources"].get("openbible"), 1)

    def test_invalid_reference_returns_400(self):
        self._auth()
        resp = self.client.get(
            "/api/v1/bible/cross-references/for/",
            {"ref": "UnknownBook 1:1"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        payload = resp.json()
        self.assertIn("ref", payload.get("errors", {}))

    def test_min_confidence_filter(self):
        self._auth()
        resp = self.client.get(
            "/api/v1/bible/cross-references/for/",
            {"ref": "TPsa 1:1", "min_confidence": "0.8"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        payload = resp.json()
        self.assertEqual(payload["summary"]["total"], 1)
        self.assertListEqual(sorted(payload["summary"]["sources"].keys()), ["manual"])

    def test_limit_alias_applies_page_size(self):
        self._auth()
        resp = self.client.get(
            "/api/v1/bible/cross-references/for/",
            {"ref": "TPsa 1:1", "limit": 1},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        payload = resp.json()
        self.assertEqual(payload["pagination"]["page_size"], 1)
        self.assertEqual(len(payload["results"]), 1)

    def test_crossrefs_by_theme(self):
        self._auth()
        resp = self.client.get(f"/api/v1/bible/cross-references/by-theme/{self.theme.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertGreaterEqual(len(data.get("results", [])), 1)

    def test_crossrefs_by_theme_with_source_filter(self):
        self._auth()
        resp = self.client.get(
            f"/api/v1/bible/cross-references/by-theme/{self.theme.id}/",
            {"source": "manual"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertTrue(all(item["source"] == "manual" for item in data.get("results", [])))
