"""
Tests for Book model.
"""
from django.db import IntegrityError
from django.test import TestCase

from bible.models import Book


class BookModelTest(TestCase):
    """Tests for Book model."""

    def test_book_creation(self):
        """Test basic book creation with all required fields."""
        book = Book.objects.create(name="Genesis", abbreviation="Gen", order=1, testament="OLD", chapter_count=50)
        self.assertEqual(str(book), "Genesis (Gen)")
        self.assertEqual(book.order, 1)
        self.assertEqual(book.testament, "OLD")
        self.assertEqual(book.chapter_count, 50)

    def test_book_unique_constraints(self):
        """Test that name, abbreviation, and order are unique."""
        Book.objects.create(name="Genesis", abbreviation="Gen", order=1, testament="OLD", chapter_count=50)

        # Test unique name
        with self.assertRaises(IntegrityError):
            Book.objects.create(name="Genesis", abbreviation="GEN2", order=2, testament="OLD", chapter_count=50)

    def test_book_ordering(self):
        """Test that books are ordered by order field."""
        book2 = Book.objects.create(name="Exodus", abbreviation="Exo", order=2, testament="OLD", chapter_count=40)
        book1 = Book.objects.create(name="Genesis", abbreviation="Gen", order=1, testament="OLD", chapter_count=50)

        books = list(Book.objects.all())
        self.assertEqual(books[0], book1)
        self.assertEqual(books[1], book2)
