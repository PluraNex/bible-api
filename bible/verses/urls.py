"""
URL configuration for Verses domain.
"""
from django.urls import path

from .views import (
    VerseDetailView,
    VersesByChapterView,
    VersesByReferenceView,
    VersesByThemeView,
    VersesCompareView,
    VersesRangeView,
)

app_name = "verses"

urlpatterns = [
    path(
        "by-chapter/<str:book_name>/<int:chapter>/",
        VersesByChapterView.as_view(),
        name="verses_by_chapter",
    ),
    path(
        "by-reference/",
        VersesByReferenceView.as_view(),
        name="verses_by_reference",
    ),
    path(
        "range/",
        VersesRangeView.as_view(),
        name="verses_range",
    ),
    path(
        "compare/",
        VersesCompareView.as_view(),
        name="verses_compare",
    ),
    path(
        "by-theme/<int:theme_id>/",
        VersesByThemeView.as_view(),
        name="verses_by_theme",
    ),
    path("<int:pk>/", VerseDetailView.as_view(), name="verse_detail"),
]
