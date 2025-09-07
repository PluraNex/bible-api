"""
Tests for health and metrics endpoints.
"""
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


class HealthEndpointsTest(TestCase):
    """Tests for health check and metrics endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_health_endpoint_returns_200(self):
        """Test health check endpoint returns 200 status."""
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("status", response.json())
        self.assertEqual(response.json()["status"], "healthy")
        self.assertEqual(response.json()["service"], "bible-api")
        self.assertEqual(response.json()["version"], "1.0.0")

    def test_metrics_endpoint_returns_200(self):
        """Test metrics endpoint returns 200 status."""
        response = self.client.get("/metrics/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("metrics", response.json())

        metrics = response.json()["metrics"]
        self.assertIn("requests_total", metrics)
        self.assertIn("response_time_avg", metrics)
        self.assertIn("database_connections", metrics)

    def test_health_endpoint_content_type(self):
        """Test health endpoint returns JSON content type."""
        response = self.client.get("/health/")

        self.assertEqual(response["Content-Type"], "application/json")

    def test_metrics_endpoint_content_type(self):
        """Test metrics endpoint returns JSON content type."""
        response = self.client.get("/metrics/")

        self.assertEqual(response["Content-Type"], "application/json")
