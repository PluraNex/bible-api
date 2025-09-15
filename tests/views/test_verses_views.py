"""
Unit tests for verses views.
Tests view methods, queryset logic, filtering, and error handling.
"""
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from bible.models import APIKey, BookName, CanonicalBook, Language, Testament, Verse, Version
from bible.verses.serializers import VerseSerializer
from bible.verses.views import VerseDetailView, VersesByChapterView, VersesByThemeView


@pytest.mark.unit
class VersesViewsTest(TestCase):
    """Test verses domain views."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="test_user")

        # Create API key
        self.api_key = APIKey.objects.create(name="Test Key", user=self.user, scopes=["read"])

        # Create languages, testaments, and version
        self.english = Language.objects.create(code="en", name="English")
        self.old_testament = Testament.objects.create(name="Old Testament")
        self.version = Version.objects.create(code="NIV", name="New International Version", language=self.english)

        # Create canonical book
        self.genesis = CanonicalBook.objects.create(
            osis_code="Gen",
            canonical_order=1,
            testament=self.old_testament,
            chapter_count=50,
            is_deuterocanonical=False,
        )

        # Create book name
        BookName.objects.create(canonical_book=self.genesis, language=self.english, name="Genesis", abbreviation="Gen")

        # Create verses
        self.verse1 = Verse.objects.create(
            book=self.genesis,
            chapter=1,
            number=1,
            text="In the beginning God created the heavens and the earth.",
            version=self.version,
        )

        self.verse2 = Verse.objects.create(
            book=self.genesis, chapter=1, number=2, text="Now the earth was formless and empty...", version=self.version
        )

    def test_verses_by_chapter_view_queryset_success(self):
        """Test VersesByChapterView queryset with valid book and chapter."""
        view = VersesByChapterView()
        view.kwargs = {"book_name": "Genesis", "chapter": 1}

        with patch("bible.verses.views.get_canonical_book_by_name") as mock_get_book:
            mock_get_book.return_value = self.genesis
            queryset = view.get_queryset()

            # Should return verses for Genesis chapter 1
            verses = list(queryset)
            self.assertEqual(len(verses), 2)
            self.assertEqual(verses[0].number, 1)
            self.assertEqual(verses[1].number, 2)

    def test_verses_by_chapter_view_queryset_invalid_book(self):
        """Test VersesByChapterView queryset with invalid book."""
        view = VersesByChapterView()
        view.kwargs = {"book_name": "InvalidBook", "chapter": 1}

        with patch("bible.verses.views.get_canonical_book_by_name") as mock_get_book:
            mock_get_book.side_effect = Exception("Book not found")
            queryset = view.get_queryset()

            # Should return empty queryset
            self.assertEqual(queryset.count(), 0)

    def test_verses_by_chapter_view_serializer_class(self):
        """Test VersesByChapterView uses correct serializer."""
        view = VersesByChapterView()
        self.assertEqual(view.serializer_class, VerseSerializer)

    def test_verses_by_chapter_view_filter_backends(self):
        """Test VersesByChapterView has correct filter backends."""
        view = VersesByChapterView()
        from django_filters.rest_framework import DjangoFilterBackend
        from rest_framework import filters

        expected_backends = [DjangoFilterBackend, filters.SearchFilter]
        self.assertEqual(view.filter_backends, expected_backends)

    def test_verses_by_chapter_view_filterset_fields(self):
        """Test VersesByChapterView filterset fields."""
        view = VersesByChapterView()
        expected_fields = ["version"]
        self.assertEqual(view.filterset_fields, expected_fields)

    def test_verses_by_chapter_view_search_fields(self):
        """Test VersesByChapterView search fields."""
        view = VersesByChapterView()
        expected_fields = ["text"]
        self.assertEqual(view.search_fields, expected_fields)

    @patch("bible.verses.views.get_canonical_book_by_name")
    def test_verses_by_chapter_view_get_success(self, mock_get_book):
        """Test VersesByChapterView GET with valid parameters."""
        mock_get_book.return_value = self.genesis

        view = VersesByChapterView()
        view.kwargs = {"book_name": "Genesis", "chapter": 1}
        request = self.factory.get("/api/v1/bible/verses/Genesis/1/")

        # Mock the super().get() to avoid full request processing
        with patch.object(view.__class__.__bases__[0], "get") as mock_super_get:
            mock_super_get.return_value = Mock(status_code=200)
            response = view.get(request, book_name="Genesis", chapter=1)

            self.assertEqual(response.status_code, 200)

    @patch("bible.verses.views.get_canonical_book_by_name")
    def test_verses_by_chapter_view_get_book_not_found(self, mock_get_book):
        """Test VersesByChapterView GET with invalid book returns 404."""
        mock_get_book.side_effect = Exception("Book not found")

        view = VersesByChapterView()
        view.kwargs = {"book_name": "InvalidBook", "chapter": 1}
        request = self.factory.get("/api/v1/bible/verses/InvalidBook/1/")

        response = view.get(request, book_name="InvalidBook", chapter=1)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"detail": "Book not found"})

    def test_verse_detail_view_queryset(self):
        """Test VerseDetailView queryset."""
        view = VerseDetailView()
        queryset = view.get_queryset()

        # Should return all verses
        self.assertEqual(queryset.model, Verse)

    def test_verse_detail_view_serializer_class(self):
        """Test VerseDetailView uses correct serializer."""
        view = VerseDetailView()
        self.assertEqual(view.serializer_class, VerseSerializer)

    def test_verse_detail_view_lookup_field(self):
        """Test VerseDetailView lookup field."""
        view = VerseDetailView()
        self.assertEqual(view.lookup_field, "pk")

    def test_verse_detail_view_get(self):
        """Test VerseDetailView GET method."""
        view = VerseDetailView()
        request = self.factory.get(f"/api/v1/bible/verses/{self.verse1.id}/")

        # Mock the super().get() to avoid full request processing
        with patch.object(view.__class__.__bases__[0], "get") as mock_super_get:
            mock_super_get.return_value = Mock(status_code=200)
            response = view.get(request, pk=self.verse1.id)

            self.assertEqual(response.status_code, 200)

    def test_verses_by_theme_view_queryset(self):
        """Test VersesByThemeView queryset logic."""
        view = VersesByThemeView()
        view.kwargs = {"theme_id": 123}

        queryset = view.get_queryset()

        # Should have proper ordering/select_related (theme_links may not exist yet)
        self.assertIn("ORDER BY", str(queryset.query))

    def test_verses_by_theme_view_serializer_class(self):
        """Test VersesByThemeView uses correct serializer."""
        view = VersesByThemeView()
        self.assertEqual(view.serializer_class, VerseSerializer)

    def test_verses_by_theme_view_filter_backends(self):
        """Test VersesByThemeView has correct filter backends."""
        view = VersesByThemeView()
        from django_filters.rest_framework import DjangoFilterBackend
        from rest_framework import filters

        expected_backends = [DjangoFilterBackend, filters.SearchFilter]
        self.assertEqual(view.filter_backends, expected_backends)

    def test_verses_by_theme_view_filterset_fields(self):
        """Test VersesByThemeView filterset fields."""
        view = VersesByThemeView()
        expected_fields = ["version", "book"]
        self.assertEqual(view.filterset_fields, expected_fields)

    def test_verses_by_theme_view_search_fields(self):
        """Test VersesByThemeView search fields."""
        view = VersesByThemeView()
        expected_fields = ["text"]
        self.assertEqual(view.search_fields, expected_fields)

    def test_verses_by_theme_view_get(self):
        """Test VersesByThemeView GET method."""
        view = VersesByThemeView()
        view.kwargs = {"theme_id": 123}
        request = self.factory.get("/api/v1/bible/verses/by-theme/123/")

        # Mock the super().get() to avoid full request processing
        with patch.object(view.__class__.__bases__[0], "get") as mock_super_get:
            mock_super_get.return_value = Mock(status_code=200)
            response = view.get(request, theme_id=123)

            self.assertEqual(response.status_code, 200)

    def test_view_inheritance(self):
        """Test that views inherit from correct base classes."""
        from rest_framework import generics

        self.assertTrue(issubclass(VersesByChapterView, generics.ListAPIView))
        self.assertTrue(issubclass(VerseDetailView, generics.RetrieveAPIView))
        self.assertTrue(issubclass(VersesByThemeView, generics.ListAPIView))

    def test_verses_by_chapter_view_query_efficiency(self):
        """Test that VersesByChapterView uses select_related for efficiency."""
        view = VersesByChapterView()
        view.kwargs = {"book_name": "Genesis", "chapter": 1}

        with patch("bible.verses.views.get_canonical_book_by_name") as mock_get_book:
            mock_get_book.return_value = self.genesis
            queryset = view.get_queryset()

            # Check that select_related is applied
            query_str = str(queryset.query)
            self.assertIn("JOIN", query_str)  # Should have joins for select_related

    def test_verses_by_theme_view_query_efficiency(self):
        """Test that VersesByThemeView uses select_related for efficiency."""
        view = VersesByThemeView()
        view.kwargs = {"theme_id": 123}

        queryset = view.get_queryset()

        # Check that select_related is applied
        query_str = str(queryset.query)
        self.assertIn("JOIN", query_str)  # Should have joins for select_related

    def test_verses_by_chapter_view_ordering(self):
        """Test that VersesByChapterView orders by number."""
        view = VersesByChapterView()
        view.kwargs = {"book_name": "Genesis", "chapter": 1}

        with patch("bible.verses.views.get_canonical_book_by_name") as mock_get_book:
            mock_get_book.return_value = self.genesis
            queryset = view.get_queryset()

            # Should be ordered by number
            query_str = str(queryset.query)
            self.assertIn("ORDER BY", query_str)

    def test_verses_by_theme_view_ordering(self):
        """Test that VersesByThemeView has correct ordering."""
        view = VersesByThemeView()
        view.kwargs = {"theme_id": 123}

        queryset = view.get_queryset()

        # Should be ordered by book canonical_order, chapter, number
        query_str = str(queryset.query)
        self.assertIn("ORDER BY", query_str)
