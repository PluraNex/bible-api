"""
Direct tests for bible.utils module to ensure coverage.
"""
from django.test import TestCase
from django.http import Http404

from bible.models import BookName, CanonicalBook, Language, Testament


class BibleUtilsDirectTest(TestCase):
    """Direct tests for bible utils functions."""

    def setUp(self):
        """Set up test data."""
        # Create test language
        self.language = Language.objects.create(code="en-direct", name="English Direct")

        # Create testament
        self.testament = Testament.objects.create(name="Test Testament Direct")

        # Create canonical book
        self.book = CanonicalBook.objects.create(
            osis_code="DirectGen",
            canonical_order=999,
            testament=self.testament,
            chapter_count=50
        )

        # Create book name
        BookName.objects.create(
            canonical_book=self.book,
            language=self.language,
            name="Direct Genesis",
            abbreviation="DGen"
        )

    def test_get_canonical_book_by_name_function(self):
        """Test getting book by name - direct import test."""
        from bible.utils import get_canonical_book_by_name

        book = get_canonical_book_by_name("Direct Genesis")
        self.assertEqual(book.osis_code, "DirectGen")

    def test_get_book_display_name_function(self):
        """Test getting book display name - direct import test."""
        from bible.utils import get_book_display_name

        name = get_book_display_name(self.book, "en-direct")
        self.assertEqual(name, "Direct Genesis")

    def test_get_book_abbreviation_function(self):
        """Test getting book abbreviation - direct import test."""
        from bible.utils import get_book_abbreviation

        abbr = get_book_abbreviation(self.book, "en-direct")
        self.assertEqual(abbr, "DGen")

    def test_get_canonical_book_by_name_not_found(self):
        """Test getting non-existent book raises 404."""
        from bible.utils import get_canonical_book_by_name

        with self.assertRaises(Http404):
            get_canonical_book_by_name("NonExistentBookDirect")

    def test_get_book_display_name_fallback(self):
        """Test display name fallback to OSIS code."""
        from bible.utils import get_book_display_name

        # Test with non-existent language
        name = get_book_display_name(self.book, "non-existent")
        self.assertEqual(name, "DirectGen")  # Should fallback to osis_code

    def test_get_book_abbreviation_fallback(self):
        """Test abbreviation fallback to OSIS code."""
        from bible.utils import get_book_abbreviation

        # Test with non-existent language
        abbr = get_book_abbreviation(self.book, "non-existent")
        self.assertEqual(abbr, "Dir")  # Should be first 3 chars of osis_code