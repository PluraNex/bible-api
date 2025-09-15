"""
Tests for Verse and Version models.
"""
from django.db import IntegrityError
from django.test import TestCase

from bible.models import BookName, CanonicalBook, Language, Testament, Verse, Version


class VersionModelTest(TestCase):
    """Tests for Version model."""

    def setUp(self):
        """Set up test data."""
        self.language = Language.objects.create(code="en-US", name="English (United States)")

    def test_version_creation(self):
        """Test basic version creation."""
        version = Version.objects.create(
            name="King James Version", code="EN_KJV", language=self.language, description="Classic English translation"
        )
        self.assertEqual(str(version), "King James Version (EN_KJV)")
        self.assertEqual(version.abbreviation, "KJV")
        self.assertTrue(version.is_active)

    def test_version_unique_code_per_language(self):
        """Test that code is unique per language."""
        Version.objects.create(name="King James Version", code="EN_KJV", language=self.language)

        with self.assertRaises(IntegrityError):
            Version.objects.create(
                name="Another Version", code="EN_KJV", language=self.language  # Duplicate code for same language
            )


class VerseModelTest(TestCase):
    """Tests for Verse model."""

    def setUp(self):
        """Set up test data."""
        # Create language
        self.language = Language.objects.create(code="en-US", name="English (United States)")

        # Create testament
        self.testament = Testament.objects.create(id=2, name="Novo Testamento")

        # Create canonical book
        self.book = CanonicalBook.objects.create(
            osis_code="John", canonical_order=43, testament=self.testament, chapter_count=21
        )

        # Create book name
        BookName.objects.create(canonical_book=self.book, language=self.language, name="John", abbreviation="Joh")

        # Create version
        self.version = Version.objects.create(name="King James Version", code="EN_KJV", language=self.language)

    def test_verse_creation(self):
        """Test basic verse creation."""
        verse = Verse.objects.create(
            book=self.book, version=self.version, chapter=3, number=16, text="For God so loved the world..."
        )
        self.assertEqual(str(verse), "John 3:16 (KJV)")
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
