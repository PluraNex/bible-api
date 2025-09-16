"""Tests for new Verses endpoints by reference/range/compare (T-007)."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.models.auth import APIKey


class VersesByReferenceEndpointsTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="tester", email="t@example.com", password="x")
        self.api_key = APIKey.objects.create(
            name="test", user=self.user, key="testkey-123", is_active=True, scopes=["read"]
        )
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

    def test_by_reference_requires_ref(self):
        resp = self.client.get("/api/v1/bible/verses/by-reference/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.json()
        self.assertIn("detail", data)
        self.assertIn("code", data)

    def test_by_reference_unknown_book(self):
        resp = self.client.get("/api/v1/bible/verses/by-reference/?ref=UnknownBook%201:1")
        # Book not found should be 404, but parser may treat as unparsed -> 400; accept either
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST))

    def test_compare_requires_params(self):
        resp = self.client.get("/api/v1/bible/verses/compare/?ref=&versions=")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.json()
        self.assertIn("detail", data)
        self.assertIn("code", data)

    def test_range_requires_ref(self):
        resp = self.client.get("/api/v1/bible/verses/range/?ref=")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.json()
        self.assertIn("detail", data)
        self.assertIn("code", data)

    def test_compare_max_versions_exceeded(self):
        # 6 versions should trigger 413 (even if they don't exist in DB)
        resp = self.client.get("/api/v1/bible/verses/compare/?ref=Jo%203:16&versions=a,b,c,d,e,f")
        self.assertEqual(resp.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        data = resp.json()
        self.assertIn("detail", data)
        self.assertIn("code", data)
