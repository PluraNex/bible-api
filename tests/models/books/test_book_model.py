"""
Tests for Book models (CanonicalBook, BookName, etc).
"""
from django.db import IntegrityError
from django.test import TransactionTestCase
from django.test.utils import override_settings

from bible.models import BookName, CanonicalBook, Language, Testament


@override_settings(USE_TZ=True)
class BookModelTest(TransactionTestCase):
    """Tests for CanonicalBook and BookName models."""

    def setUp(self):
        """Set up test data."""
        # Create test testament (use different ID to avoid conflicts)
        self.testament, _ = Testament.objects.get_or_create(id=99, defaults={"name": "Test Testament"})
        # Create test language (use different code to avoid conflicts)
        self.language, _ = Language.objects.get_or_create(code="test-lang", defaults={"name": "Test Language"})

    def test_book_creation(self):
        """Test basic canonical book creation with all required fields."""
        book = CanonicalBook.objects.create(
            osis_code="TestGen", canonical_order=999, testament=self.testament, chapter_count=50
        )

        # Create book name in test language
        book_name = BookName.objects.create(
            canonical_book=book, language=self.language, name="Test Gênesis", abbreviation="TGn"
        )

        self.assertEqual(str(book), "TestGen")
        self.assertEqual(book.canonical_order, 999)
        self.assertEqual(book.chapter_count, 50)
        self.assertEqual(str(book_name), "Test Gênesis [test-lang]")

    def test_book_unique_constraints(self):
        """Test that osis_code and canonical_order are unique."""
        CanonicalBook.objects.create(
            osis_code="TestGen1", canonical_order=998, testament=self.testament, chapter_count=50
        )

        # Test unique osis_code
        with self.assertRaises(IntegrityError):
            CanonicalBook.objects.create(
                osis_code="TestGen1",  # Duplicate osis_code
                canonical_order=997,
                testament=self.testament,
                chapter_count=50,
            )

        # Test unique canonical_order
        with self.assertRaises(IntegrityError):
            CanonicalBook.objects.create(
                osis_code="TestGen2",
                canonical_order=998,  # Duplicate canonical_order
                testament=self.testament,
                chapter_count=40,
            )

    def test_book_ordering(self):
        """Test that books are ordered by canonical_order field."""
        book2 = CanonicalBook.objects.create(
            osis_code="TestExod", canonical_order=996, testament=self.testament, chapter_count=40
        )
        book1 = CanonicalBook.objects.create(
            osis_code="TestGen3", canonical_order=995, testament=self.testament, chapter_count=50
        )

        # Filter to only test books to avoid interference from seeded data
        books = list(CanonicalBook.objects.filter(osis_code__startswith="Test").order_by("canonical_order"))
        # Verify ordering: book1 should come before book2
        self.assertEqual(books[-2], book1)  # book1 should come before book2
        self.assertEqual(books[-1], book2)
