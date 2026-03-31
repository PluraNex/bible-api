"""
Import curated theme-verse catalog from hybrid search experiments.

Source: bible-hybrid-search/experiments/verse_linking_final/catalog.json
Destination: Theme + ThemeVerseLink models (enriched theme system)
"""

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from django.db import transaction
from django.utils.text import slugify

from bible.models import CanonicalBook, Verse, Version
from bible.themes.models import Theme, ThemeVerseLink, ThemeStatus

logger = logging.getLogger(__name__)

# Mapping from catalog 3-letter codes to DB OSIS codes
CATALOG_TO_OSIS = {
    "GEN": "Gen", "EXO": "Exod", "LEV": "Lev", "NUM": "Num", "DEU": "Deut",
    "JOS": "Josh", "JDG": "Judg", "RUT": "Ruth",
    "1SA": "1Sam", "2SA": "2Sam", "1KI": "1Kgs", "2KI": "2Kgs",
    "1CH": "1Chr", "2CH": "2Chr", "EZR": "Ezra", "NEH": "Neh", "EST": "Esth",
    "JOB": "Job", "PSA": "Ps", "PRO": "Prov", "ECC": "Eccl", "SNG": "Song",
    "ISA": "Isa", "JER": "Jer", "LAM": "Lam", "EZE": "Ezek", "DAN": "Dan",
    "HOS": "Hos", "JOL": "Joel", "AMO": "Amos", "OBA": "Obad", "JON": "Jonah",
    "MIC": "Mic", "NAM": "Nah", "HAB": "Hab", "ZEP": "Zeph",
    "HAG": "Hag", "ZEC": "Zech", "MAL": "Mal",
    # NT
    "MAT": "Matt", "MRK": "Mark", "LUK": "Luke", "JHN": "John", "ACT": "Acts",
    "ROM": "Rom", "1CO": "1Cor", "2CO": "2Cor", "GAL": "Gal", "EPH": "Eph",
    "PHP": "Phil", "COL": "Col", "1TH": "1Thess", "2TH": "2Thess",
    "1TI": "1Tim", "2TI": "2Tim", "TIT": "Titus", "PHM": "Phlm",
    "HEB": "Heb", "JAS": "Jas", "1PE": "1Pet", "2PE": "2Pet",
    "1JN": "1John", "2JN": "2John", "3JN": "3John", "JUD": "Jude", "REV": "Rev",
}

# Grade to relevance_score mapping
GRADE_TO_SCORE = {3: 1.0, 2: 0.67, 1: 0.33, 0: 0.0}


@dataclass
class ImportResult:
    themes_created: int = 0
    themes_updated: int = 0
    themes_skipped: int = 0
    verse_links_created: int = 0
    verse_links_skipped: int = 0
    verses_not_found: int = 0
    errors: list = field(default_factory=list)
    duration_seconds: float = 0.0


