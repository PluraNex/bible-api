"""
URL configuration for Cross-References domain.
"""
from django.urls import path

from .views import (
    CrossReferencesByThemeView,
    CrossReferencesByVerseDeprecatedView,
    CrossReferencesByVerseView,
    CrossReferencesGroupedView,
    CrossReferencesParallelsView,
)

app_name = "crossrefs"

urlpatterns = [
    # New: textual reference support via query param ?ref=
    path("for/", CrossReferencesByVerseView.as_view(), name="crossrefs_for"),
    path("for/grouped/", CrossReferencesGroupedView.as_view(), name="crossrefs_for_grouped"),
    path("parallels/", CrossReferencesParallelsView.as_view(), name="crossrefs_parallels"),
    path(
        "verse/<int:verse_id>/",
        CrossReferencesByVerseDeprecatedView.as_view(),
        name="crossrefs_by_verse",
    ),
    path(
        "by-theme/<int:theme_id>/",
        CrossReferencesByThemeView.as_view(),
        name="crossrefs_by_theme",
    ),
]
