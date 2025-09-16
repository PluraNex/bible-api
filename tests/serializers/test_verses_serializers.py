"""
Tests for Verse serializers.
"""
from django.test import TestCase

from bible.models import BookName, CanonicalBook, Language, Testament, Verse, Version
from bible.verses.serializers import VerseSerializer


class VerseSerializerTest(TestCase):
    """Tests for VerseSerializer."""

    def setUp(self):
        """Set up test data."""
        # Create language
        self.language = Language.objects.create(code="en-US", name="English (United States)")

        # Create testament
        self.testament = Testament.objects.create(id=96, name="Test Testament")

        # Create canonical book
        self.book = CanonicalBook.objects.create(
            osis_code="TestJohn", canonical_order=943, testament=self.testament, chapter_count=21
        )

        # Create book name
        BookName.objects.create(canonical_book=self.book, language=self.language, name="Test John", abbreviation="TJoh")

        # Create version
        self.version = Version.objects.create(name="Test King James Version", code="TEST_KJV", language=self.language)

        # Create verse
        self.verse = Verse.objects.create(
            book=self.book, version=self.version, chapter=3, number=16, text="For God so loved the world..."
        )

    def test_serialization(self):
        """Test verse serialization includes all expected fields."""
        serializer = VerseSerializer(instance=self.verse)
        data = serializer.data

        self.assertEqual(data["chapter"], 3)
        self.assertEqual(data["number"], 16)
        self.assertEqual(data["text"], "For God so loved the world...")
        self.assertEqual(data["reference"], "Test John 3:16")  # Property field

    def test_reference_property(self):
        """Test reference property generates correct human-readable reference."""
        self.assertEqual(self.verse.reference, "Test John 3:16")

    def test_str_representation(self):
        """Test verse string representation."""
        expected = "TestJohn 3:16 (KJV)"
        self.assertEqual(str(self.verse), expected)
