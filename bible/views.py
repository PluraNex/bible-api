"""
Bible API views.
"""
from django.core.cache import cache
from django.db import connections
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class BibleOverviewAPIView(APIView):
    """
    Bible overview endpoint providing basic API information.
    """

    @extend_schema(
        summary="Bible API Overview",
        description="Get basic information about the Bible API",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "api_name": {"type": "string"},
                    "version": {"type": "string"},
                    "description": {"type": "string"},
                    "endpoints": {
                        "type": "object",
                        "properties": {
                            "books": {"type": "string"},
                            "verses": {"type": "string"},
                            "auth": {"type": "string"},
                        },
                    },
                },
            }
        },
    )
    def get(self, request):
        """Get Bible API overview."""
        return Response(
            {
                "api_name": "Bible API",
                "version": "1.0.0",
                "description": "A comprehensive RESTful Bible API with AI integration",
                "endpoints": {
                    "books": "/api/v1/bible/books/",
                    "verses": "/api/v1/bible/verses/",
                    "auth": "/api/v1/auth/",
                },
            },
            status=status.HTTP_200_OK,
        )


# Domain-specific views live under bible/<domain>/views.py


class ReadinessCheckView(APIView):
    """Readiness probe: checks DB and cache connectivity."""
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        summary="Readiness check",
        description="Returns 200 when DB and cache are reachable; otherwise 503 with details.",
        responses={
            200: {
                "type": "object",
                "properties": {"status": {"type": "string"}, "checks": {"type": "object"}},
            },
            503: {
                "type": "object",
                "properties": {"status": {"type": "string"}, "checks": {"type": "object"}},
            },
        },
    )
    def get(self, request):
        checks = {"database": False, "cache": False}
        db_ok = cache_ok = False

        # DB check
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            db_ok = True
        except Exception:
            db_ok = False

        # Cache check
        try:
            cache.set("__readiness_probe__", "ok", 5)
            cache_ok = cache.get("__readiness_probe__") == "ok"
        except Exception:
            cache_ok = False

        checks["database"] = db_ok
        checks["cache"] = cache_ok
        status_code = status.HTTP_200_OK if (db_ok and cache_ok) else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(
            {"status": "ready" if status_code == 200 else "not_ready", "checks": checks}, status=status_code
        )


class PrometheusMetricsView(APIView):
    """Very small placeholder Prometheus metrics endpoint (to be replaced by django-prometheus)."""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        # Minimal text exposition format; replace with real metrics collector in T-009
        content = """# HELP bible_api_dummy_requests_total Dummy total requests
# TYPE bible_api_dummy_requests_total counter
bible_api_dummy_requests_total{service="bible-api"} 1
"""
        return HttpResponse(content, status=200, content_type="text/plain; version=0.0.4; charset=utf-8")
