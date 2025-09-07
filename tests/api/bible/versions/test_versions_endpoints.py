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

    def test_detail_abbreviation_case_insensitive(self):
        """Detail lookup by abbreviation should be case-insensitive."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/versions/kjv/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["abbreviation"], "KJV")

    def test_list_ordering_by_name(self):
        """List should be ordered deterministically by name (asc)."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/versions/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [item["name"] for item in resp.json().get("results", [])]
        self.assertEqual(names, sorted(names))

    def test_filter_is_active_false(self):
        """Filtering by is_active=false should return only inactive versions."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/versions/?is_active=false")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        items = resp.json().get("results", [])
        self.assertGreaterEqual(len(items), 1)
        self.assertTrue(all(item["is_active"] is False for item in items))

    def test_language_filter_case_insensitive(self):
        """Language filter should be case-insensitive."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.get("/api/v1/bible/versions/?language=EN")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        items = resp.json().get("results", [])
        self.assertTrue(all(v["language"].lower() == "en" for v in items))

    def test_is_active_various_formats(self):
        """is_active should accept various boolean formats."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

        # Test different true formats
        for true_val in ["1", "true", "True", "TRUE", "yes", "YES"]:
            resp = self.client.get(f"/api/v1/bible/versions/?is_active={true_val}")
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            items = resp.json().get("results", [])
            if items:  # Only check if we have results
                self.assertTrue(all(item["is_active"] is True for item in items))

    def test_requires_read_scope(self):
        """Endpoints should require 'read' scope."""
        # API key without 'read' scope
        no_read_key = APIKey.objects.create(name="No Read Key", user=self.user, scopes=["write"])  # Missing 'read'

        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {no_read_key.key}")

        # Both endpoints should return 403
        list_resp = self.client.get("/api/v1/bible/versions/")
        self.assertEqual(list_resp.status_code, status.HTTP_403_FORBIDDEN)

        detail_resp = self.client.get("/api/v1/bible/versions/KJV/")
        self.assertEqual(detail_resp.status_code, status.HTTP_403_FORBIDDEN)
