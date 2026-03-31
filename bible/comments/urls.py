"""URLs for commentary domain."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AuthorViewSet, CommentaryViewSet, SourceViewSet

router = DefaultRouter()
router.register(r"entries", CommentaryViewSet, basename="commentary-entry")
router.register(r"authors", AuthorViewSet, basename="commentary-author")
router.register(r"sources", SourceViewSet, basename="commentary-source")

urlpatterns = [
    path("", include(router.urls)),
]
