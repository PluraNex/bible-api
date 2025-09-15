"""
Unit tests for themes views.
Tests view methods, queryset logic, and inheritance.
"""
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from bible.models import APIKey, Theme
from bible.themes.serializers import ThemeSerializer
from bible.themes.views import ThemeDetailView, ThemeListView


@pytest.mark.unit
class ThemesViewsTest(TestCase):
    """Test themes domain views."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="test_user")

        # Create API key
        self.api_key = APIKey.objects.create(name="Test Key", user=self.user, scopes=["read"])

        # Create themes
        self.theme1 = Theme.objects.create(name="Love", description="Biblical concept of divine and human love")

        self.theme2 = Theme.objects.create(name="Faith", description="Trust and belief in God")

    def test_theme_list_view_queryset(self):
        """Test ThemeListView queryset."""
        view = ThemeListView()
        queryset = view.get_queryset()

        # Should return all themes
        self.assertEqual(queryset.model, Theme)
        themes = list(queryset)
        self.assertEqual(len(themes), 2)

    def test_theme_list_view_serializer_class(self):
        """Test ThemeListView uses correct serializer."""
        view = ThemeListView()
        self.assertEqual(view.serializer_class, ThemeSerializer)

    def test_theme_list_view_get(self):
        """Test ThemeListView GET method."""
        view = ThemeListView()
        request = self.factory.get("/api/v1/bible/themes/")

        # Mock the super().get() to avoid full request processing
        with patch.object(view.__class__.__bases__[0], "get") as mock_super_get:
            mock_super_get.return_value = Mock(status_code=200)
            response = view.get(request)

            self.assertEqual(response.status_code, 200)

    def test_theme_detail_view_queryset(self):
        """Test ThemeDetailView queryset."""
        view = ThemeDetailView()
        queryset = view.get_queryset()

        # Should return all themes
        self.assertEqual(queryset.model, Theme)

    def test_theme_detail_view_serializer_class(self):
        """Test ThemeDetailView uses correct serializer."""
        view = ThemeDetailView()
        self.assertEqual(view.serializer_class, ThemeSerializer)

    def test_theme_detail_view_lookup_field(self):
        """Test ThemeDetailView lookup field."""
        view = ThemeDetailView()
        self.assertEqual(view.lookup_field, "pk")

    def test_theme_detail_view_get(self):
        """Test ThemeDetailView GET method."""
        view = ThemeDetailView()
        request = self.factory.get(f"/api/v1/bible/themes/{self.theme1.id}/")

        # Mock the super().get() to avoid full request processing
        with patch.object(view.__class__.__bases__[0], "get") as mock_super_get:
            mock_super_get.return_value = Mock(status_code=200)
            response = view.get(request, pk=self.theme1.id)

            self.assertEqual(response.status_code, 200)

    def test_view_inheritance(self):
        """Test that views inherit from correct base classes."""
        from rest_framework import generics

        self.assertTrue(issubclass(ThemeListView, generics.ListAPIView))
        self.assertTrue(issubclass(ThemeDetailView, generics.RetrieveAPIView))

    def test_theme_list_view_methods(self):
        """Test ThemeListView only allows GET method."""
        view = ThemeListView()
        # By default, ListAPIView only allows GET method
        self.assertTrue(hasattr(view, "get"))
        self.assertFalse(hasattr(view, "post"))
        self.assertFalse(hasattr(view, "put"))
        self.assertFalse(hasattr(view, "delete"))

    def test_theme_detail_view_methods(self):
        """Test ThemeDetailView only allows GET method."""
        view = ThemeDetailView()
        # By default, RetrieveAPIView only allows GET method
        self.assertTrue(hasattr(view, "get"))
        self.assertFalse(hasattr(view, "post"))
        self.assertFalse(hasattr(view, "put"))
        self.assertFalse(hasattr(view, "delete"))

    def test_theme_list_view_queryset_efficiency(self):
        """Test ThemeListView queryset is efficient."""
        view = ThemeListView()
        queryset = view.get_queryset()

        # Should use the base queryset efficiently
        self.assertEqual(str(queryset.query).count("SELECT"), 1)

    def test_theme_detail_view_queryset_efficiency(self):
        """Test ThemeDetailView queryset is efficient."""
        view = ThemeDetailView()
        queryset = view.get_queryset()

        # Should use the base queryset efficiently
        self.assertEqual(str(queryset.query).count("SELECT"), 1)

    def test_theme_list_view_queryset_all_themes(self):
        """Test ThemeListView returns all themes."""
        view = ThemeListView()
        queryset = view.get_queryset()

        themes = list(queryset.all())
        theme_names = [theme.name for theme in themes]

        self.assertIn("Love", theme_names)
        self.assertIn("Faith", theme_names)

    def test_theme_detail_view_lookup_functionality(self):
        """Test ThemeDetailView lookup works with pk."""
        view = ThemeDetailView()

        # The lookup_field is 'pk' by default
        self.assertEqual(view.lookup_field, "pk")

        # Should be able to find themes by pk
        queryset = view.get_queryset()
        theme = queryset.filter(pk=self.theme1.id).first()
        self.assertEqual(theme.name, "Love")
