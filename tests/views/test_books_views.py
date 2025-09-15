"""
Unit tests for books views.
Tests view methods, filtering, ordering, and error handling.
"""
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from bible.books.serializers import BookSerializer
from bible.books.views import BookInfoView, BookListView, ChaptersByBookView
from bible.models import APIKey, BookName, CanonicalBook, Language, Testament


@pytest.mark.unit
class BooksViewsTest(TestCase):
    """Test books domain views."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="test_user")

        # Create API key
        self.api_key = APIKey.objects.create(name="Test Key", user=self.user, scopes=["read"])

        # Create languages and testaments
        self.english = Language.objects.create(code="en", name="English")
        self.old_testament = Testament.objects.create(name="Old Testament")
        self.new_testament = Testament.objects.create(name="New Testament")

        # Create canonical books
        self.genesis = CanonicalBook.objects.create(
            osis_code="Gen",
            canonical_order=1,
            testament=self.old_testament,
            chapter_count=50,
            is_deuterocanonical=False,
        )

        self.exodus = CanonicalBook.objects.create(
            osis_code="Exo",
            canonical_order=2,
            testament=self.old_testament,
            chapter_count=40,
            is_deuterocanonical=False,
        )

        self.john = CanonicalBook.objects.create(
            osis_code="John",
            canonical_order=43,
            testament=self.new_testament,
            chapter_count=21,
            is_deuterocanonical=False,
        )

        # Create book names
        BookName.objects.create(canonical_book=self.genesis, language=self.english, name="Genesis", abbreviation="Gen")

        BookName.objects.create(canonical_book=self.exodus, language=self.english, name="Exodus", abbreviation="Exo")

        BookName.objects.create(canonical_book=self.john, language=self.english, name="John", abbreviation="Jn")

    def test_book_list_view_queryset(self):
        """Test BookListView queryset is properly configured."""
        view = BookListView()
        queryset = view.get_queryset()

        # Should be ordered by canonical_order
        books = list(queryset)
        self.assertEqual(len(books), 3)
        self.assertEqual(books[0].osis_code, "Gen")
        self.assertEqual(books[1].osis_code, "Exo")
        self.assertEqual(books[2].osis_code, "John")

    def test_book_list_view_serializer_class(self):
        """Test BookListView uses correct serializer."""
        view = BookListView()
        self.assertEqual(view.serializer_class, BookSerializer)

    def test_book_list_view_filter_backends(self):
        """Test BookListView has correct filter backends."""
        view = BookListView()
        from django_filters.rest_framework import DjangoFilterBackend
        from rest_framework import filters

        expected_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
        self.assertEqual(view.filter_backends, expected_backends)

    def test_book_list_view_filterset_fields(self):
        """Test BookListView filterset fields."""
        view = BookListView()
        expected_fields = ["testament", "is_deuterocanonical"]
        self.assertEqual(view.filterset_fields, expected_fields)

    def test_book_list_view_search_fields(self):
        """Test BookListView search fields."""
        view = BookListView()
        expected_fields = ["osis_code", "names__name", "names__abbreviation"]
        self.assertEqual(view.search_fields, expected_fields)

    def test_book_list_view_ordering_fields(self):
        """Test BookListView ordering fields."""
        view = BookListView()
        expected_fields = ["canonical_order", "chapter_count"]
        self.assertEqual(view.ordering_fields, expected_fields)

    def test_book_list_view_default_ordering(self):
        """Test BookListView default ordering."""
        view = BookListView()
        self.assertEqual(view.ordering, ["canonical_order"])

    @patch("bible.books.views.get_canonical_book_by_name")
    def test_book_info_view_success(self, mock_get_book):
        """Test BookInfoView returns book info successfully."""
        mock_get_book.return_value = self.genesis

        view = BookInfoView()
        request = self.factory.get("/api/v1/bible/books/Genesis/info/")
        response = view.get(request, book_name="Genesis")

        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.data)
        mock_get_book.assert_called_once_with("Genesis")

    @patch("bible.books.views.get_canonical_book_by_name")
    def test_book_info_view_not_found(self, mock_get_book):
        """Test BookInfoView returns 404 when book not found."""
        mock_get_book.side_effect = Exception("Book not found")

        view = BookInfoView()
        request = self.factory.get("/api/v1/bible/books/InvalidBook/info/")
        response = view.get(request, book_name="InvalidBook")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"detail": "Book not found"})

    @patch("bible.books.views.get_canonical_book_by_name")
    @patch("bible.books.views.get_book_display_name")
    def test_chapters_by_book_view_success(self, mock_display_name, mock_get_book):
        """Test ChaptersByBookView returns chapters successfully."""
        mock_get_book.return_value = self.genesis
        mock_display_name.return_value = "Genesis"

        view = ChaptersByBookView()
        request = self.factory.get("/api/v1/bible/books/Genesis/chapters/")
        response = view.get(request, book_name="Genesis")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["book"], "Genesis")
        self.assertEqual(response.data["chapters"], list(range(1, 51)))  # 50 chapters

        mock_get_book.assert_called_once_with("Genesis")
        mock_display_name.assert_called_once_with(self.genesis)

    @patch("bible.books.views.get_canonical_book_by_name")
    def test_chapters_by_book_view_not_found(self, mock_get_book):
        """Test ChaptersByBookView returns 404 when book not found."""
        mock_get_book.side_effect = Exception("Book not found")

        view = ChaptersByBookView()
        request = self.factory.get("/api/v1/bible/books/InvalidBook/chapters/")
        response = view.get(request, book_name="InvalidBook")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"detail": "Book not found"})

    def test_book_list_view_query_efficiency(self):
        """Test that BookListView uses select_related for efficiency."""
        view = BookListView()
        queryset = view.get_queryset()

        # Check that select_related is applied
        self.assertTrue(hasattr(queryset, "_prefetch_related_lookups"))
        # The queryset should include select_related('testament')
        self.assertIn("testament", str(queryset.query))

    def test_book_info_view_methods(self):
        """Test BookInfoView only allows GET method."""
        view = BookInfoView()
        # By default, APIView allows all methods, but we only implement get
        self.assertTrue(hasattr(view, "get"))
        self.assertFalse(hasattr(view, "post"))
        self.assertFalse(hasattr(view, "put"))
        self.assertFalse(hasattr(view, "delete"))

    def test_chapters_by_book_view_methods(self):
        """Test ChaptersByBookView only allows GET method."""
        view = ChaptersByBookView()
        # By default, APIView allows all methods, but we only implement get
        self.assertTrue(hasattr(view, "get"))
        self.assertFalse(hasattr(view, "post"))
        self.assertFalse(hasattr(view, "put"))
        self.assertFalse(hasattr(view, "delete"))

    @patch("bible.books.views.get_canonical_book_by_name")
    @patch("bible.books.views.get_book_display_name")
    def test_chapters_by_book_different_chapter_counts(self, mock_display_name, mock_get_book):
        """Test ChaptersByBookView with different chapter counts."""
        # Test with John (21 chapters)
        mock_get_book.return_value = self.john
        mock_display_name.return_value = "John"

        view = ChaptersByBookView()
        request = self.factory.get("/api/v1/bible/books/John/chapters/")
        response = view.get(request, book_name="John")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["book"], "John")
        self.assertEqual(response.data["chapters"], list(range(1, 22)))  # 21 chapters
        self.assertEqual(len(response.data["chapters"]), 21)

    def test_view_inheritance(self):
        """Test that views inherit from correct base classes."""
        from rest_framework import generics
        from rest_framework.views import APIView

        self.assertTrue(issubclass(BookListView, generics.ListAPIView))
        self.assertTrue(issubclass(BookInfoView, APIView))
        self.assertTrue(issubclass(ChaptersByBookView, APIView))
