"""
URL configuration for Bible app.
"""
from django.urls import include, path

from . import views
from .books.views import BookInfoView, BookListView, ChaptersByBookView
from .verses.views import VerseDetailView, VersesByChapterView
from .themes.views import ThemeDetailView, ThemeListView
from .crossrefs.views import CrossReferencesByVerseView

app_name = "bible"

urlpatterns = [
    # Overview
    path("overview/", views.BibleOverviewAPIView.as_view(), name="overview"),

    # Books
    path(
        "books/",
        include(
            [
                path("", BookListView.as_view(), name="books_list"),
                path("<str:book_name>/chapters/", ChaptersByBookView.as_view(), name="book_chapters"),
                path("<str:book_name>/info/", BookInfoView.as_view(), name="book_info"),
            ]
        ),
    ),

    # Verses
    path(
        "verses/",
        include(
            [
                path(
                    "by-chapter/<str:book_name>/<int:chapter>/",
                    VersesByChapterView.as_view(),
                    name="verses_by_chapter",
                ),
                path("<int:pk>/", VerseDetailView.as_view(), name="verse_detail"),
            ]
        ),
    ),

    # Themes
    path(
        "themes/",
        include(
            [
                path("", ThemeListView.as_view(), name="themes_list"),
                path("<int:pk>/detail/", ThemeDetailView.as_view(), name="theme_detail"),
            ]
        ),
    ),

    # Cross-references
    path(
        "cross-references/",
        include(
            [
                path(
                    "verse/<int:verse_id>/",
                    CrossReferencesByVerseView.as_view(),
                    name="crossrefs_by_verse",
                ),
            ]
        ),
    ),
]
