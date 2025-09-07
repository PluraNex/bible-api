"""
API tests for themes endpoints.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.models import APIKey, Theme


class ThemesApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="themes_user")
        self.api_key = APIKey.objects.create(name="Themes Key", user=self.user, scopes=["read"])
        self.t1 = Theme.objects.create(name="Faith")
        self.t2 = Theme.objects.create(name="Love")

    def test_requires_auth(self):
        self.assertEqual(self.client.get("/api/v1/bible/themes/").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_and_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        lst = self.client.get("/api/v1/bible/themes/")
        self.assertEqual(lst.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(lst.json().get("results", [])), 2)

        detail = self.client.get(f"/api/v1/bible/themes/{self.t1.id}/detail/")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.json().get("name"), "Faith")
