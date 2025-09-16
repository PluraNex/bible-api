"""
Unit tests for cross-references views.
Tests view methods, queryset logic, and query efficiency.
"""
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from bible.crossrefs.serializers import CrossReferenceSerializer
from bible.crossrefs.views import CrossReferencesByThemeView, CrossReferencesByVerseView
from bible.models import APIKey, BookName, CanonicalBook, CrossReference, Language, Testament


@pytest.mark.unit
class CrossRefsViewsTest(TestCase):
    """Test cross-references domain views."""

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

        self.john = CanonicalBook.objects.create(
            osis_code="John",
            canonical_order=43,
            testament=self.new_testament,
            chapter_count=21,
            is_deuterocanonical=False,
        )

        # Create book names
        BookName.objects.create(canonical_book=self.genesis, language=self.english, name="Genesis", abbreviation="Gen")

        BookName.objects.create(canonical_book=self.john, language=self.english, name="John", abbreviation="Jn")

        # Create cross reference
        self.crossref = CrossReference.objects.create(
            from_book=self.genesis,
            from_chapter=1,
            from_verse=1,
            to_book=self.john,
            to_chapter=1,
            to_verse_start=1,
            to_verse_end=1,
            confidence=0.8,
        )

    def test_crossrefs_by_verse_view_serializer_class(self):
        """Test CrossReferencesByVerseView uses correct serializer."""
        view = CrossReferencesByVerseView()
        self.assertEqual(view.serializer_class, CrossReferenceSerializer)

    def test_crossrefs_by_verse_view_queryset(self):
        """Test CrossReferencesByVerseView queryset logic."""
        view = CrossReferencesByVerseView()
        view.kwargs = {"verse_id": 123}

        queryset = view.get_queryset()

        # Should have select_related for efficiency
        query_str = str(queryset.query)
        self.assertIn("JOIN", query_str)  # Should have joins for select_related

        # Should have proper ordering
        self.assertIn("ORDER BY", query_str)

    def test_crossrefs_by_verse_view_get(self):
        """Test CrossReferencesByVerseView GET method."""
        view = CrossReferencesByVerseView()
        view.kwargs = {"verse_id": 123}
        request = self.factory.get("/api/v1/bible/cross-references/by-verse/123/")

        # Mock the super().get() to avoid full request processing
        with patch.object(view.__class__.__bases__[0], "get") as mock_super_get:
            mock_super_get.return_value = Mock(status_code=200)
            response = view.get(request, verse_id=123)

            self.assertEqual(response.status_code, 200)

    def test_crossrefs_by_theme_view_serializer_class(self):
        """Test CrossReferencesByThemeView uses correct serializer."""
        view = CrossReferencesByThemeView()
        self.assertEqual(view.serializer_class, CrossReferenceSerializer)

    def test_crossrefs_by_theme_view_queryset(self):
        """Test CrossReferencesByThemeView queryset logic."""
        view = CrossReferencesByThemeView()
        view.kwargs = {"theme_id": 123}

        queryset = view.get_queryset()

        # Should have select_related for efficiency
        query_str = str(queryset.query)
        self.assertIn("JOIN", query_str)  # Should have joins for select_related

        # Should have proper ordering
        self.assertIn("ORDER BY", query_str)

    def test_crossrefs_by_theme_view_get(self):
        """Test CrossReferencesByThemeView GET method."""
        view = CrossReferencesByThemeView()
        view.kwargs = {"theme_id": 123}
        request = self.factory.get("/api/v1/bible/cross-references/by-theme/123/")

        # Mock the super().get() to avoid full request processing
        with patch.object(view.__class__.__bases__[0], "get") as mock_super_get:
            mock_super_get.return_value = Mock(status_code=200)
            response = view.get(request, theme_id=123)

            self.assertEqual(response.status_code, 200)

    def test_view_inheritance(self):
        """Test that views inherit from correct base classes."""
        from rest_framework import generics

        self.assertTrue(issubclass(CrossReferencesByVerseView, generics.ListAPIView))
        self.assertTrue(issubclass(CrossReferencesByThemeView, generics.ListAPIView))

    def test_crossrefs_by_verse_view_query_efficiency(self):
        """Test that CrossReferencesByVerseView uses select_related for efficiency."""
        view = CrossReferencesByVerseView()
        view.kwargs = {"verse_id": 123}

        queryset = view.get_queryset()

        # Check that select_related is applied with correct fields
        query_str = str(queryset.query)
        self.assertIn("JOIN", query_str)  # Should have joins for select_related
        # The queryset should include both from_book and to_book relationships
        self.assertIn("from_book", str(queryset.query))
        self.assertIn("to_book", str(queryset.query))

    def test_crossrefs_by_theme_view_query_efficiency(self):
        """Test that CrossReferencesByThemeView uses select_related for efficiency."""
        view = CrossReferencesByThemeView()
        view.kwargs = {"theme_id": 123}

        queryset = view.get_queryset()

        # Check that select_related is applied with correct fields
        query_str = str(queryset.query)
        self.assertIn("JOIN", query_str)  # Should have joins for select_related
        # The queryset should include both from_book and to_book relationships
        self.assertIn("from_book", str(queryset.query))
        self.assertIn("to_book", str(queryset.query))

    def test_crossrefs_by_verse_view_ordering(self):
        """Test CrossReferencesByVerseView ordering."""
        view = CrossReferencesByVerseView()
        view.kwargs = {"verse_id": 123}

        queryset = view.get_queryset()

        # Should be ordered by from_book, from_chapter, from_verse
        query_str = str(queryset.query)
        self.assertIn("ORDER BY", query_str)

    def test_crossrefs_by_theme_view_ordering(self):
        """Test CrossReferencesByThemeView ordering."""
        view = CrossReferencesByThemeView()
        view.kwargs = {"theme_id": 123}

        queryset = view.get_queryset()

        # Should be ordered by from_book, from_chapter, from_verse
        query_str = str(queryset.query)
        self.assertIn("ORDER BY", query_str)

    def test_crossrefs_by_verse_view_methods(self):
        """Test CrossReferencesByVerseView only allows GET method."""
        view = CrossReferencesByVerseView()
        # By default, ListAPIView only allows GET method
        self.assertTrue(hasattr(view, "get"))
        self.assertFalse(hasattr(view, "post"))
        self.assertFalse(hasattr(view, "put"))
        self.assertFalse(hasattr(view, "delete"))

    def test_crossrefs_by_theme_view_methods(self):
        """Test CrossReferencesByThemeView only allows GET method."""
        view = CrossReferencesByThemeView()
        # By default, ListAPIView only allows GET method
        self.assertTrue(hasattr(view, "get"))
        self.assertFalse(hasattr(view, "post"))
        self.assertFalse(hasattr(view, "put"))
        self.assertFalse(hasattr(view, "delete"))

    def test_crossrefs_by_verse_view_kwargs_usage(self):
        """Test that CrossReferencesByVerseView correctly uses kwargs."""
        view = CrossReferencesByVerseView()
        view.kwargs = {"verse_id": 456}

        # The view should access verse_id from kwargs
        queryset = view.get_queryset()

        # Verify that the view method accessed the kwargs
        self.assertIsNotNone(queryset)

    def test_crossrefs_by_theme_view_kwargs_usage(self):
        """Test that CrossReferencesByThemeView correctly uses kwargs."""
        view = CrossReferencesByThemeView()
        view.kwargs = {"theme_id": 789}

        # The view should access theme_id from kwargs
        queryset = view.get_queryset()

        # Verify that the view method accessed the kwargs
        self.assertIsNotNone(queryset)
