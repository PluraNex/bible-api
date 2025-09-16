"""
Tests for Version serializers.
"""
from django.test import TestCase

from bible.models import Language, Version
from bible.versions.serializers import VersionSerializer


class VersionSerializerTest(TestCase):
    """Tests for VersionSerializer."""

    def setUp(self):
        """Set up test data."""
        self.language = Language.objects.create(code="en-US", name="English (United States)")
        self.version = Version.objects.create(
            name="King James Version",
            code="EN_KJV",
            language=self.language,
            description="Classic English translation",
            is_active=True,
        )

    def test_serialization(self):
        """Test version serialization includes all expected fields."""
        serializer = VersionSerializer(instance=self.version)
        data = serializer.data

        self.assertEqual(data["name"], "King James Version")
        self.assertEqual(data["code"], "EN_KJV")
        self.assertEqual(data["abbreviation"], "KJV")  # Property field
        self.assertEqual(data["language"], "en-US")
        self.assertEqual(data["description"], "Classic English translation")
        self.assertTrue(data["is_active"])

    def test_abbreviation_property(self):
        """Test abbreviation property extracts correctly from code."""
        # Test with underscore separator
        version1 = Version.objects.create(name="Nova Versão Internacional", code="PT_BR_NVI", language=self.language)
        serializer1 = VersionSerializer(instance=version1)
        self.assertEqual(serializer1.data["abbreviation"], "NVI")

        # Test without underscore
        version2 = Version.objects.create(name="Simple Code", code="SIMPLE", language=self.language)
        serializer2 = VersionSerializer(instance=version2)
        self.assertEqual(serializer2.data["abbreviation"], "SIMPLE")
