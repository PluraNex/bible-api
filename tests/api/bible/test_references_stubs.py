"""Smoke tests for References endpoints stubs (T-006)."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.models.auth import APIKey


class ReferencesStubsTest(TestCase):
    def setUp(self):
        # Create a user and API key for authenticated requests
        User = get_user_model()
        self.user = User.objects.create_user(username="tester", email="t@example.com", password="x")
        self.api_key = APIKey.objects.create(
            name="test", user=self.user, key="testkey-123", is_active=True, scopes=["read"]
        )
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

    def test_parse_ok(self):
        resp = self.client.get("/api/v1/bible/references/parse/?q=Jo%203:16-18;1Co%2013")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn("items", data)

    def test_resolve_ok(self):
        resp = self.client.post(
            "/api/v1/bible/references/resolve/",
            {"items": ["Jo 3:16", "1Co 13"], "lang": "pt"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn("results", data)

    def test_normalize_ok(self):
        resp = self.client.post(
            "/api/v1/bible/references/normalize/",
            {"items": ["Cânticos", "1 Reis"], "lang": "pt-BR"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn("normalized", data)
