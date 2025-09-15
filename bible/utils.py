"""
Utility functions for the Bible API.
"""
from django.db.models import Q
from rest_framework import generics

from .models import BookName, CanonicalBook


def get_canonical_book_by_name(book_name: str) -> CanonicalBook:
    """
    Get a canonical book by name, abbreviation, or OSIS code.

    This utility centralizes the logic for finding books by various identifiers,
    supporting multiple languages and fallback mechanisms.

    Args:
        book_name: The book name, abbreviation, or OSIS code to search for

    Returns:
        CanonicalBook instance

    Raises:
        Http404: If no book is found
    """
    # Try to find book by name or abbreviation in any language through BookName model
    book_name_obj = (
        BookName.objects.filter(Q(name__iexact=book_name) | Q(abbreviation__iexact=book_name))
        .select_related("canonical_book")
        .first()
    )

    if book_name_obj:
        return book_name_obj.canonical_book

    # Fallback: try by osis_code directly
    return generics.get_object_or_404(CanonicalBook.objects.all(), osis_code__iexact=book_name)


def get_book_display_name(canonical_book: CanonicalBook, language_code: str = "en") -> str:
    """
    Get the display name for a canonical book in the specified language.

    Args:
        canonical_book: The CanonicalBook instance
        language_code: The language code (default: 'en')

    Returns:
        Display name for the book
    """
    book_name = canonical_book.names.filter(language__code=language_code, version__isnull=True).first()

    return book_name.name if book_name else canonical_book.osis_code


def get_book_abbreviation(canonical_book: CanonicalBook, language_code: str = "en") -> str:
    """
    Get the abbreviation for a canonical book in the specified language.

    Args:
        canonical_book: The CanonicalBook instance
        language_code: The language code (default: 'en')

    Returns:
        Abbreviation for the book
    """
    book_name = canonical_book.names.filter(language__code=language_code, version__isnull=True).first()

    return book_name.abbreviation if book_name else canonical_book.osis_code[:3]
