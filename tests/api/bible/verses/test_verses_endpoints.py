"""
API tests for verses endpoints.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.models import APIKey, Book, Verse, Version, Theme, VerseTheme


class VersesApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="verses_user")
        self.api_key = APIKey.objects.create(name="Verses Key", user=self.user, scopes=["read"])

        self.book = Book.objects.create(name="John", abbreviation="Joh", order=43, testament="NEW", chapter_count=21)
        self.version = Version.objects.create(name="King James Version", abbreviation="KJV", language="en")
        self.v1 = Verse.objects.create(book=self.book, version=self.version, chapter=3, number=16, text="For God so loved...")
        self.v2 = Verse.objects.create(book=self.book, version=self.version, chapter=3, number=17, text="For God sent not...")

    def test_requires_auth(self):
        self.assertEqual(self.client.get(f"/api/v1/bible/verses/by-chapter/{self.book.name}/3/").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_by_chapter_and_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        by_chapter = self.client.get(f"/api/v1/bible/verses/by-chapter/{self.book.name}/3/")
        self.assertEqual(by_chapter.status_code, status.HTTP_200_OK)
        self.assertEqual(len(by_chapter.json().get("results", [])), 2)

        detail = self.client.get(f"/api/v1/bible/verses/{self.v1.id}/")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertIn("text", detail.json())

    def test_book_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/verses/by-chapter/Fake/1/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_verses_by_theme(self):
        theme = Theme.objects.create(name="Love")
        VerseTheme.objects.create(verse=self.v1, theme=theme)
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get(f"/api/v1/bible/verses/by-theme/{theme.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json().get("results", [])), 1)

    def test_verses_by_theme_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/verses/by-theme/999/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json().get("results", [])), 0)
