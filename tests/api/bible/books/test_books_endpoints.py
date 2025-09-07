"""
API tests for books endpoints.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.models import APIKey, Book


class BooksApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="books_user")
        self.api_key = APIKey.objects.create(name="Books Key", user=self.user, scopes=["read"])
        Book.objects.create(name="Genesis", abbreviation="Gen", order=1, testament="OLD", chapter_count=50)
        Book.objects.create(name="Exodus", abbreviation="Exo", order=2, testament="OLD", chapter_count=40)

    def test_requires_auth(self):
        self.assertEqual(self.client.get("/api/v1/bible/books/").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_books(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/books/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.json().get("results", [])), 2)

    def test_book_info_and_chapters(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        info = self.client.get("/api/v1/bible/books/Genesis/info/")
        self.assertEqual(info.status_code, status.HTTP_200_OK)
        self.assertEqual(info.json().get("abbreviation"), "Gen")

        chapters = self.client.get("/api/v1/bible/books/Genesis/chapters/")
        self.assertEqual(chapters.status_code, status.HTTP_200_OK)
        self.assertEqual(len(chapters.json().get("chapters", [])), 50)

    def test_book_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/books/Fake/chapters/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
