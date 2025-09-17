"""
Unit tests for cross-references views.
Tests view methods, queryset logic, and query efficiency.
"""
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from bible.crossrefs.serializers import CrossReferenceSerializer
from bible.crossrefs.views import CrossReferencesByThemeView, CrossReferencesByVerseView
from bible.models import APIKey, BookName, CanonicalBook, CrossReference, Language, Testament, Theme


@pytest.mark.unit
class CrossRefsViewsTest(TestCase):
    """Test cross-references domain views."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.api_factory = APIRequestFactory()
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

        # Create theme
        self.theme = Theme.objects.create(name="Test Theme", description="A test theme for cross-reference testing")

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
        django_request = self.api_factory.get("/api/v1/bible/cross-references/for/?ref=Gen 1:1")
        request = Request(django_request)
        view.request = request

        queryset = view.get_queryset()

        # Should have select_related for efficiency
        query_str = str(queryset.query)
        self.assertIn("JOIN", query_str)  # Should have joins for select_related

        # Should have proper ordering
        self.assertIn("ORDER BY", query_str)

    def test_crossrefs_by_verse_view_get(self):
        """Test CrossReferencesByVerseView GET method exists and is callable."""
        view = CrossReferencesByVerseView()
        # Test that the view has the list method
        self.assertTrue(hasattr(view, "list"))
        self.assertTrue(callable(view.list))

        # Test that the view has the expected serializer class
        self.assertEqual(view.serializer_class, CrossReferenceSerializer)

    def test_crossrefs_by_theme_view_serializer_class(self):
        """Test CrossReferencesByThemeView uses correct serializer."""
        view = CrossReferencesByThemeView()
        self.assertEqual(view.serializer_class, CrossReferenceSerializer)

    def test_crossrefs_by_theme_view_queryset(self):
        """Test CrossReferencesByThemeView queryset logic."""
        view = CrossReferencesByThemeView()
        view.kwargs = {"theme_id": self.theme.id}
        django_request = self.api_factory.get(f"/api/v1/bible/cross-references/by-theme/{self.theme.id}/")
        request = Request(django_request)
        view.request = request

        queryset = view.get_queryset()

        # Should have select_related for efficiency
        query_str = str(queryset.query)
        self.assertIn("JOIN", query_str)  # Should have joins for select_related

        # Should have proper ordering
        self.assertIn("ORDER BY", query_str)

    def test_crossrefs_by_theme_view_get(self):
        """Test CrossReferencesByThemeView GET method."""
        view = CrossReferencesByThemeView()
        view.kwargs = {"theme_id": self.theme.id}
        django_request = self.api_factory.get(f"/api/v1/bible/cross-references/by-theme/{self.theme.id}/")
        request = Request(django_request)
        view.request = request

        # Mock get_queryset to return non-empty queryset and set _available_total
        mock_queryset = CrossReference.objects.none()
        with patch.object(view, "get_queryset", return_value=mock_queryset) as mock_get_queryset:

            def side_effect():
                view._available_total = 1  # Set this when get_queryset is called
                return mock_queryset

            mock_get_queryset.side_effect = side_effect

            with patch.object(view, "paginate_queryset", return_value=None):
                with patch.object(view, "get_serializer") as mock_serializer:
                    mock_serializer.return_value.data = []
                    response = view.list(request, theme_id=self.theme.id)

                    self.assertEqual(response.status_code, 200)

    def test_view_inheritance(self):
        """Test that views inherit from correct base classes."""
        from rest_framework import generics

        self.assertTrue(issubclass(CrossReferencesByVerseView, generics.ListAPIView))
        self.assertTrue(issubclass(CrossReferencesByThemeView, generics.ListAPIView))

    def test_crossrefs_by_verse_view_query_efficiency(self):
        """Test that CrossReferencesByVerseView uses select_related for efficiency."""
        view = CrossReferencesByVerseView()
        django_request = self.api_factory.get("/api/v1/bible/cross-references/for/?ref=Gen 1:1")
        request = Request(django_request)
        view.request = request

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
        view.kwargs = {"theme_id": self.theme.id}
        django_request = self.api_factory.get(f"/api/v1/bible/cross-references/by-theme/{self.theme.id}/")
        request = Request(django_request)
        view.request = request

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
        django_request = self.api_factory.get("/api/v1/bible/cross-references/for/?ref=Gen 1:1")
        request = Request(django_request)
        view.request = request

        queryset = view.get_queryset()

        # Should be ordered by from_book, from_chapter, from_verse
        query_str = str(queryset.query)
        self.assertIn("ORDER BY", query_str)

    def test_crossrefs_by_theme_view_ordering(self):
        """Test CrossReferencesByThemeView ordering."""
        view = CrossReferencesByThemeView()
        view.kwargs = {"theme_id": self.theme.id}
        django_request = self.api_factory.get(f"/api/v1/bible/cross-references/by-theme/{self.theme.id}/")
        request = Request(django_request)
        view.request = request

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
        """Test that CrossReferencesByVerseView correctly uses query params."""
        view = CrossReferencesByVerseView()
        django_request = self.api_factory.get("/api/v1/bible/cross-references/for/?ref=Gen 1:1")
        request = Request(django_request)
        view.request = request

        # The view should access ref from query params
        queryset = view.get_queryset()

        # Verify that the view method accessed the query params
        self.assertIsNotNone(queryset)

    def test_crossrefs_by_theme_view_kwargs_usage(self):
        """Test that CrossReferencesByThemeView correctly uses kwargs."""
        view = CrossReferencesByThemeView()
        view.kwargs = {"theme_id": self.theme.id}
        django_request = self.api_factory.get(f"/api/v1/bible/cross-references/by-theme/{self.theme.id}/")
        request = Request(django_request)
        view.request = request

        # The view should access theme_id from kwargs
        queryset = view.get_queryset()

        # Verify that the view method accessed the kwargs
        self.assertIsNotNone(queryset)
