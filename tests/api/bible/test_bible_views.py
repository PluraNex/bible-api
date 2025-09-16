"""
Tests for bible.views module.
"""
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


class BibleOverviewAPIViewTest(TestCase):
    """Test BibleOverviewAPIView."""

    def setUp(self):
        """Set up test data."""
        from django.contrib.auth.models import User
        from bible.models import APIKey

        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser")
        self.api_key = APIKey.objects.create(name="Test Key", user=self.user, scopes=["read"])

    def test_get_bible_overview(self):
        """Test GET request to bible overview endpoint."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key.key}")
        response = self.client.get("/api/v1/bible/overview/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data["api_name"], "Bible API")
        self.assertEqual(data["version"], "1.0.0")
        self.assertIn("description", data)
        self.assertIn("endpoints", data)

        # Check endpoints structure
        endpoints = data["endpoints"]
        self.assertIn("books", endpoints)
        self.assertIn("verses", endpoints)
        self.assertIn("auth", endpoints)
        self.assertEqual(endpoints["books"], "/api/v1/bible/books/")
        self.assertEqual(endpoints["verses"], "/api/v1/bible/verses/")
        self.assertEqual(endpoints["auth"], "/api/v1/auth/")


class PrometheusMetricsViewTest(TestCase):
    """Test PrometheusMetricsView."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

    def test_get_prometheus_metrics(self):
        """Test GET request to prometheus metrics endpoint."""
        response = self.client.get("/metrics/prometheus/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/plain; version=0.0.4; charset=utf-8")

        # Check that response contains expected prometheus format
        content = response.content.decode()
        self.assertIn("# HELP", content)
        self.assertIn("# TYPE", content)
        # Since we're using django-prometheus, check for common metrics
        self.assertTrue(any(metric in content for metric in ['python_info', 'process_', 'django_']))

    def test_prometheus_metrics_public_access(self):
        """Test that prometheus metrics endpoint is publicly accessible."""
        # Should not require authentication
        response = self.client.get("/metrics/prometheus/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)