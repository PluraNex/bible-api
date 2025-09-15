"""
URL configuration for Books domain.
"""
from django.urls import path

from .views import (
    BookAliasesView,
    BookCanonView,
    BookChapterVersesView,
    BookContextView,
    BookInfoView,
    BookListView,
    BookNeighborsView,
    BookOutlineView,
    BookRangeView,
    BookResolveView,
    BookRestrictedSearchView,
    BooksByAuthorView,
    BooksByTestamentView,
    BookSearchView,
    BookSectionDetailView,
    BookSectionsView,
    BookStatisticsView,
    BookStructureView,
    ChaptersByBookView,
)

app_name = "books"

urlpatterns = [
    # Basic endpoints
    path("", BookListView.as_view(), name="books_list"),
    path("by-author/<str:author_name>/", BooksByAuthorView.as_view(), name="books_by_author"),
    path("by-testament/<int:testament_id>/", BooksByTestamentView.as_view(), name="books_by_testament"),
    # Phase 1: Discovery/Normalization endpoints
    path("search/", BookSearchView.as_view(), name="books_search"),
    path("aliases/", BookAliasesView.as_view(), name="books_aliases"),
    path("resolve/<str:identifier>/", BookResolveView.as_view(), name="books_resolve"),
    path("canon/<str:tradition>/", BookCanonView.as_view(), name="books_canon"),
    # Book-specific endpoints
    path("<str:book_name>/chapters/", ChaptersByBookView.as_view(), name="book_chapters"),
    path("<str:book_name>/info/", BookInfoView.as_view(), name="book_info"),
    path("<str:book_name>/outline/", BookOutlineView.as_view(), name="book_outline"),
    path("<str:book_name>/context/", BookContextView.as_view(), name="book_context"),
    path("<str:book_name>/structure/", BookStructureView.as_view(), name="book_structure"),
    path("<str:book_name>/statistics/", BookStatisticsView.as_view(), name="book_statistics"),
    # Phase 2: Navigation/Structure endpoints
    path("<str:book_name>/neighbors/", BookNeighborsView.as_view(), name="book_neighbors"),
    path("<str:book_name>/sections/", BookSectionsView.as_view(), name="book_sections"),
    path("<str:book_name>/sections/<str:section_id>/", BookSectionDetailView.as_view(), name="book_section_detail"),
    path("<str:book_name>/search/", BookRestrictedSearchView.as_view(), name="book_restricted_search"),
    path("<str:book_name>/<int:chapter>/verses/", BookChapterVersesView.as_view(), name="book_chapter_verses"),
    path("<str:book_name>/range/", BookRangeView.as_view(), name="book_range"),
]
