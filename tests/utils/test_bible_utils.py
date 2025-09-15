"""
Tests for bible.utils module.
"""
from django.test import TestCase

from bible.models import BookName, CanonicalBook, Language, Testament
from bible.utils import get_book_abbreviation, get_book_display_name, get_canonical_book_by_name


class BibleUtilsTest(TestCase):
    def setUp(self):
        self.language = Language.objects.create(code="en-test", name="English Test")
        self.testament = Testament.objects.create(id=95, name="Test Testament")

        self.book = CanonicalBook.objects.create(
            osis_code="TestGen", canonical_order=1, testament=self.testament, chapter_count=50
        )

        BookName.objects.create(canonical_book=self.book, language=self.language, name="Genesis", abbreviation="Gen")

    def test_get_canonical_book_by_name_exact_match(self):
        """Test getting book by exact name match."""
        book = get_canonical_book_by_name("Genesis")
        self.assertEqual(book, self.book)

    def test_get_canonical_book_by_abbreviation(self):
        """Test getting book by abbreviation."""
        book = get_canonical_book_by_name("Gen")
        self.assertEqual(book, self.book)

    def test_get_canonical_book_by_osis_code(self):
        """Test getting book by OSIS code."""
        book = get_canonical_book_by_name("TestGen")
        self.assertEqual(book, self.book)

    def test_get_canonical_book_case_insensitive(self):
        """Test getting book with case insensitive search."""
        book = get_canonical_book_by_name("genesis")
        self.assertEqual(book, self.book)

        book = get_canonical_book_by_name("GEN")
        self.assertEqual(book, self.book)

    def test_get_canonical_book_not_found(self):
        """Test getting non-existent book raises 404."""
        from django.http import Http404

        with self.assertRaises(Http404):
            get_canonical_book_by_name("NonExistentBook")

    def test_get_book_display_name(self):
        """Test getting display name for a book."""
        name = get_book_display_name(self.book, "en-test")
        self.assertEqual(name, "Genesis")

    def test_get_book_display_name_fallback(self):
        """Test getting display name with fallback to OSIS code."""
        # Create a book without any names
        book2 = CanonicalBook.objects.create(
            osis_code="TestEzr", canonical_order=2, testament=self.testament, chapter_count=10
        )
        name = get_book_display_name(book2, "en-test")
        self.assertEqual(name, "TestEzr")

    def test_get_book_abbreviation(self):
        """Test getting abbreviation for a book."""
        abbr = get_book_abbreviation(self.book, "en-test")
        self.assertEqual(abbr, "Gen")

    def test_get_book_abbreviation_fallback(self):
        """Test getting abbreviation with fallback to OSIS code."""
        # Create a book without any names
        book2 = CanonicalBook.objects.create(
            osis_code="TestEzra", canonical_order=2, testament=self.testament, chapter_count=10
        )
        abbr = get_book_abbreviation(book2, "en-test")
        self.assertEqual(abbr, "Tes")  # First 3 chars of OSIS code
