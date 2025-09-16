"""
Simple test to improve bible.views coverage.
"""
from django.test import TestCase
from rest_framework.test import APIClient


class BibleViewsCoverageTest(TestCase):
    """Test to cover missing lines in bible.views module."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

    def test_prometheus_view_get(self):
        """Test PrometheusMetricsView.get method directly."""
        from bible.views import PrometheusMetricsView
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get('/metrics/prometheus/')

        view = PrometheusMetricsView()
        response = view.get(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], "text/plain; version=0.0.4; charset=utf-8")

        content = response.content.decode()
        self.assertIn("bible_api_dummy_requests_total", content)  # This should cover lines 114-118