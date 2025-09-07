"""
Tests for Verse and Version models.
"""
from django.db import IntegrityError
from django.test import TestCase

from bible.models import Book, Verse, Version


class VersionModelTest(TestCase):
    """Tests for Version model."""

    def test_version_creation(self):
        """Test basic version creation."""
        version = Version.objects.create(
            name="King James Version", abbreviation="KJV", language="en", description="Classic English translation"
        )
        self.assertEqual(str(version), "King James Version (KJV)")
        self.assertEqual(version.language, "en")
        self.assertTrue(version.is_active)

    def test_version_unique_abbreviation(self):
        """Test that abbreviation is unique."""
        Version.objects.create(name="King James Version", abbreviation="KJV", language="en")

        with self.assertRaises(IntegrityError):
            Version.objects.create(name="Another Version", abbreviation="KJV", language="en")  # Duplicate abbreviation


class VerseModelTest(TestCase):
    """Tests for Verse model."""

    def setUp(self):
        self.book = Book.objects.create(name="John", abbreviation="Joh", order=43, testament="NEW", chapter_count=21)
        self.version = Version.objects.create(name="King James Version", abbreviation="KJV", language="en")

    def test_verse_creation(self):
        """Test basic verse creation."""
        verse = Verse.objects.create(
            book=self.book, version=self.version, chapter=3, number=16, text="For God so loved the world..."
        )
        self.assertEqual(str(verse), "Joh 3:16 (KJV)")
        self.assertEqual(verse.reference, "John 3:16")

    def test_verse_unique_constraint(self):
        """Test that book+version+chapter+number combination is unique."""
        Verse.objects.create(
            book=self.book, version=self.version, chapter=3, number=16, text="For God so loved the world..."
        )

        with self.assertRaises(IntegrityError):
            Verse.objects.create(
                book=self.book,
                version=self.version,
                chapter=3,
                number=16,  # Duplicate combination
                text="Different text",
            )

    def test_verse_ordering(self):
        """Test that verses are ordered correctly."""
        verse2 = Verse.objects.create(book=self.book, version=self.version, chapter=3, number=17, text="Text 2")
        verse1 = Verse.objects.create(book=self.book, version=self.version, chapter=3, number=16, text="Text 1")

        verses = list(Verse.objects.all())
        self.assertEqual(verses[0], verse1)
        self.assertEqual(verses[1], verse2)
