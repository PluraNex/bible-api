"""
Tests for Theme serializers.
"""
from django.test import TestCase

from bible.models import Theme
from bible.themes.serializers import ThemeSerializer


class ThemeSerializerTest(TestCase):
    """Tests for ThemeSerializer."""

    def setUp(self):
        """Set up test data."""
        self.theme = Theme.objects.create(name="Faith")

    def test_serialization(self):
        """Test theme serialization includes all expected fields."""
        serializer = ThemeSerializer(instance=self.theme)
        data = serializer.data

        self.assertEqual(data["name"], "Faith")
        self.assertIn("id", data)

    def test_str_representation(self):
        """Test theme string representation."""
        self.assertEqual(str(self.theme), "Faith")

    def test_theme_ordering(self):
        """Test themes are ordered by name."""
        Theme.objects.create(name="Hope")
        Theme.objects.create(name="Grace")

        themes = list(Theme.objects.all())
        self.assertEqual(themes[0].name, "Faith")
        self.assertEqual(themes[1].name, "Grace")
        self.assertEqual(themes[2].name, "Hope")
