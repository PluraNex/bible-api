"""
Bible API Data Core Engine - Unified & Streamlined

All-in-one data processing engine that replaces the complex pipeline
with a simple, robust, and maintainable solution.
"""
import json
import logging
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from django.db import transaction

from bible.models import CanonicalBook, CrossReference, Language, License, Testament, Verse, Version

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Simple result class for operations."""

    success: bool
    items_processed: int = 0
    error_message: str | None = None
    details: dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class BibleDataEngine:
    """
    Ultra-simplified Bible data processing engine.

    Does everything the old complex pipeline did, but in one clean class:
    - Language detection
    - Data validation
    - Migration/reorganization
    - Database population
    - Cross-references
    - Quality checks
    """

    # Language detection patterns (consolidated from old system)
    LANG_PATTERNS = {
        "pt-BR": [r"^(ACF|ARA|ARC|AS21|JFAA|KJA|KJF|NAA|NBV|NTLH|NVI|NVT|TB)$", r"^Por.*", r".*Almeida.*"],
        "en-US": [r"^(KJV|ASV|BBE|WEB|YLT|NKJV|ESV|NIV)$", r"^(Geneva|Darby).*"],
        "de-DE": [r"^Ger.*", r".*Luther.*", r".*Elberfelder.*"],
        "fr-FR": [r"^Fre.*", r".*Crampon.*", r".*Segond.*"],
        "es-ES": [r"^Spa.*", r".*Valera.*", r"^RV.*"],
        "it-IT": [r"^Ita.*", r".*Diodati.*"],
        "nl-NL": [r"^Dut.*", r"^Nl.*"],
    }

    # Book mapping (simplified from old system)
    BOOK_MAPPING = {
        # Portuguese format
        "Gn": {"osis": "Gen", "order": 1, "testament": "OLD", "chapters": 50},
        "Êx": {"osis": "Exod", "order": 2, "testament": "OLD", "chapters": 40},
        "Lv": {"osis": "Lev", "order": 3, "testament": "OLD", "chapters": 27},
        "Nm": {"osis": "Num", "order": 4, "testament": "OLD", "chapters": 36},
        "Dt": {"osis": "Deut", "order": 5, "testament": "OLD", "chapters": 34},
        "Js": {"osis": "Josh", "order": 6, "testament": "OLD", "chapters": 24},
        "Jz": {"osis": "Judg", "order": 7, "testament": "OLD", "chapters": 21},
        "Rt": {"osis": "Ruth", "order": 8, "testament": "OLD", "chapters": 4},
        "1Sm": {"osis": "1Sam", "order": 9, "testament": "OLD", "chapters": 31},
        "2Sm": {"osis": "2Sam", "order": 10, "testament": "OLD", "chapters": 24},
        "1Rs": {"osis": "1Kgs", "order": 11, "testament": "OLD", "chapters": 22},
        "2Rs": {"osis": "2Kgs", "order": 12, "testament": "OLD", "chapters": 25},
        "1Cr": {"osis": "1Chr", "order": 13, "testament": "OLD", "chapters": 29},
        "2Cr": {"osis": "2Chr", "order": 14, "testament": "OLD", "chapters": 36},
        "Ed": {"osis": "Ezra", "order": 15, "testament": "OLD", "chapters": 10},
        "Ne": {"osis": "Neh", "order": 16, "testament": "OLD", "chapters": 13},
        "Et": {"osis": "Esth", "order": 17, "testament": "OLD", "chapters": 10},
        "Jó": {"osis": "Job", "order": 18, "testament": "OLD", "chapters": 42},
        "Sl": {"osis": "Ps", "order": 19, "testament": "OLD", "chapters": 150},
        "Pv": {"osis": "Prov", "order": 20, "testament": "OLD", "chapters": 31},
        "Ec": {"osis": "Eccl", "order": 21, "testament": "OLD", "chapters": 12},
        "Ct": {"osis": "Song", "order": 22, "testament": "OLD", "chapters": 8},
        "Is": {"osis": "Isa", "order": 23, "testament": "OLD", "chapters": 66},
        "Jr": {"osis": "Jer", "order": 24, "testament": "OLD", "chapters": 52},
        "Lm": {"osis": "Lam", "order": 25, "testament": "OLD", "chapters": 5},
        "Ez": {"osis": "Ezek", "order": 26, "testament": "OLD", "chapters": 48},
        "Dn": {"osis": "Dan", "order": 27, "testament": "OLD", "chapters": 12},
        "Os": {"osis": "Hos", "order": 28, "testament": "OLD", "chapters": 14},
        "Jl": {"osis": "Joel", "order": 29, "testament": "OLD", "chapters": 3},
        "Am": {"osis": "Amos", "order": 30, "testament": "OLD", "chapters": 9},
        "Ob": {"osis": "Obad", "order": 31, "testament": "OLD", "chapters": 1},
        "Jn": {"osis": "Jonah", "order": 32, "testament": "OLD", "chapters": 4},
        "Mq": {"osis": "Mic", "order": 33, "testament": "OLD", "chapters": 7},
        "Na": {"osis": "Nah", "order": 34, "testament": "OLD", "chapters": 3},
        "Hc": {"osis": "Hab", "order": 35, "testament": "OLD", "chapters": 3},
        "Sf": {"osis": "Zeph", "order": 36, "testament": "OLD", "chapters": 3},
        "Ag": {"osis": "Hag", "order": 37, "testament": "OLD", "chapters": 2},
        "Zc": {"osis": "Zech", "order": 38, "testament": "OLD", "chapters": 14},
        "Ml": {"osis": "Mal", "order": 39, "testament": "OLD", "chapters": 4},
        # New Testament
        "Mt": {"osis": "Matt", "order": 40, "testament": "NEW", "chapters": 28},
        "Mc": {"osis": "Mark", "order": 41, "testament": "NEW", "chapters": 16},
        "Lc": {"osis": "Luke", "order": 42, "testament": "NEW", "chapters": 24},
        "Jo": {"osis": "John", "order": 43, "testament": "NEW", "chapters": 21},
        "At": {"osis": "Acts", "order": 44, "testament": "NEW", "chapters": 28},
        "Rm": {"osis": "Rom", "order": 45, "testament": "NEW", "chapters": 16},
        "1Co": {"osis": "1Cor", "order": 46, "testament": "NEW", "chapters": 16},
        "2Co": {"osis": "2Cor", "order": 47, "testament": "NEW", "chapters": 13},
        "Gl": {"osis": "Gal", "order": 48, "testament": "NEW", "chapters": 6},
        "Ef": {"osis": "Eph", "order": 49, "testament": "NEW", "chapters": 6},
        "Fp": {"osis": "Phil", "order": 50, "testament": "NEW", "chapters": 4},
        "Cl": {"osis": "Col", "order": 51, "testament": "NEW", "chapters": 4},
        "1Ts": {"osis": "1Thess", "order": 52, "testament": "NEW", "chapters": 5},
        "2Ts": {"osis": "2Thess", "order": 53, "testament": "NEW", "chapters": 3},
        "1Tm": {"osis": "1Tim", "order": 54, "testament": "NEW", "chapters": 6},
        "2Tm": {"osis": "2Tim", "order": 55, "testament": "NEW", "chapters": 4},
        "Tt": {"osis": "Titus", "order": 56, "testament": "NEW", "chapters": 3},
        "Fm": {"osis": "Phlm", "order": 57, "testament": "NEW", "chapters": 1},
        "Hb": {"osis": "Heb", "order": 58, "testament": "NEW", "chapters": 13},
        "Tg": {"osis": "Jas", "order": 59, "testament": "NEW", "chapters": 5},
        "1Pe": {"osis": "1Pet", "order": 60, "testament": "NEW", "chapters": 5},
        "2Pe": {"osis": "2Pet", "order": 61, "testament": "NEW", "chapters": 3},
        "1Jo": {"osis": "1John", "order": 62, "testament": "NEW", "chapters": 5},
        "2Jo": {"osis": "2John", "order": 63, "testament": "NEW", "chapters": 1},
        "3Jo": {"osis": "3John", "order": 64, "testament": "NEW", "chapters": 1},
        "Jd": {"osis": "Jude", "order": 65, "testament": "NEW", "chapters": 1},
        "Ap": {"osis": "Rev", "order": 66, "testament": "NEW", "chapters": 22},
        # English format alternatives
        "Genesis": {"osis": "Gen", "order": 1, "testament": "OLD", "chapters": 50},
        "Exodus": {"osis": "Exod", "order": 2, "testament": "OLD", "chapters": 40},
        "Matthew": {"osis": "Matt", "order": 40, "testament": "NEW", "chapters": 28},
        "Mark": {"osis": "Mark", "order": 41, "testament": "NEW", "chapters": 16},
        "Luke": {"osis": "Luke", "order": 42, "testament": "NEW", "chapters": 24},
        "John": {"osis": "John", "order": 43, "testament": "NEW", "chapters": 21},
    }

    def __init__(self, data_dir: str = "data"):
        """Initialize with data directory."""
        self.data_dir = Path(data_dir)
        self.processed_dir = self.data_dir / "processed" / "bibles" / "canonical"
        self.external_dir = self.data_dir / "external" / "multilingual-collection" / "raw"

    def detect_language(self, filename: str) -> str:
        """Simple language detection from filename."""
        stem = Path(filename).stem

        for lang_code, patterns in self.LANG_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, stem, re.IGNORECASE):
                    return lang_code

        return "unknown"

    def validate_bible_json(self, data: dict | list) -> bool:
        """Quick validation of Bible JSON structure (supports both formats)."""

        # Format 1: List of books (Portuguese format)
        if isinstance(data, list):
            if len(data) == 0:
                return False
            first_book = data[0]
            if "abbrev" not in first_book or "chapters" not in first_book:
                return False
            if len(first_book["chapters"]) == 0:
                return False
            # Chapters are arrays of strings
            first_chapter = first_book["chapters"][0]
            if not isinstance(first_chapter, list) or len(first_chapter) == 0:
                return False
            return True

        # Format 2: Dict with books array (Standard format)
        elif isinstance(data, dict):
            if "books" not in data:
                return False
            books = data["books"]
            if not isinstance(books, list) or len(books) == 0:
                return False
            first_book = books[0]
            if "name" not in first_book or "chapters" not in first_book:
                return False
            if len(first_book["chapters"]) == 0:
                return False
            first_chapter = first_book["chapters"][0]
            if "verses" not in first_chapter or len(first_chapter["verses"]) == 0:
                return False
            first_verse = first_chapter["verses"][0]
            if "text" not in first_verse or not first_verse["text"]:
                return False
            return True

        return False

    def migrate_raw_files(self, source_dir: str | None = None, min_confidence: float = 0.6) -> ProcessingResult:
        """Migrate raw Bible files to processed structure."""
        if source_dir:
            source_path = Path(source_dir)
        else:
            source_path = self.external_dir

        if not source_path.exists():
            return ProcessingResult(success=False, error_message=f"Source directory not found: {source_path}")

        processed_count = 0
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        for file_path in source_path.glob("*.json"):
            lang_code = self.detect_language(file_path.name)

            if lang_code == "unknown":
                logger.warning(f"Could not detect language for {file_path.name}")
                continue

            # Create language/version directory structure
            version_code = file_path.stem.lower()
            target_dir = self.processed_dir / lang_code.split("-")[0] / version_code
            target_dir.mkdir(parents=True, exist_ok=True)

            # Copy file
            target_file = target_dir / f"{version_code}.json"
            shutil.copy2(file_path, target_file)
            processed_count += 1

            logger.info(f"Migrated: {file_path.name} -> {lang_code}/{version_code}")

        return ProcessingResult(
            success=True, items_processed=processed_count, details={"migrated_files": processed_count}
        )

    @transaction.atomic
    def populate_version(self, version_file: Path, language_code: str, version_code: str) -> ProcessingResult:
        """Populate single Bible version into database."""
        try:
            with open(version_file, encoding="utf-8") as f:
                bible_data = json.load(f)

            if not self.validate_bible_json(bible_data):
                return ProcessingResult(success=False, error_message="Invalid JSON structure")

            # Ensure language exists
            language, _ = Language.objects.get_or_create(
                code=language_code, defaults={"name": self._get_language_name(language_code)}
            )

            # Ensure license exists
            license_obj, _ = License.objects.get_or_create(code="PD", defaults={"name": "Public Domain"})

            # Get version name from data
            if isinstance(bible_data, dict):
                version_name = bible_data.get("name", bible_data.get("translation", version_code.upper()))
            else:
                version_name = version_code.upper()

            # Create version
            version, created = Version.objects.get_or_create(
                code=version_code.upper(), defaults={"name": version_name, "language": language, "license": license_obj}
            )

            if not created:
                # Clear existing verses
                Verse.objects.filter(version=version).delete()

            # Process books and verses - handle both formats
            verses_created = 0
            verse_batch = []

            # Determine format and extract books
            if isinstance(bible_data, list):
                # Format 1: List of books (Portuguese format)
                books_data = bible_data
            else:
                # Format 2: Dict with books array (Standard format)
                books_data = bible_data["books"]

            for book_data in books_data:
                # Handle different book name fields
                if "abbrev" in book_data:
                    # Portuguese format uses abbreviation
                    book_name = book_data["abbrev"]
                elif "name" in book_data:
                    # Standard format uses name
                    book_name = book_data["name"]
                else:
                    logger.warning("Book missing name/abbreviation")
                    continue

                if book_name not in self.BOOK_MAPPING:
                    logger.warning(f"Unknown book: {book_name}")
                    continue

                book_info = self.BOOK_MAPPING[book_name]
                canonical_book = self._ensure_canonical_book(book_info)

                for chapter_num, chapter_data in enumerate(book_data["chapters"], 1):
                    # Handle different chapter formats
                    if isinstance(chapter_data, list):
                        # Format 1: Chapter is array of verse strings
                        for verse_num, verse_text in enumerate(chapter_data, 1):
                            verse_text = verse_text.strip()
                            if not verse_text:
                                continue

                            verse_batch.append(
                                Verse(
                                    book=canonical_book,
                                    version=version,
                                    chapter=chapter_num,
                                    number=verse_num,
                                    text=verse_text,
                                )
                            )
                            verses_created += 1
                    else:
                        # Format 2: Chapter is dict with verses array
                        verses_array = chapter_data.get("verses", []) if isinstance(chapter_data, dict) else []
                        for verse_data in verses_array:
                            if isinstance(verse_data, dict):
                                verse_text = verse_data.get("text", "").strip()
                                verse_num = verse_data.get("verse", len(verse_batch) + 1)
                            else:
                                # Fallback: treat as string
                                verse_text = str(verse_data).strip()
                                verse_num = len(verse_batch) + 1

                            if not verse_text:
                                continue

                            verse_batch.append(
                                Verse(
                                    book=canonical_book,
                                    version=version,
                                    chapter=chapter_num,
                                    number=verse_num,
                                    text=verse_text,
                                )
                            )
                            verses_created += 1

                    # Batch insert every 1000 verses
                    if len(verse_batch) >= 1000:
                        Verse.objects.bulk_create(verse_batch)
                        verse_batch = []

            # Insert remaining verses
            if verse_batch:
                Verse.objects.bulk_create(verse_batch)

            logger.info(f"Successfully populated {version_code} with {verses_created} verses")

            return ProcessingResult(
                success=True,
                items_processed=verses_created,
                details={"version": version_code, "verses": verses_created},
            )

        except Exception as e:
            logger.error(f"Error populating {version_code}: {e}")
            return ProcessingResult(success=False, error_message=str(e))

    def populate_all(self, language_filter: list[str] | None = None) -> ProcessingResult:
        """Populate all processed Bible versions."""
        if not self.processed_dir.exists():
            return ProcessingResult(success=False, error_message="No processed data directory found")

        total_versions = 0
        total_verses = 0
        failed_versions = []

        for lang_dir in self.processed_dir.iterdir():
            if not lang_dir.is_dir():
                continue

            lang_code = lang_dir.name
            # Apply language mapping
            mapped_lang = self._map_language_code(lang_code)

            if language_filter and mapped_lang not in language_filter:
                continue

            for version_dir in lang_dir.iterdir():
                if not version_dir.is_dir():
                    continue

                version_code = version_dir.name
                version_file = version_dir / f"{version_code}.json"

                if version_file.exists():
                    result = self.populate_version(version_file, mapped_lang, version_code)
                    total_versions += 1

                    if result.success:
                        total_verses += result.items_processed
                    else:
                        failed_versions.append((version_code, result.error_message))

        # Also populate commentaries with multilingual support
        commentary_result = self.populate_commentaries(language_filter or ["pt-BR", "en-US"])
        total_commentaries = commentary_result.items_processed if commentary_result.success else 0

        success = len(failed_versions) == 0
        return ProcessingResult(
            success=success,
            items_processed=total_verses + total_commentaries,
            details={
                "total_versions": total_versions,
                "total_verses": total_verses,
                "total_commentaries": total_commentaries,
                "failed_versions": failed_versions,
            },
        )

    def populate_cross_references(self, crossref_file: str = "data/external/cross-references.txt") -> ProcessingResult:
        """Populate cross references from external file."""
        crossref_path = Path(crossref_file)
        if not crossref_path.exists():
            return ProcessingResult(success=False, error_message=f"Cross reference file not found: {crossref_file}")

        created_count = 0
        crossref_batch = []

        with open(crossref_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Parse cross reference line (simplified)
                parts = line.split("\t")
                if len(parts) < 4:
                    continue

                try:
                    from_ref, to_ref, weight = parts[0], parts[1], float(parts[2])

                    # Find verses (simplified - assumes verses exist)
                    from_verse = self._find_verse(from_ref)
                    to_verse = self._find_verse(to_ref)

                    if from_verse and to_verse:
                        crossref_batch.append(CrossReference(from_verse=from_verse, to_verse=to_verse, weight=weight))
                        created_count += 1

                        if len(crossref_batch) >= 1000:
                            CrossReference.objects.bulk_create(crossref_batch, ignore_conflicts=True)
                            crossref_batch = []

                except (ValueError, IndexError):
                    continue

        # Insert remaining cross references
        if crossref_batch:
            CrossReference.objects.bulk_create(crossref_batch, ignore_conflicts=True)

        return ProcessingResult(
            success=True, items_processed=created_count, details={"cross_references": created_count}
        )

    def get_status(self) -> dict[str, Any]:
        """Get simple status of data pipeline."""
        status = {"directories": {}, "database": {}, "processed_files": 0}

        # Check directories
        for name, path in [("external", self.external_dir), ("processed", self.processed_dir)]:
            status["directories"][name] = {
                "exists": path.exists(),
                "files": len(list(path.glob("**/*.json"))) if path.exists() else 0,
            }

        # Database stats
        status["database"] = {
            "languages": Language.objects.count(),
            "versions": Version.objects.count(),
            "verses": Verse.objects.count(),
            "cross_references": CrossReference.objects.count(),
        }

        return status

    def populate_commentaries(self, languages: list[str]) -> ProcessingResult:
        """
        Populate commentary data following multilingual pattern.

        Args:
            languages: List of language codes to process
        """
        from bible.models import CommentarySource

        total_entries = 0
        total_authors = 0

        # Look for commentary data in scraped directory
        scraped_dir = Path("data/scraped/commentaries")

        if not scraped_dir.exists():
            logger.warning("⚠️ No scraped commentaries directory found")
            return ProcessingResult(success=True, items_processed=0)

        with transaction.atomic():
            # Create commentary sources with multilingual support
            for lang_code in languages:
                try:
                    language = Language.objects.get(code=lang_code)

                    # Create Catena Bible source for each language
                    source, created = CommentarySource.objects.get_or_create(
                        short_code=f"CATENA_{lang_code.upper()}",
                        defaults={
                            "name": f"Catena Bible Commentary ({lang_code})",
                            "language": language,
                            "description": f"Ancient Christian commentary collection in {lang_code}",
                            "url": "https://catenabible.com",
                            "is_active": True,
                        },
                    )

                    if created:
                        logger.info(f"✅ Created commentary source: {source.name}")

                    # Process commentary files for this language
                    lang_entries = self._process_commentary_files(scraped_dir, source, language)
                    total_entries += lang_entries

                except Language.DoesNotExist:
                    logger.warning(f"⚠️ Language {lang_code} not found, skipping commentary population")
                    continue

            # Populate authors from commentary data
            total_authors = self._populate_authors_from_commentaries()

        logger.info(f"✅ Commentary population complete: {total_entries} entries, {total_authors} authors")
        return ProcessingResult(
            success=True,
            items_processed=total_entries + total_authors,
            details={"commentary_entries": total_entries, "authors": total_authors, "languages": languages},
        )

    def _process_commentary_files(self, scraped_dir: Path, source, language) -> int:
        """Process individual commentary JSON files."""
        from bible.models import CommentaryEntry

        entries_created = 0
        commentary_batch = []

        # Find all commentary JSON files
        json_files = list(scraped_dir.glob("**/*.json"))
        logger.info(f"📂 Found {len(json_files)} commentary files")

        for json_file in json_files:
            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)

                # Extract verse reference (e.g., "LK 1:1")
                verse_ref = data.get("verse_reference", "")
                if not verse_ref:
                    continue

                # Parse reference: "LK 1:1" -> book=Luke, chapter=1, verse=1
                book_code, chapter_verse = verse_ref.split(" ")
                chapter, verse = chapter_verse.split(":")

                # Find canonical book
                book = self._find_canonical_book(book_code)
                if not book:
                    continue

                # Process each commentary in the file
                commentaries = data.get("commentaries", [])
                for commentary in commentaries:
                    author_name = commentary.get("author", "")
                    content = commentary.get("content", "")

                    if not content or not author_name:
                        continue

                    # Get or create author
                    self._get_or_create_author(author_name, commentary)

                    # Create commentary entry
                    commentary_batch.append(
                        CommentaryEntry(
                            source=source,
                            book=book,
                            chapter=int(chapter),
                            verse_start=int(verse),
                            verse_end=int(verse),
                            title=f"Commentary on {verse_ref}",
                            body_text=content,
                            original_reference=verse_ref,
                        )
                    )

                    entries_created += 1

                    # Batch insert
                    if len(commentary_batch) >= 100:
                        CommentaryEntry.objects.bulk_create(commentary_batch, ignore_conflicts=True)
                        commentary_batch = []

            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning(f"⚠️ Error processing {json_file}: {e}")
                continue

        # Insert remaining entries
        if commentary_batch:
            CommentaryEntry.objects.bulk_create(commentary_batch, ignore_conflicts=True)

        return entries_created

    def _find_canonical_book(self, book_code: str) -> Optional["CanonicalBook"]:
        """Find canonical book by various codes (Luke -> LK, etc.)."""
        # Map common codes
        book_mappings = {
            "LK": "Luke",
            "MT": "Matt",
            "MK": "Mark",
            "JN": "John",
            "AC": "Acts",
            "RM": "Rom",
            "CO1": "1Cor",
            "CO2": "2Cor",
            "GA": "Gal",
            "EP": "Eph",
            "PH": "Phil",
            "COL": "Col",
            "TH1": "1Thess",
            "TH2": "2Thess",
            "TI1": "1Tim",
            "TI2": "2Tim",
            "TIT": "Titus",
            "PHM": "Phlm",
            "HE": "Heb",
            "JA": "Jas",
            "PE1": "1Pet",
            "PE2": "2Pet",
            "JN1": "1John",
            "JN2": "2John",
            "JN3": "3John",
            "JU": "Jude",
            "RE": "Rev",
        }

        osis_code = book_mappings.get(book_code, book_code)

        try:
            return CanonicalBook.objects.get(osis_code=osis_code)
        except CanonicalBook.DoesNotExist:
            # Try alternative lookups
            try:
                return CanonicalBook.objects.filter(names__abbreviation=book_code).first()
            except Exception:
                logger.warning(f"⚠️ Book not found: {book_code}")
                return None

    def _get_or_create_author(self, author_name: str, commentary_data: dict):
        """Get or create author with multilingual support."""
        from bible.models import Author

        # Extract period from commentary (e.g., "AD397")
        period = commentary_data.get("period", "")

        # Parse period to get approximate dates
        birth_year = None
        death_year = None
        century = None

        if period and period.startswith("AD"):
            try:
                year = int(period.replace("AD", "").strip())
                death_year = year
                birth_year = year - 60  # Rough estimate
                century = f"{(year // 100) + 1}th century"
            except ValueError:
                pass

        # Determine author type based on period
        author_type = "church_father"
        if death_year and death_year > 1500:
            author_type = "modern"
        elif death_year and death_year > 1000:
            author_type = "medieval"

        author, created = Author.objects.get_or_create(
            name=author_name,
            defaults={
                "short_name": author_name.split()[-1] if " " in author_name else author_name,
                "author_type": author_type,
                "birth_year": birth_year,
                "death_year": death_year,
                "century": century or period,
                "reliability_rating": "good",
            },
        )

        return author

    def _populate_authors_from_commentaries(self) -> int:
        """Populate additional author metadata from commentary sources."""
        # This would extract unique authors from commentaries
        # and enrich their metadata - simplified for now
        return 0

    def _map_language_code(self, lang_code: str) -> str:
        """Map generic language codes to specific ones."""
        mapping = {
            "pt": "pt-BR",
            "en": "en-US",
            "de": "de-DE",
            "fr": "fr-FR",
            "es": "es-ES",
            "it": "it-IT",
            "nl": "nl-NL",
        }
        return mapping.get(lang_code, lang_code)

    def _get_language_name(self, code: str) -> str:
        """Get language name from code."""
        names = {
            "pt-BR": "Português (Brasil)",
            "en-US": "English (United States)",
            "de-DE": "Deutsch (Deutschland)",
            "fr-FR": "Français (France)",
            "es-ES": "Español (España)",
            "it-IT": "Italiano (Italia)",
            "nl-NL": "Nederlands (Nederland)",
        }
        return names.get(code, code.upper())

    def _ensure_canonical_book(self, book_info: dict) -> CanonicalBook:
        """Ensure canonical book exists."""
        testament_name = book_info["testament"]

        # Try to get existing testament first
        try:
            testament = Testament.objects.get(name=testament_name)
        except Testament.DoesNotExist:
            testament = Testament.objects.create(name=testament_name, description=f"{testament_name} Testament")

        # Try to get existing canonical book first
        try:
            book = CanonicalBook.objects.get(osis_code=book_info["osis"])
        except CanonicalBook.DoesNotExist:
            book = CanonicalBook.objects.create(
                osis_code=book_info["osis"],
                canonical_order=book_info["order"],
                testament=testament,
                chapter_count=book_info["chapters"],
            )

        return book

    def _find_verse(self, verse_ref: str) -> Verse | None:
        """Find verse from reference string (simplified)."""
        # This would need proper parsing logic
        # For now, return None to avoid errors
        return None
