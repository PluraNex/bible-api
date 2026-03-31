"""Centralized version resolution and selection service.

Consolidates version lookup logic previously duplicated across:
- bible.verses.views._pick_default_version_for_lang()
- bible.verses.views.VersesByChapterView.get_queryset() (nested pick_default_version)
- bible.versions.views.VersionDefaultView._get_default_version_for_language()
"""

from __future__ import annotations

from ..models import Version


def get_default_version_for_lang(lang_code: str) -> Version | None:
    """Get default active version for a language with fallback strategy.

    Fallback chain:
    1. Exact language match (e.g., "pt-BR" -> "pt-BR")
    2. Base -> regional (e.g., "pt" -> "pt-BR")
    3. Regional -> base (e.g., "pt-BR" -> "pt")
    4. English fallback (e.g., "xy" -> "en")

    When multiple versions exist for the same language, returns the first
    version ordered alphabetically by name (ascending) for predictable results.
    """
    # Exact language
    version = Version.objects.filter(language__code=lang_code, is_active=True).order_by("name").first()
    if version:
        return version

    # Base -> regional (e.g., "pt" tries "pt-BR")
    if "-" not in lang_code:
        regional = (
            Version.objects.filter(language__code__startswith=f"{lang_code}-", is_active=True)
            .order_by("name")
            .first()
        )
        if regional:
            return regional

    # Regional -> base (e.g., "pt-BR" tries "pt")
    if "-" in lang_code:
        base_lang = lang_code.split("-")[0]
        base_version = Version.objects.filter(language__code=base_lang, is_active=True).order_by("name").first()
        if base_version:
            return base_version

    # English fallback
    if lang_code != "en":
        en_version = Version.objects.filter(language__code="en", is_active=True).order_by("name").first()
        if en_version:
            return en_version

    return None


def get_version_by_ref(version_ref: str) -> Version | None:
    """Resolve a version by ID, exact code, or code suffix.

    Tries in order:
    1. Parse as integer ID
    2. Exact code match (case-insensitive)
    3. Code suffix match (e.g., "KJV" matches "EN_KJV")

    Returns None if no version is found.
    """
    try:
        version_id = int(version_ref)
        return Version.objects.filter(pk=version_id).first()
    except (ValueError, TypeError):
        return (
            Version.objects.filter(code__iexact=version_ref).first()
            or Version.objects.filter(code__iendswith=f"_{version_ref}").first()
        )
