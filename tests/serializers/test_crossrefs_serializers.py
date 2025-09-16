"""
Tests for CrossReference serializers.
"""
from django.test import TestCase

from bible.crossrefs.serializers import CrossReferenceSerializer
from bible.models import CanonicalBook, CrossReference, Language, Testament


class CrossReferenceSerializerTest(TestCase):
    """Tests for CrossReferenceSerializer."""

    def setUp(self):
        """Set up test data."""
        # Create test language and testament
        self.language = Language.objects.create(code="test-xr", name="Test CrossRef Lang")
        self.testament = Testament.objects.create(id=95, name="Test XRef Testament")

        # Create canonical books
        self.from_book = CanonicalBook.objects.create(
            osis_code="TestGen", canonical_order=991, testament=self.testament, chapter_count=50
        )

        self.to_book = CanonicalBook.objects.create(
            osis_code="TestExod", canonical_order=992, testament=self.testament, chapter_count=40
        )

        # Create cross-reference
        self.crossref = CrossReference.objects.create(
            from_book=self.from_book,
            from_chapter=1,
            from_verse=1,
            to_book=self.to_book,
            to_chapter=2,
            to_verse_start=3,
            to_verse_end=5,
            source="test-source",
            confidence=0.8,
            explanation="Test cross-reference explanation",
        )

    def test_serialization(self):
        """Test cross-reference serialization includes all expected fields."""
        serializer = CrossReferenceSerializer(instance=self.crossref)
        data = serializer.data

        self.assertEqual(data["from_chapter"], 1)
        self.assertEqual(data["from_verse"], 1)
        self.assertEqual(data["to_chapter"], 2)
        self.assertEqual(data["to_verse_start"], 3)
        self.assertEqual(data["to_verse_end"], 5)
        self.assertEqual(data["source"], "test-source")
        self.assertEqual(data["confidence"], 0.8)
        self.assertEqual(data["explanation"], "Test cross-reference explanation")

    def test_str_representation(self):
        """Test cross-reference string representation."""
        expected = "TestGen 1:1 → TestExod 2:3-5"
        self.assertEqual(str(self.crossref), expected)

    def test_str_representation_single_verse(self):
        """Test cross-reference string representation for single verse."""
        single_crossref = CrossReference.objects.create(
            from_book=self.from_book,
            from_chapter=1,
            from_verse=2,
            to_book=self.to_book,
            to_chapter=3,
            to_verse_start=4,
            to_verse_end=4,  # Same start and end
            source="single-test",
        )
        expected = "TestGen 1:2 → TestExod 3:4"
        self.assertEqual(str(single_crossref), expected)
