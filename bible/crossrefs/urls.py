"""
URL configuration for Cross-References domain.
"""
from django.urls import path

from .views import CrossReferencesByThemeView, CrossReferencesByVerseView

app_name = "crossrefs"

urlpatterns = [
    path(
        "verse/<int:verse_id>/",
        CrossReferencesByVerseView.as_view(),
        name="crossrefs_by_verse",
    ),
    path(
        "by-theme/<int:theme_id>/",
        CrossReferencesByThemeView.as_view(),
        name="crossrefs_by_theme",
    ),
]
