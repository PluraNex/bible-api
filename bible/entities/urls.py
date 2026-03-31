"""URL configuration for Biblical Entities domain."""

from rest_framework.routers import DefaultRouter

from .views import CanonicalEntityViewSet

router = DefaultRouter()
router.register(r"", CanonicalEntityViewSet, basename="entity")

urlpatterns = router.urls
