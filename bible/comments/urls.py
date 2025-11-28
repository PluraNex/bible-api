"""URLs for commentary domain."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CommentaryViewSet

router = DefaultRouter()
router.register(r"", CommentaryViewSet, basename="commentary")

urlpatterns = [
    path("", include(router.urls)),
]
