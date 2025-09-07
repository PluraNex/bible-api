"""
Tests for AI module routes and auth behavior.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bible.models import APIKey


class AiRoutesTest(TestCase):
    """Tests for /api/v1/ai/ endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="ai_tester")
        self.api_key = APIKey.objects.create(name="AI Test Key", user=self.user, scopes=["read", "ai"])

    def test_agents_requires_auth(self):
        response = self.client.get("/api/v1/ai/agents/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tools_requires_auth(self):
        response = self.client.get("/api/v1/ai/tools/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_agents_and_tools_with_valid_api_key(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

        agents_resp = self.client.get("/api/v1/ai/agents/")
        self.assertEqual(agents_resp.status_code, status.HTTP_200_OK)
        self.assertIn("agents", agents_resp.json())

        tools_resp = self.client.get("/api/v1/ai/tools/")
        self.assertEqual(tools_resp.status_code, status.HTTP_200_OK)
        self.assertIn("tools", tools_resp.json())

    def test_tool_test_returns_501(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        resp = self.client.post("/api/v1/ai/tools/apply_theme_tags/test/")
        self.assertEqual(resp.status_code, status.HTTP_501_NOT_IMPLEMENTED)
        data = resp.json()
        self.assertEqual(data.get("status"), "test_not_implemented")

    def test_run_endpoints_return_501(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")

        create = self.client.post("/api/v1/ai/agents/themer/runs/")
        self.assertEqual(create.status_code, status.HTTP_501_NOT_IMPLEMENTED)

        detail = self.client.get("/api/v1/ai/runs/123/")
        self.assertEqual(detail.status_code, status.HTTP_501_NOT_IMPLEMENTED)

        approve = self.client.post("/api/v1/ai/runs/123/approve/")
        self.assertEqual(approve.status_code, status.HTTP_501_NOT_IMPLEMENTED)

        cancel = self.client.delete("/api/v1/ai/runs/123/cancel/")
        self.assertEqual(cancel.status_code, status.HTTP_501_NOT_IMPLEMENTED)
