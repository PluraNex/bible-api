"""
API tests for cross-references endpoints.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.models import APIKey, Book, CrossReference, Theme, Verse, VerseTheme, Version


class CrossRefsApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="xrefs_user")
        self.api_key = APIKey.objects.create(name="Xrefs Key", user=self.user, scopes=["read"])
        book = Book.objects.create(name="Psalms", abbreviation="Psa", order=19, testament="OLD", chapter_count=150)
        ver = Version.objects.create(name="KJV", abbreviation="KJV", language="en")
        self.v1 = Verse.objects.create(book=book, version=ver, chapter=1, number=1, text="Blessed is the man...")
        self.v2 = Verse.objects.create(book=book, version=ver, chapter=1, number=2, text="But his delight...")
        CrossReference.objects.create(from_verse=self.v1, to_verse=self.v2, relationship_type="parallel", source="manual")

    def test_requires_auth(self):
        resp = self.client.get(f"/api/v1/bible/cross-references/verse/{self.v1.id}/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_crossrefs(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get(f"/api/v1/bible/cross-references/verse/{self.v1.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.json().get("results", [])), 1)

    def test_crossrefs_by_theme(self):
        theme = Theme.objects.create(name="Faith")
        VerseTheme.objects.create(verse=self.v1, theme=theme)
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get(f"/api/v1/bible/cross-references/by-theme/{theme.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.json().get("results", [])), 1)
