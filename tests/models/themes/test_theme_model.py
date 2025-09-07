"""
Tests for Theme model.
"""
from django.db import IntegrityError
from django.test import TestCase

from bible.models import Theme


class ThemeModelTest(TestCase):
    """Tests for Theme model."""

    def test_theme_creation(self):
        theme = Theme.objects.create(name="Creation", description="Theme about creation")
        self.assertEqual(str(theme), "Creation")

    def test_theme_unique_name(self):
        Theme.objects.create(name="Love")
        with self.assertRaises(IntegrityError):
            Theme.objects.create(name="Love")
