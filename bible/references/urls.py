"""URL configuration for References domain (T-006)."""
from django.urls import path

from .views import ReferenceNormalizeView, ReferenceParseView, ReferenceResolveView

app_name = "references"

urlpatterns = [
    path("parse/", ReferenceParseView.as_view(), name="references_parse"),
    path("resolve/", ReferenceResolveView.as_view(), name="references_resolve"),
    path("normalize/", ReferenceNormalizeView.as_view(), name="references_normalize"),
]
