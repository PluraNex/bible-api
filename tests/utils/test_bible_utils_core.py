"""Tests for bible.utils core functions."""
import pytest
from django.http import Http404
from django.test import TestCase

from bible.models import CanonicalBook, BookName, Language, Testament
from bible.utils import get_canonical_book_by_name, get_book_display_name, get_book_abbreviation


class BibleUtilsTest(TestCase):
    """Test bible.utils functions."""

    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        # Create languages
        cls.english = Language.objects.create(code="en", name="English")
        cls.portuguese = Language.objects.create(code="pt", name="Portuguese")

        # Create testament
        cls.testament = Testament.objects.create(name="New Testament")

        # Create canonical book
        cls.genesis = CanonicalBook.objects.create(
            osis_code="Gen",
            canonical_order=1,
            testament=cls.testament,
            chapter_count=50
        )

        # Create book names
        cls.genesis_en = BookName.objects.create(
            canonical_book=cls.genesis,
            language=cls.english,
            name="Genesis",
            abbreviation="Gen"
        )

        cls.genesis_pt = BookName.objects.create(
            canonical_book=cls.genesis,
            language=cls.portuguese,
            name="Gênesis",
            abbreviation="Gên"
        )

    def test_get_canonical_book_by_name_exact_match(self):
        """Test finding book by exact name."""
        book = get_canonical_book_by_name("Genesis")
        self.assertEqual(book, self.genesis)

    def test_get_canonical_book_by_name_case_insensitive(self):
        """Test finding book by case-insensitive name."""
        book = get_canonical_book_by_name("GENESIS")
        self.assertEqual(book, self.genesis)

        book = get_canonical_book_by_name("genesis")
        self.assertEqual(book, self.genesis)

    def test_get_canonical_book_by_abbreviation(self):
        """Test finding book by abbreviation."""
        book = get_canonical_book_by_name("Gen")
        self.assertEqual(book, self.genesis)

    def test_get_canonical_book_by_abbreviation_case_insensitive(self):
        """Test finding book by case-insensitive abbreviation."""
        book = get_canonical_book_by_name("GEN")
        self.assertEqual(book, self.genesis)

    def test_get_canonical_book_by_osis_code(self):
        """Test finding book by OSIS code fallback."""
        # Create a book without BookName entries
        matthew = CanonicalBook.objects.create(
            osis_code="Matt",
            canonical_order=2,
            testament=self.testament,
            chapter_count=28
        )

        book = get_canonical_book_by_name("Matt")
        self.assertEqual(book, matthew)

    def test_get_canonical_book_by_name_not_found(self):
        """Test 404 when book not found."""
        with self.assertRaises(Http404):
            get_canonical_book_by_name("NonexistentBook")

    def test_get_canonical_book_by_portuguese_name(self):
        """Test finding book by Portuguese name."""
        book = get_canonical_book_by_name("Gênesis")
        self.assertEqual(book, self.genesis)

    def test_get_book_display_name_english(self):
        """Test getting display name in English."""
        name = get_book_display_name(self.genesis, "en")
        self.assertEqual(name, "Genesis")

    def test_get_book_display_name_portuguese(self):
        """Test getting display name in Portuguese."""
        name = get_book_display_name(self.genesis, "pt")
        self.assertEqual(name, "Gênesis")

    def test_get_book_display_name_fallback_to_osis(self):
        """Test fallback to OSIS code when no name found."""
        name = get_book_display_name(self.genesis, "fr")  # French not available
        self.assertEqual(name, "Gen")

    def test_get_book_display_name_default_english(self):
        """Test default to English when no language specified."""
        name = get_book_display_name(self.genesis)
        self.assertEqual(name, "Genesis")

    def test_get_book_abbreviation_english(self):
        """Test getting abbreviation in English."""
        abbr = get_book_abbreviation(self.genesis, "en")
        self.assertEqual(abbr, "Gen")

    def test_get_book_abbreviation_portuguese(self):
        """Test getting abbreviation in Portuguese."""
        abbr = get_book_abbreviation(self.genesis, "pt")
        self.assertEqual(abbr, "Gên")

    def test_get_book_abbreviation_fallback_to_osis(self):
        """Test fallback to first 3 chars of OSIS code when no abbr found."""
        abbr = get_book_abbreviation(self.genesis, "fr")  # French not available
        self.assertEqual(abbr, "Gen")

    def test_get_book_abbreviation_default_english(self):
        """Test default to English when no language specified."""
        abbr = get_book_abbreviation(self.genesis)
        self.assertEqual(abbr, "Gen")