"""
URL configuration for Verses domain.
"""
from django.urls import path

from .views import VerseDetailView, VersesByChapterView, VersesByThemeView

app_name = "verses"

urlpatterns = [
    path(
        "by-chapter/<str:book_name>/<int:chapter>/",
        VersesByChapterView.as_view(),
        name="verses_by_chapter",
    ),
    path(
        "by-theme/<int:theme_id>/",
        VersesByThemeView.as_view(),
        name="verses_by_theme",
    ),
    path("<int:pk>/", VerseDetailView.as_view(), name="verse_detail"),
]
