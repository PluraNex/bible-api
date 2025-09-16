"""
Tests for readiness and Prometheus metrics endpoints.
"""
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


class ReadinessAndPrometheusTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_readiness_endpoint(self):
        resp = self.client.get("/health/readiness/")
        # In CI, DB/cache may be available; accept 200 or 503 but payload shape must be consistent
        self.assertIn(resp.status_code, (status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE))
        data = resp.json()
        self.assertIn("status", data)
        self.assertIn("checks", data)
        self.assertIn("database", data["checks"])  # boolean
        self.assertIn("cache", data["checks"])  # boolean

    def test_prometheus_metrics_endpoint(self):
        resp = self.client.get("/metrics/prometheus/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp["Content-Type"].startswith("text/plain"))
        body = resp.content.decode()
        # Expect some django-prometheus metrics prefix
        self.assertTrue("django_http" in body or "process_cpu" in body)
