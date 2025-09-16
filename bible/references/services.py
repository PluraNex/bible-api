"""Services for reference parsing and resolution (T-006)."""
from __future__ import annotations

import re
import unicodedata

from django.core.cache import cache

from bible.models import BookName, CanonicalBook, Language

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]")


def _normalize_key(text: str) -> str:
    """Normalize text for alias lookups: strip accents, lower, remove non-alnum.

    Example: "1 Co." -> "1co"; "Cânticos" -> "canticos".
    """
    if not text:
        return ""
    # Normalize accents
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower().strip()
    # Remove non alphanumeric
    norm = _NON_ALNUM_RE.sub("", norm)
    return norm


def _cache_key(lang: str) -> str:
    return f"ref_aliases:{lang or 'en'}:v1"


def _get_language(lang_code: str) -> Language | None:
    try:
        return Language.objects.get(code=lang_code)
    except Language.DoesNotExist:
        return None


def _build_alias_map(lang_code: str) -> dict[str, CanonicalBook]:
    """Build mapping of aliases -> CanonicalBook for a given language.

    Includes: BookName.name, BookName.abbreviation (where version IS NULL) and CanonicalBook.osis_code.
    """
    mapping: dict[str, CanonicalBook] = {}

    # Prefer exact language; if not found, fall back to base language (pt-BR -> pt)
    lang = _get_language(lang_code)
    langs = []
    if lang:
        langs.append(lang)
    if "-" in (lang_code or ""):
        base = lang_code.split("-")[0]
        base_lang = _get_language(base)
        if base_lang and base_lang not in langs:
            langs.append(base_lang)
    # Always include English as a final fallback
    en = _get_language("en")
    if en and en not in langs:
        langs.append(en)

    # Add aliases from BookName (version is NULL for generic names)
    for lang in langs:
        for bn in (
            BookName.objects.filter(language=lang, version__isnull=True)
            .select_related("canonical_book")
            .only("name", "abbreviation", "canonical_book__id", "canonical_book__osis_code")
        ):
            book = bn.canonical_book
            if bn.name:
                mapping.setdefault(_normalize_key(bn.name), book)
            if bn.abbreviation:
                mapping.setdefault(_normalize_key(bn.abbreviation), book)

    # Add OSIS codes for all books
    for book in CanonicalBook.objects.all().only("id", "osis_code"):
        mapping.setdefault(_normalize_key(book.osis_code), book)

    return mapping


def get_alias_map(lang_code: str) -> dict[str, CanonicalBook]:
    """Get alias -> CanonicalBook map for language, cached in memory and Redis."""
    cache_key = _cache_key(lang_code)
    data = cache.get(cache_key)
    if data is not None:
        return data

    # Build and cache
    mapping = _build_alias_map(lang_code)
    cache.set(cache_key, mapping, timeout=60 * 30)  # 30 minutes
    return mapping


def resolve_book_by_alias(book_raw: str, lang_code: str) -> CanonicalBook | None:
    """Resolve a raw book string to CanonicalBook using alias map for language."""
    aliases = get_alias_map(lang_code)
    key = _normalize_key(book_raw)
    return aliases.get(key)
