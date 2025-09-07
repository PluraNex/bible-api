"""
API tests for versions endpoints.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.models import APIKey, Version


class VersionsApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="vers_user")
        self.api_key = APIKey.objects.create(name="Vers Key", user=self.user, scopes=["read"])
        Version.objects.create(name="King James Version", abbreviation="KJV", language="en", is_active=True)
        Version.objects.create(name="Nova Versão Internacional", abbreviation="NVI", language="pt", is_active=True)
        Version.objects.create(name="Outdated Version", abbreviation="OV", language="en", is_active=False)

    def test_requires_auth(self):
        self.assertEqual(self.client.get("/api/v1/bible/versions/").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_versions(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/versions/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.json().get("results", [])), 2)

    def test_filter_by_language_and_active(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/versions/?language=en&is_active=true")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        items = resp.json().get("results", [])
        self.assertTrue(all(v["language"].lower() == "en" for v in items))
        self.assertTrue(all(v["is_active"] is True for v in items))

    def test_detail_and_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        ok = self.client.get("/api/v1/bible/versions/KJV/")
        self.assertEqual(ok.status_code, status.HTTP_200_OK)
        self.assertEqual(ok.json()["abbreviation"], "KJV")

        miss = self.client.get("/api/v1/bible/versions/FAKE/")
        self.assertEqual(miss.status_code, status.HTTP_404_NOT_FOUND)
