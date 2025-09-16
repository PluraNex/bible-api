"""
Tests for readiness and monitoring views.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


class ReadinessCheckViewTest(TestCase):
    """Tests for ReadinessCheckView."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

    def test_readiness_success(self):
        """Test readiness check when all services are healthy."""
        response = self.client.get("/health/readiness/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data["status"], "ready")
        self.assertIn("checks", data)

    @patch('bible.views.connections')
    def test_readiness_database_failure(self, mock_connections):
        """Test readiness check when database is not reachable."""
        # Mock database connection failure
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Database connection failed")
        mock_connections.__getitem__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        response = self.client.get("/health/readiness/")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

        data = response.json()
        self.assertEqual(data["status"], "not_ready")
        self.assertFalse(data["checks"]["database"])

    @patch('bible.views.cache')
    def test_readiness_cache_failure(self, mock_cache):
        """Test readiness check when cache is not reachable."""
        # Mock cache failure
        mock_cache.set.side_effect = Exception("Cache connection failed")

        response = self.client.get("/health/readiness/")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

        data = response.json()
        self.assertEqual(data["status"], "not_ready")
        self.assertFalse(data["checks"]["cache"])

    @patch('bible.views.cache')
    def test_readiness_cache_get_failure(self, mock_cache):
        """Test readiness check when cache get operation fails."""
        # Mock cache get returning wrong value
        mock_cache.set.return_value = None  # set succeeds
        mock_cache.get.side_effect = Exception("Cache get failed")

        response = self.client.get("/health/readiness/")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

        data = response.json()
        self.assertEqual(data["status"], "not_ready")
        self.assertFalse(data["checks"]["cache"])


class PrometheusMetricsViewTest(TestCase):
    """Tests for PrometheusMetricsView."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

    def test_prometheus_metrics_response(self):
        """Test prometheus metrics endpoint returns expected format."""
        response = self.client.get("/metrics/prometheus/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], "text/plain; version=0.0.4; charset=utf-8")

        content = response.content.decode()
        # Check for common prometheus metrics (should be django-prometheus format)
        self.assertIn("# HELP", content)
        self.assertIn("# TYPE", content)
        # Should contain some django metrics
        self.assertTrue(any(metric in content for metric in ['django_', 'python_', 'process_']))

    def test_prometheus_metrics_no_auth_required(self):
        """Test that prometheus metrics endpoint doesn't require authentication."""
        # Should work without any authentication headers
        response = self.client.get("/metrics/prometheus/")
        self.assertEqual(response.status_code, 200)