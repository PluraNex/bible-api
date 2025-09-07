"""
Tests for Theme model.
"""
from django.db import IntegrityError
from django.test import TestCase

from bible.models import Theme


class ThemeModelTest(TestCase):
    """Tests for Theme model."""

    def test_theme_creation(self):
        theme = Theme.objects.create(name="Creation", description="Theme about creation", color="#00FF00", icon="seed")
        self.assertEqual(str(theme), "Creation")
        self.assertEqual(theme.color, "#00FF00")
        self.assertEqual(theme.icon, "seed")

    def test_theme_unique_name(self):
        Theme.objects.create(name="Love")
        with self.assertRaises(IntegrityError):
            Theme.objects.create(name="Love")

