"""
Final test for bible.utils module to ensure complete coverage.
"""
from django.test import TestCase
from rest_framework.exceptions import NotFound

from bible.models import BookName, CanonicalBook, Language, Testament


class BibleUtilsFinalTest(TestCase):
    """Final comprehensive test for bible utils."""

    def setUp(self):
        """Set up test data."""
        # Create test language
        self.language = Language.objects.create(code="en-final", name="English Final")

        # Create testament
        self.testament = Testament.objects.create(name="Final Testament")

        # Create canonical book
        self.book = CanonicalBook.objects.create(
            osis_code="FinalGen",
            canonical_order=9999,
            testament=self.testament,
            chapter_count=50
        )

        # Create book name
        self.book_name = BookName.objects.create(
            canonical_book=self.book,
            language=self.language,
            name="Final Genesis",
            abbreviation="FGen",
            version=None  # Explicitly set to None
        )

    def test_get_canonical_book_by_name_direct(self):
        """Test getting book by name - direct execution."""
        # Import function directly to ensure it's executed
        from bible.utils import get_canonical_book_by_name

        # Test with exact name
        result = get_canonical_book_by_name("Final Genesis")
        self.assertEqual(result.osis_code, "FinalGen")

        # Test with abbreviation
        result = get_canonical_book_by_name("FGen")
        self.assertEqual(result.osis_code, "FinalGen")

        # Test with OSIS code
        result = get_canonical_book_by_name("FinalGen")
        self.assertEqual(result.osis_code, "FinalGen")

    def test_get_canonical_book_by_name_not_found_direct(self):
        """Test getting non-existent book."""
        from bible.utils import get_canonical_book_by_name

        from django.http import Http404
        with self.assertRaises(Http404):
            get_canonical_book_by_name("NonExistentFinalBook")

    def test_get_book_display_name_direct(self):
        """Test getting book display name."""
        from bible.utils import get_book_display_name

        # Test with existing language
        result = get_book_display_name(self.book, "en-final")
        self.assertEqual(result, "Final Genesis")

        # Test with non-existent language (should fallback to OSIS)
        result = get_book_display_name(self.book, "non-existent")
        self.assertEqual(result, "FinalGen")

        # Test with default language
        result = get_book_display_name(self.book)
        self.assertEqual(result, "FinalGen")  # No 'en' language, so fallback

    def test_get_book_abbreviation_direct(self):
        """Test getting book abbreviation."""
        from bible.utils import get_book_abbreviation

        # Test with existing language
        result = get_book_abbreviation(self.book, "en-final")
        self.assertEqual(result, "FGen")

        # Test with non-existent language (should fallback to OSIS[:3])
        result = get_book_abbreviation(self.book, "non-existent")
        self.assertEqual(result, "Fin")  # First 3 chars of "FinalGen"

        # Test with default language
        result = get_book_abbreviation(self.book)
        self.assertEqual(result, "Fin")  # No 'en' language, so fallback