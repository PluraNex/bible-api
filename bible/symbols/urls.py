"""URL configuration for Biblical Symbols domain."""

from rest_framework.routers import DefaultRouter

from .views import BiblicalSymbolViewSet

router = DefaultRouter()
router.register(r"", BiblicalSymbolViewSet, basename="symbol")

urlpatterns = router.urls
