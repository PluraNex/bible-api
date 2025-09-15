"""
Comprehensive tests for bible.utils module.
"""
from django.http import Http404
from django.test import TestCase

from bible.models import BookName, CanonicalBook, Language, Testament
from bible.utils import get_book_abbreviation, get_book_display_name, get_canonical_book_by_name


class BibleUtilsTest(TestCase):
    """Comprehensive tests for Bible utility functions."""

    def setUp(self):
        """Set up test data."""
        # Create languages
        self.english = Language.objects.create(code="en", name="English")
        self.portuguese = Language.objects.create(code="pt", name="Portuguese")

        # Create testament
        self.new_testament = Testament.objects.create(name="New Testament")

        # Create canonical book
        self.john_canonical = CanonicalBook.objects.create(
            osis_code="John", canonical_order=43, testament=self.new_testament, chapter_count=21
        )

        # Create book names in different languages
        self.john_en = BookName.objects.create(
            canonical_book=self.john_canonical, language=self.english, name="John", abbreviation="Jn"
        )

        self.john_pt = BookName.objects.create(
            canonical_book=self.john_canonical, language=self.portuguese, name="João", abbreviation="Jo"
        )

    def test_get_canonical_book_by_name_with_english_name(self):
        """Test finding book by English name."""
        book = get_canonical_book_by_name("John")
        self.assertEqual(book, self.john_canonical)

    def test_get_canonical_book_by_name_with_portuguese_name(self):
        """Test finding book by Portuguese name."""
        book = get_canonical_book_by_name("João")
        self.assertEqual(book, self.john_canonical)

    def test_get_canonical_book_by_name_with_abbreviation(self):
        """Test finding book by abbreviation."""
        book = get_canonical_book_by_name("Jn")
        self.assertEqual(book, self.john_canonical)

        book = get_canonical_book_by_name("Jo")
        self.assertEqual(book, self.john_canonical)

    def test_get_canonical_book_by_name_with_osis_code(self):
        """Test finding book by OSIS code."""
        book = get_canonical_book_by_name("John")
        self.assertEqual(book, self.john_canonical)

    def test_get_canonical_book_by_name_case_insensitive(self):
        """Test that search is case insensitive."""
        book = get_canonical_book_by_name("JOHN")
        self.assertEqual(book, self.john_canonical)

        book = get_canonical_book_by_name("john")
        self.assertEqual(book, self.john_canonical)

        book = get_canonical_book_by_name("JN")
        self.assertEqual(book, self.john_canonical)

    def test_get_canonical_book_by_name_not_found(self):
        """Test that Http404 is raised when book is not found."""
        with self.assertRaises(Http404):
            get_canonical_book_by_name("NonexistentBook")

    def test_get_book_display_name_english(self):
        """Test getting display name in English."""
        display_name = get_book_display_name(self.john_canonical, "en")
        self.assertEqual(display_name, "John")

    def test_get_book_display_name_portuguese(self):
        """Test getting display name in Portuguese."""
        display_name = get_book_display_name(self.john_canonical, "pt")
        self.assertEqual(display_name, "João")

    def test_get_book_display_name_fallback_to_osis(self):
        """Test fallback to OSIS code when language not found."""
        display_name = get_book_display_name(self.john_canonical, "es")
        self.assertEqual(display_name, "John")  # Falls back to OSIS code

    def test_get_book_display_name_default_language(self):
        """Test default language parameter."""
        display_name = get_book_display_name(self.john_canonical)
        self.assertEqual(display_name, "John")  # Default is 'en'

    def test_get_book_abbreviation_english(self):
        """Test getting abbreviation in English."""
        abbrev = get_book_abbreviation(self.john_canonical, "en")
        self.assertEqual(abbrev, "Jn")

    def test_get_book_abbreviation_portuguese(self):
        """Test getting abbreviation in Portuguese."""
        abbrev = get_book_abbreviation(self.john_canonical, "pt")
        self.assertEqual(abbrev, "Jo")

    def test_get_book_abbreviation_fallback(self):
        """Test fallback to first 3 chars of OSIS when language not found."""
        abbrev = get_book_abbreviation(self.john_canonical, "es")
        self.assertEqual(abbrev, "Joh")  # First 3 chars of "John"

    def test_get_book_abbreviation_default_language(self):
        """Test default language parameter."""
        abbrev = get_book_abbreviation(self.john_canonical)
        self.assertEqual(abbrev, "Jn")  # Default is 'en'


class BibleUtilsEdgeCasesTest(TestCase):
    """Test edge cases and error conditions."""

    def setUp(self):
        """Set up minimal test data."""
        self.english = Language.objects.create(code="en", name="English")
        self.testament = Testament.objects.create(name="Old Testament")

        # Book with no names
        self.genesis_canonical = CanonicalBook.objects.create(
            osis_code="Gen", canonical_order=1, testament=self.testament, chapter_count=50
        )

    def test_get_book_display_name_no_names(self):
        """Test display name when no BookName objects exist."""
        display_name = get_book_display_name(self.genesis_canonical, "en")
        self.assertEqual(display_name, "Gen")

    def test_get_book_abbreviation_no_names(self):
        """Test abbreviation when no BookName objects exist."""
        abbrev = get_book_abbreviation(self.genesis_canonical, "en")
        self.assertEqual(abbrev, "Gen")

    def test_get_canonical_book_empty_string(self):
        """Test behavior with empty string."""
        with self.assertRaises(Http404):
            get_canonical_book_by_name("")

    def test_get_canonical_book_whitespace_only(self):
        """Test behavior with whitespace-only string."""
        with self.assertRaises(Http404):
            get_canonical_book_by_name("   ")


class BibleUtilsPerformanceTest(TestCase):
    """Test performance aspects of utility functions."""

    def setUp(self):
        """Set up test data with multiple books."""
        self.english = Language.objects.create(code="en", name="English")
        self.testament = Testament.objects.create(name="Old Testament")

        # Create multiple books
        self.books = []
        for i, name in enumerate(["Genesis", "Exodus", "Leviticus"]):
            canonical_book = CanonicalBook.objects.create(
                osis_code=name[:3], canonical_order=i + 1, testament=self.testament, chapter_count=50
            )
            BookName.objects.create(
                canonical_book=canonical_book, language=self.english, name=name, abbreviation=name[:3]
            )
            self.books.append(canonical_book)

    def test_query_efficiency(self):
        """Test that queries use proper select_related to avoid N+1 problems."""
        with self.assertNumQueries(1):  # Should be only 1 query due to select_related
            book = get_canonical_book_by_name("Genesis")
            self.assertEqual(book.osis_code, "Gen")

    def test_multiple_lookups_efficiency(self):
        """Test multiple lookups to ensure no query caching issues."""
        with self.assertNumQueries(3):  # Each lookup should be 1 query
            book1 = get_canonical_book_by_name("Genesis")
            book2 = get_canonical_book_by_name("Exodus")
            book3 = get_canonical_book_by_name("Leviticus")

        self.assertEqual(len({book1, book2, book3}), 3)  # All different books
