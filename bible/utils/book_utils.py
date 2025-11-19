"""
Book-related utility functions.
"""

from django.db.models import Q
from django.http import Http404

from ..models import CanonicalBook


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
    from ..models import BookName

    # First try exact OSIS code match
    book = CanonicalBook.objects.filter(osis_code__iexact=book_name).first()
    if book:
        return book

    # Try finding by book names/abbreviations
    book_name_obj = (
        BookName.objects.filter(Q(name__iexact=book_name) | Q(abbreviation__iexact=book_name))
        .select_related("canonical_book")
        .first()
    )

    if book_name_obj:
        return book_name_obj.canonical_book

    raise Http404(f"Book '{book_name}' not found")


def get_book_display_name(canonical_book: CanonicalBook, language_code: str = "en") -> str:
    """
    Get the display name for a canonical book in the specified language.

    Implements fallback logic: pt-BR → pt → en, es-ES → es → en, etc.

    Args:
        canonical_book: The CanonicalBook instance
        language_code: The language code (default: 'en')

    Returns:
        Display name for the book
    """
    if not language_code:
        language_code = "en"

    lang_code = language_code.strip()

    # Try exact match first
    book_name = canonical_book.names.filter(language__code__iexact=lang_code, version__isnull=True).first()
    if book_name:
        return book_name.name

    # Fallback: try base language (pt-BR → pt, es-ES → es, en-US → en)
    lang_lower = lang_code.lower()
    if "-" in lang_code:
        base_lang = lang_code.split("-")[0]
        book_name = canonical_book.names.filter(language__code__iexact=base_lang, version__isnull=True).first()
        if book_name:
            return book_name.name

    # Final fallback: try English
    if lang_lower != "en":
        book_name = canonical_book.names.filter(language__code__iexact="en", version__isnull=True).first()
        if book_name:
            return book_name.name

    # Ultimate fallback: OSIS code
    return canonical_book.osis_code


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