class CatalogImporter:
    """Import theme-verse catalog from hybrid search experiments."""

    def __init__(self, catalog_path: str | None = None, version_code: str = "PT_NAA"):
        self.catalog_path = Path(catalog_path) if catalog_path else self._default_path()
        self.version_code = version_code
        self._book_cache: dict[str, CanonicalBook | None] = {}
        self._verse_cache: dict[str, Verse | None] = {}
        self._version: Version | None = None

    def _default_path(self) -> Path:
        return Path("C:/Users/Iury Coelho/Desktop/bible-hybrid-search/experiments/verse_linking_final/catalog.json")

    def _get_version(self) -> Version | None:
        if self._version is None:
            try:
                self._version = Version.objects.get(code=self.version_code)
            except Version.DoesNotExist:
                # Try partial match
                self._version = Version.objects.filter(code__icontains="NAA").first()
                if self._version is None:
                    self._version = Version.objects.first()
                    if self._version:
                        logger.warning(f"Version {self.version_code} not found, using {self._version.code}")
        return self._version

    def _resolve_book(self, catalog_code: str) -> CanonicalBook | None:
        if catalog_code in self._book_cache:
            return self._book_cache[catalog_code]

        osis_code = CATALOG_TO_OSIS.get(catalog_code)
        if not osis_code:
            logger.warning(f"Unknown catalog book code: {catalog_code}")
            self._book_cache[catalog_code] = None
            return None

        try:
            book = CanonicalBook.objects.get(osis_code=osis_code)
            self._book_cache[catalog_code] = book
            return book
        except CanonicalBook.DoesNotExist:
            logger.warning(f"Book not found in DB: {osis_code} (from {catalog_code})")
            self._book_cache[catalog_code] = None
            return None

    def _resolve_verse(self, ref: str) -> Verse | None:
        """Resolve 'HEB.11.6' to a Verse record."""
        if ref in self._verse_cache:
            return self._verse_cache[ref]

        parts = ref.split(".")
        if len(parts) != 3:
            self._verse_cache[ref] = None
            return None

        catalog_code, chapter_str, verse_str = parts
        book = self._resolve_book(catalog_code)
        if not book:
            self._verse_cache[ref] = None
            return None

        version = self._get_version()
        if not version:
            self._verse_cache[ref] = None
            return None

        try:
            verse = Verse.objects.get(
                book=book,
                version=version,
                chapter=int(chapter_str),
                number=int(verse_str),
            )
            self._verse_cache[ref] = verse
            return verse
        except Verse.DoesNotExist:
            # Try any version
            verse = Verse.objects.filter(
                book=book,
                chapter=int(chapter_str),
                number=int(verse_str),
            ).first()
            self._verse_cache[ref] = verse
            if not verse:
                logger.debug(f"Verse not found: {ref}")
            return verse

    def import_catalog(self, update_existing: bool = False) -> ImportResult:
        """Import the full theme-verse catalog."""
        result = ImportResult()
        start = time.time()

        if not self.catalog_path.exists():
            result.errors.append(f"Catalog file not found: {self.catalog_path}")
            return result

        with open(self.catalog_path, encoding="utf-8") as f:
            data = json.load(f)

        themes_data = data.get("themes", {})
        logger.info(f"Importing {len(themes_data)} themes from {self.catalog_path.name}")

        for cluster_id, theme_data in themes_data.items():
            try:
                self._import_theme(cluster_id, theme_data, update_existing, result)
            except Exception as e:
                result.errors.append(f"Error importing theme '{cluster_id}': {e}")
                logger.exception(f"Error importing theme '{cluster_id}'")

        result.duration_seconds = time.time() - start
        return result

    @transaction.atomic
    def _import_theme(
        self,
        cluster_id: str,
        theme_data: dict,
        update_existing: bool,
        result: ImportResult,
    ):
        """Import a single theme with its verse links."""
        theme_name_pt = theme_data.get("theme", cluster_id)
        theme_name_en = theme_data.get("theme_en", "")
        evidence_score = theme_data.get("evidence_score", 0.0)
        verses = theme_data.get("verses", [])

        slug = slugify(cluster_id)
        if not slug:
            slug = slugify(theme_name_pt)

        # Get or create theme
        existing = Theme.objects.filter(slug=slug).first()

        if existing and not update_existing:
            result.themes_skipped += 1
            return

        if existing:
            theme = existing
            theme.name_pt = theme_name_pt
            theme.name_en = theme_name_en or theme.name_en
            theme.evidence_score = evidence_score
            theme.verse_count = len(verses)
            theme.status = ThemeStatus.APPROVED
            theme.label_normalized = slug
            theme.save()
            result.themes_updated += 1
        else:
            theme = Theme.objects.create(
                slug=slug,
                name_pt=theme_name_pt,
                name_en=theme_name_en,
                label_normalized=slug,
                evidence_score=evidence_score,
                verse_count=len(verses),
                status=ThemeStatus.APPROVED,
                anchor_source=Theme.AnchorSource.DERIVED,
            )
            result.themes_created += 1

        # Set anchor verses (grade 3)
        grade3_refs = [v["ref"] for v in verses if v.get("grade") == 3]
        if grade3_refs:
            theme.anchor_verses = grade3_refs[:10]
            theme.save(update_fields=["anchor_verses"])

        # Import verse links
        if update_existing:
            ThemeVerseLink.objects.filter(theme=theme, source=ThemeVerseLink.LinkSource.IMPORTED).delete()

        links_to_create = []
        for verse_data in verses:
            ref = verse_data.get("ref", "")
            grade = verse_data.get("grade", 1)
            verse = self._resolve_verse(ref)

            if not verse:
                result.verses_not_found += 1
                continue

            # Check for existing link
            if ThemeVerseLink.objects.filter(theme=theme, verse=verse).exists():
                result.verse_links_skipped += 1
                continue

            links_to_create.append(
                ThemeVerseLink(
                    theme=theme,
                    verse=verse,
                    grade=grade,
                    relevance_score=GRADE_TO_SCORE.get(grade, 0.33),
                    is_primary_theme=(grade == 3),
                    source=ThemeVerseLink.LinkSource.IMPORTED,
                )
            )

        if links_to_create:
            ThemeVerseLink.objects.bulk_create(links_to_create, ignore_conflicts=True)
            result.verse_links_created += len(links_to_create)
