"""
Tests for AI endpoints (skeleton implementation).
"""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class AIEndpointsTest(APITestCase):
    """Test AI endpoints skeleton implementation."""

    def test_agents_list_endpoint_returns_200(self):
        """Test that agents list endpoint returns 200."""
        url = reverse("ai:ai_agents_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("agents", response.data)

    def test_tools_list_endpoint_returns_200(self):
        """Test that tools list endpoint returns 200."""
        url = reverse("ai:ai_tools_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tools", response.data)

    def test_tool_test_endpoint_requires_authentication(self):
        """Test that tool test endpoint requires authentication (401)."""
        url = reverse("ai:ai_tool_test", kwargs={"tool": "test-tool"})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_agent_run_create_endpoint_requires_authentication(self):
        """Test that agent run create endpoint requires authentication (401)."""
        url = reverse("ai:ai_agent_run_create", kwargs={"name": "themer"})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_agent_run_detail_endpoint_requires_authentication(self):
        """Test that agent run detail endpoint requires authentication (401)."""
        url = reverse("ai:ai_run_detail", kwargs={"run_id": 123})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_agent_run_approve_endpoint_requires_authentication(self):
        """Test that agent run approve endpoint requires authentication (401)."""
        url = reverse("ai:ai_run_approve", kwargs={"run_id": 123})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_agent_run_cancel_endpoint_requires_authentication(self):
        """Test that agent run cancel endpoint requires authentication (401)."""
        url = reverse("ai:ai_run_cancel", kwargs={"run_id": 123})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
