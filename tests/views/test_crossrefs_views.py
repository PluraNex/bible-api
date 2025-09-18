"""
Unit tests for cross-references views.
Tests view methods, queryset logic, and query efficiency.
"""
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from bible.crossrefs.serializers import CrossReferenceSerializer
from bible.crossrefs.views import (
    CrossReferenceFiltersMixin,
    CrossReferencePagination,
    CrossReferencesByThemeView,
    CrossReferencesByVerseDeprecatedView,
    CrossReferencesByVerseView,
    CrossReferencesGroupedView,
    CrossReferencesParallelsView,
    ReferenceResolutionMixin,
)
from bible.models import APIKey, BookName, CanonicalBook, CrossReference, Language, Testament, Theme, Verse, Version


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

        # Create version
        self.version = Version.objects.create(
            code="KJV",
            name="King James Version",
            language=self.english,
        )

        # Create theme
        self.theme = Theme.objects.create(name="Test Theme", description="A test theme for cross-reference testing")

        # Create verses
        self.verse_gen = Verse.objects.create(
            book=self.genesis,
            version=self.version,
            chapter=1,
            number=1,
            text="In the beginning God created the heaven and the earth.",
        )

        self.verse_john = Verse.objects.create(
            book=self.john,
            version=self.version,
            chapter=3,
            number=16,
            text="For God so loved the world...",
        )

        # Add theme to verse
        self.verse_gen.themes.add(self.theme)

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
            source="TSK",
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

    def test_crossrefs_by_verse_view_vary_header(self):
        """Ensure cache varies by Accept-Language header."""
        cache.clear()
        view = CrossReferencesByVerseView()
        django_request = self.api_factory.get(
            "/api/v1/bible/cross-references/for/?ref=Gen 1:1",
            HTTP_ACCEPT_LANGUAGE="pt",
        )
        request = Request(django_request)
        request.lang_code = "pt"
        view.request = request
        view.format_kwarg = None

        response = view.get(request)

        vary_header = response.get("Vary", "")
        self.assertIn("Accept-Language", vary_header)

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

    # New tests for better coverage
    def test_pagination_limit_validation(self):
        """Test CrossReferencePagination limit validation."""
        pagination = CrossReferencePagination()

        # Test invalid limit
        request = self.api_factory.get("/?limit=invalid")
        with self.assertRaises(ValidationError):
            pagination.get_page_size(Request(request))

        # Test zero limit
        request = self.api_factory.get("/?limit=0")
        with self.assertRaises(ValidationError):
            pagination.get_page_size(Request(request))

        # Test valid limit
        request = self.api_factory.get("/?limit=50")
        page_size = pagination.get_page_size(Request(request))
        self.assertEqual(page_size, 50)

    def test_filter_mixin_source_filter(self):
        """Test CrossReferenceFiltersMixin source filtering."""
        mixin = CrossReferenceFiltersMixin()
        request = self.api_factory.get("/?source=TSK")
        mixin.request = Request(request)

        queryset = CrossReference.objects.all()
        filtered = mixin._apply_common_filters(queryset)

        self.assertEqual(
            filtered.count(),
            queryset.filter(source__iexact="TSK").count(),
        )
        self.assertEqual(set(filtered.values_list("source", flat=True)), {"TSK"})
        self.assertEqual(mixin.applied_filters["source"], "TSK")

    def test_filter_mixin_min_confidence_validation(self):
        """Test CrossReferenceFiltersMixin min_confidence validation."""
        mixin = CrossReferenceFiltersMixin()

        # Test invalid confidence
        request = self.api_factory.get("/?min_confidence=invalid")
        mixin.request = Request(request)

        queryset = CrossReference.objects.all()
        with self.assertRaises(ValidationError):
            mixin._apply_common_filters(queryset)

        # Test out of range confidence
        request = self.api_factory.get("/?min_confidence=1.5")
        mixin.request = Request(request)

        with self.assertRaises(ValidationError):
            mixin._apply_common_filters(queryset)

    def test_reference_resolution_mixin_missing_ref(self):
        """Test ReferenceResolutionMixin missing ref parameter."""
        mixin = ReferenceResolutionMixin()
        request = self.api_factory.get("/")
        mixin.request = Request(request)

        with self.assertRaises(ValidationError):
            mixin._resolve_reference()

    def test_reference_resolution_mixin_invalid_book(self):
        """Test ReferenceResolutionMixin with invalid book."""
        mixin = ReferenceResolutionMixin()
        request = self.api_factory.get("/?ref=INVALIDBOOK 1:1")
        mixin.request = Request(request)

        with self.assertRaises(ValidationError):
            mixin._resolve_reference()

    def test_reference_resolution_mixin_invalid_chapter_verse(self):
        """Test ReferenceResolutionMixin with invalid chapter/verse."""
        mixin = ReferenceResolutionMixin()
        request = self.api_factory.get("/?ref=Gen abc:def")
        mixin.request = Request(request)

        with self.assertRaises(ValidationError):
            mixin._resolve_reference()

    def test_crossrefs_by_verse_view_not_found(self):
        """Test CrossReferencesByVerseView when no references found."""
        view = CrossReferencesByVerseView()
        django_request = self.api_factory.get("/api/v1/bible/cross-references/for/?ref=Gen 2:1")
        request = Request(django_request)
        view.request = request

        with self.assertRaises(NotFound):
            view.list(request)

    def test_crossrefs_by_verse_view_build_summary(self):
        """Test CrossReferencesByVerseView _build_summary method."""
        view = CrossReferencesByVerseView()
        django_request = self.api_factory.get("/api/v1/bible/cross-references/for/?ref=Gen 1:1&limit=10")
        request = Request(django_request)
        view.request = request
        view._input_ref = "Gen 1:1"

        queryset = CrossReference.objects.filter(from_book=self.genesis)
        summary = view._build_summary(queryset, 1, 1)

        self.assertEqual(summary["input"], "Gen 1:1")
        self.assertEqual(summary["available"], 1)
        self.assertEqual(summary["total"], 1)
        self.assertIn("filters", summary)
        self.assertIn("sources", summary)
        self.assertIn("confidence", summary)

    def test_parallels_view_not_found(self):
        """Test CrossReferencesParallelsView when no parallels found."""
        view = CrossReferencesParallelsView()
        django_request = self.api_factory.get("/api/v1/bible/cross-references/parallels/?ref=Gen 1:1")
        request = Request(django_request)
        view.request = request
        view.format_kwarg = None

        response = view.get(request)
        self.assertEqual(response.status_code, 404)

    def test_grouped_view_basic(self):
        """Test CrossReferencesGroupedView basic functionality."""
        view = CrossReferencesGroupedView()
        django_request = self.api_factory.get("/api/v1/bible/cross-references/grouped/?ref=Gen 1:1")
        request = Request(django_request)
        view.request = request
        view.format_kwarg = None

        response = view.get(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("groups", response.data)
        self.assertIn("total", response.data)

    def test_deprecated_view_with_verse_id(self):
        """Test CrossReferencesByVerseDeprecatedView with verse ID."""
        view = CrossReferencesByVerseDeprecatedView()
        view.kwargs = {"verse_id": self.verse_gen.id}
        django_request = self.api_factory.get(f"/api/v1/bible/cross-references/verse/{self.verse_gen.id}/")
        request = Request(django_request)
        view.request = request
        view.format_kwarg = None

        response = view.get(request)

        # Check deprecation headers
        self.assertEqual(response["Deprecation"], "true")
        self.assertEqual(response["Sunset"], "2025-03-31")
        self.assertIn("successor-version", response["Link"])

    def test_deprecated_view_invalid_verse_id(self):
        """Test CrossReferencesByVerseDeprecatedView with invalid verse ID."""
        view = CrossReferencesByVerseDeprecatedView()
        view.kwargs = {"verse_id": 99999}

        queryset = view.get_queryset()
        self.assertFalse(queryset.exists())

    def test_by_theme_view_theme_not_found(self):
        """Test CrossReferencesByThemeView with non-existent theme."""
        view = CrossReferencesByThemeView()
        view.kwargs = {"theme_id": 99999}
        django_request = self.api_factory.get("/api/v1/bible/cross-references/by-theme/99999/")
        request = Request(django_request)
        view.request = request

        with self.assertRaises(NotFound):
            view.get_queryset()
