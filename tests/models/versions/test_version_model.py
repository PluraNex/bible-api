"""
Tests for Version model.
"""
from django.test import TestCase

from bible.models import Language, License, Version


class VersionModelTest(TestCase):
    """Test Version model."""

    def setUp(self):
        """Set up test data."""
        self.language = Language.objects.create(code="en", name="English")
        self.license = License.objects.create(name="Public Domain", code="PD")

    def test_version_creation(self):
        """Test creating a Version instance."""
        version = Version.objects.create(
            language=self.language,
            code="EN_KJV",
            name="King James Version",
            versification="KJV",
            copyright="Public Domain",
            license=self.license,
            is_active=True
        )

        self.assertEqual(version.language, self.language)
        self.assertEqual(version.code, "EN_KJV")
        self.assertEqual(version.name, "King James Version")
        self.assertEqual(version.versification, "KJV")
        self.assertEqual(version.copyright, "Public Domain")
        self.assertEqual(version.license, self.license)
        self.assertTrue(version.is_active)

    def test_version_str_representation(self):
        """Test string representation of Version."""
        version = Version.objects.create(
            language=self.language,
            code="EN_KJV",
            name="King James Version"
        )

        expected = "King James Version (EN_KJV)"
        self.assertEqual(str(version), expected)

    def test_abbreviation_property_with_underscore(self):
        """Test abbreviation property with underscore in code."""
        version = Version.objects.create(
            language=self.language,
            code="PT_BR_NVI",
            name="Nova Versão Internacional"
        )

        self.assertEqual(version.abbreviation, "NVI")

    def test_abbreviation_property_without_underscore(self):
        """Test abbreviation property without underscore in code."""
        version = Version.objects.create(
            language=self.language,
            code="SIMPLE",
            name="Simple Version"
        )

        self.assertEqual(version.abbreviation, "SIMPLE")

    def test_version_defaults(self):
        """Test default values for Version fields."""
        version = Version.objects.create(
            language=self.language,
            name="Test Version"
        )

        self.assertEqual(version.code, "EN_UNKNOWN")
        self.assertEqual(version.versification, "KJV")
        self.assertEqual(version.copyright, "")
        self.assertEqual(version.permissions, "")
        self.assertEqual(version.source_url, "")
        self.assertEqual(version.description, "")
        self.assertTrue(version.is_active)
        self.assertIsNone(version.license)

    def test_version_meta_ordering(self):
        """Test Version model ordering."""
        self.assertEqual(Version._meta.ordering, ["language_id", "code"])

    def test_version_meta_db_table(self):
        """Test Version model database table name."""
        self.assertEqual(Version._meta.db_table, "versions")

    def test_version_with_nullable_language(self):
        """Test Version creation with null language."""
        version = Version.objects.create(
            name="Test Version",
            code="TEST"
        )

        self.assertIsNone(version.language)
        self.assertEqual(version.name, "Test Version")
        self.assertEqual(version.code, "TEST")

    def test_version_license_relationship(self):
        """Test Version license foreign key relationship."""
        version = Version.objects.create(
            language=self.language,
            name="Licensed Version",
            license=self.license
        )

        self.assertEqual(version.license, self.license)

        # Test related name
        related_versions = self.license.versions.all()
        self.assertIn(version, related_versions)