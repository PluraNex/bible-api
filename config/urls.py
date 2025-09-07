"""
URL configuration for Bible API project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def health_check(request):
    """Simple health check endpoint."""
    return JsonResponse({"status": "healthy", "service": "bible-api", "version": "1.0.0"})


def metrics(request):
    """Basic metrics endpoint."""
    return JsonResponse({"metrics": {"requests_total": 0, "response_time_avg": 0, "database_connections": 0}})


urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # Health and metrics
    path("health/", health_check, name="health"),
    path("metrics/", metrics, name="metrics"),
    # API v1
    path(
        "api/v1/",
        include(
            [
                path("bible/", include("bible.urls")),
                path("auth/", include("bible.apps.auth.urls")),
                # OpenAPI schema
                path("schema/", SpectacularAPIView.as_view(), name="schema"),
                path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
            ]
        ),
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
