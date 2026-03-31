"""URLs for Biblical Images domain."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ArtistViewSet, BiblicalImageViewSet

router = DefaultRouter()
router.register(r"artists", ArtistViewSet, basename="artist")
router.register(r"", BiblicalImageViewSet, basename="image")

urlpatterns = [
    path("", include(router.urls)),
]
