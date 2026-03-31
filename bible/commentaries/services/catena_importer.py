"""
Import authors from validated_authors.json and commentaries from Catena Bible dataset.

Usage:
    python manage.py bible commentaries import-authors
    python manage.py bible commentaries import-entries [--limit 100]
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from django.db import transaction

from bible.commentaries.models import Author, CommentaryEntry, CommentarySource
from bible.models import CanonicalBook

logger = logging.getLogger(__name__)

# OSIS mapping: Catena Bible uses short codes in folder names
CATENA_BOOK_TO_OSIS = {
    # OT — full names
    "genesis": "Gen", "exodus": "Exod", "leviticus": "Lev", "numbers": "Num",
    "deuteronomy": "Deut", "joshua": "Josh", "judges": "Judg", "ruth": "Ruth",
    "1samuel": "1Sam", "2samuel": "2Sam", "1kings": "1Kgs", "2kings": "2Kgs",
    "1chronicles": "1Chr", "2chronicles": "2Chr", "ezra": "Ezra", "nehemiah": "Neh",
    "esther": "Esth", "job": "Job", "psalms": "Ps", "proverbs": "Prov",
    "ecclesiastes": "Eccl", "song_of_solomon": "Song", "songofsolomon": "Song",
    "isaiah": "Isa", "jeremiah": "Jer", "lamentations": "Lam", "ezekiel": "Ezek",
    "daniel": "Dan", "hosea": "Hos", "joel": "Joel", "amos": "Amos",
    "obadiah": "Obad", "jonah": "Jonah", "micah": "Mic", "nahum": "Nah",
    "habakkuk": "Hab", "zephaniah": "Zeph", "haggai": "Hag", "zechariah": "Zech",
    "malachi": "Mal",
    # OT — Catena Bible short folder codes (used in dataset directory names)
    "gn": "Gen", "ex": "Exod", "lv": "Lev", "nm": "Num", "dt": "Deut",
    "jo": "Josh", "jgs": "Judg", "ru": "Ruth",
    "1sm": "1Sam", "2sm": "2Sam", "1kgs": "1Kgs", "2kgs": "2Kgs",
    "1chr": "1Chr", "2chr": "2Chr", "ezr": "Ezra", "neh": "Neh",
    "est": "Esth", "jb": "Job", "ps": "Ps", "prv": "Prov",
    "eccl": "Eccl", "sg": "Song",
    "is": "Isa", "jer": "Jer", "lam": "Lam", "ez": "Ezek",
    "dn": "Dan", "hos": "Hos", "jl": "Joel", "am": "Amos",
    "ob": "Obad", "jon": "Jonah", "mi": "Mic", "na": "Nah",
    "hb": "Hab", "zep": "Zeph", "hg": "Hag", "zec": "Zech",
    "mal": "Mal",
    # NT — short codes (used in some filenames)
    "1thes": "1Thess", "2thes": "2Thess",
    # Deuterocanonical
    "tobit": "Tob", "judith": "Jdt", "wisdom": "Wis", "sirach": "Sir",
    "baruch": "Bar", "1maccabees": "1Macc", "2maccabees": "2Macc",
    # NT — full names
    "matthew": "Matt", "mark": "Mark", "luke": "Luke", "john": "John",
    "acts": "Acts", "romans": "Rom", "1corinthians": "1Cor", "2corinthians": "2Cor",
    "galatians": "Gal", "ephesians": "Eph", "philippians": "Phil",
    "colossians": "Col", "1thessalonians": "1Thess", "2thessalonians": "2Thess",
    "1timothy": "1Tim", "2timothy": "2Tim", "titus": "Titus", "philemon": "Phlm",
    "hebrews": "Heb", "james": "Jas", "1peter": "1Pet", "2peter": "2Pet",
    "1john": "1John", "2john": "2John", "3john": "3John", "jude": "Jude",
    "revelation": "Rev",
}

AUTHORS_JSON = Path("data/authors/validated_authors.json")
CATENA_BASE = Path("C:/Users/Iury Coelho/Desktop/bible-commentaries-dataset/data/01_cleaned/catena_bible")


@dataclass
class ImportResult:
    authors_created: int = 0
    authors_updated: int = 0
    authors_skipped: int = 0
    sources_created: int = 0
    entries_created: int = 0
    entries_skipped: int = 0
    books_not_found: int = 0
    errors: list = field(default_factory=list)
    duration_seconds: float = 0.0


class CatenaImporter:
    """Import validated authors and Catena Bible commentaries."""

    def __init__(self, authors_json: str | None = None, catena_base: str | None = None):
        self.authors_json = Path(authors_json) if authors_json else AUTHORS_JSON
        self.catena_base = Path(catena_base) if catena_base else CATENA_BASE
        self._book_cache: dict[str, CanonicalBook | None] = {}
        self._author_cache: dict[str, Author | None] = {}

    def _resolve_book(self, folder_name: str) -> CanonicalBook | None:
        """Resolve a Catena folder name to a CanonicalBook."""
        key = folder_name.lower().replace(" ", "").replace("-", "").replace("_", "")
        if key in self._book_cache:
            return self._book_cache[key]

        osis = CATENA_BOOK_TO_OSIS.get(key)
        if not osis:
            # Try partial match
            for catena_key, osis_code in CATENA_BOOK_TO_OSIS.items():
                if catena_key in key or key in catena_key:
                    osis = osis_code
                    break

        if not osis:
            self._book_cache[key] = None
            return None

        try:
            book = CanonicalBook.objects.get(osis_code=osis)
            self._book_cache[key] = book
            return book
        except CanonicalBook.DoesNotExist:
            self._book_cache[key] = None
            return None

    def _parse_verse_ref(self, filename: str):
        """Parse 'rom_12_01.json' → ('romans', 12, 1)."""
        name = filename.replace(".json", "")
        parts = name.split("_")
        if len(parts) < 3:
            return None, None, None

        # Last two parts are chapter and verse
        try:
            verse = int(parts[-1])
            chapter = int(parts[-2])
            book_part = "_".join(parts[:-2])
            return book_part, chapter, verse
        except (ValueError, IndexError):
            return None, None, None

    # ─── Authors Import ───────────────────────────────────────

    def import_authors(self, update_existing: bool = False) -> ImportResult:
        """Import authors from validated_authors.json."""
        result = ImportResult()
        start = time.time()

        if not self.authors_json.exists():
            result.errors.append(f"Authors JSON not found: {self.authors_json}")
            return result

        with open(self.authors_json, encoding="utf-8") as f:
            data = json.load(f)

        authors_data = data.get("authors", [])
        logger.info(f"Importing {len(authors_data)} authors from {self.authors_json.name}")

        for author_data in authors_data:
            try:
                self._import_author(author_data, update_existing, result)
            except Exception as e:
                name = author_data.get("canonical_name", "?")
                result.errors.append(f"Error importing author '{name}': {e}")
                logger.exception(f"Error importing author '{name}'")

        result.duration_seconds = time.time() - start
        return result

    def _import_author(self, data: dict, update_existing: bool, result: ImportResult):
        """Import a single author."""
        canonical_name = data.get("canonical_name", data.get("dataset_name", ""))
        if not canonical_name:
            return

        existing = Author.objects.filter(name=canonical_name).first()
        if existing and not update_existing:
            self._author_cache[data.get("dataset_name", "")] = existing
            result.authors_skipped += 1
            return

        # Map JSON author_type to model choices
        author_type = data.get("author_type", "church_father")
        type_map = {
            "modern_compilation": "modern_commentator",
            "bible_translation": "modern_commentator",
            "apostolic": "apostolic_father",
        }
        author_type = type_map.get(author_type, author_type)

        # Build Wikipedia URL from slug
        wiki_slug = data.get("wikipedia_slug", "")
        wiki_url = f"https://en.wikipedia.org/wiki/{wiki_slug}" if wiki_slug else ""

        fields = {
            "name": canonical_name,
            "short_name": data.get("short_name", ""),
            "author_type": author_type,
            "birth_year": data.get("born"),
            "death_year": data.get("died"),
            "birthplace": data.get("born_location", "") or "",
            "death_location": data.get("died_location", "") or "",
            "tradition": data.get("tradition", "") or "",
            "theological_school": data.get("theological_school", "") or "",
            "era": data.get("patristic_era", "") or "",
            "major_works": data.get("major_works", []),
            "biography_summary": data.get("description", "") or "",
            "theological_contributions": data.get("theological_contribution", "") or "",
            "is_doctor_of_church": data.get("is_doctor_of_church", False),
            "is_saint": data.get("is_church_father", False),
            "portrait_image": data.get("avatar_url", "") or "",
            "portrait_source": "Wikimedia Commons",
            "portrait_license": "Public Domain",
            "wikipedia_url": wiki_url,
            "primary_hermeneutic": data.get("hermeneutical_method", "") or "",
            "orthodoxy_status": data.get("orthodoxy_status", "orthodox"),
            "recognized_by": data.get("recognized_by", []),
            "councils": data.get("councils") or [],
        }

        if existing:
            for key, value in fields.items():
                setattr(existing, key, value)
            existing.save()
            self._author_cache[data.get("dataset_name", "")] = existing
            result.authors_updated += 1
        else:
            author = Author.objects.create(**fields)
            self._author_cache[data.get("dataset_name", "")] = author
            result.authors_created += 1

    # ─── Sources Import ───────────────────────────────────────

    def ensure_sources(self) -> dict[str, CommentarySource]:
        """Create or get the Catena Bible and CCEL sources."""
        sources = {}

        catena, created = CommentarySource.objects.get_or_create(
            short_code="CATENA",
            defaults={
                "name": "Catena Bible Commentary",
                "source_type": "catena",
                "description": "Collection of Church Fathers commentaries on Scripture (AD 100-1700), sourced from catenabible.com",
                "url": "https://catenabible.com",
                "is_active": True,
                "is_featured": True,
                "is_free": True,
                "coverage": "whole_bible",
                "author_type": "Church Fathers",
            },
        )
        sources["catena"] = catena
        if created:
            logger.info("Created Catena Bible source")

        ccel, created = CommentarySource.objects.get_or_create(
            short_code="CCEL",
            defaults={
                "name": "Christian Classics Ethereal Library",
                "source_type": "patristic",
                "description": "Digital library of classic Christian texts spanning 2000 years of Christian writing",
                "url": "https://www.ccel.org",
                "is_active": True,
                "is_featured": True,
                "is_free": True,
                "coverage": "whole_bible",
                "author_type": "Mixed (Patristic to Modern)",
            },
        )
        sources["ccel"] = ccel
        if created:
            logger.info("Created CCEL source")

        return sources

    # ─── Entries Import ───────────────────────────────────────

    def import_entries(self, limit: int | None = None, batch_size: int = 500) -> ImportResult:
        """Import commentary entries from Catena Bible dataset."""
        result = ImportResult()
        start = time.time()

        if not self.catena_base.exists():
            result.errors.append(f"Catena base not found: {self.catena_base}")
            return result

        # Ensure authors are cached
        if not self._author_cache:
            self._warm_author_cache()

        sources = self.ensure_sources()
        catena_source = sources["catena"]

        entries_batch = []
        total_processed = 0

        # Walk through all JSON files
        for root, _dirs, files in os.walk(self.catena_base):
            for filename in sorted(files):
                if not filename.endswith(".json"):
                    continue

                if limit and total_processed >= limit:
                    break

                filepath = os.path.join(root, filename)
                try:
                    entries = self._parse_commentary_file(filepath, catena_source, result)
                    entries_batch.extend(entries)
                    total_processed += len(entries)

                    # Bulk create in batches
                    if len(entries_batch) >= batch_size:
                        CommentaryEntry.objects.bulk_create(entries_batch, ignore_conflicts=True)
                        result.entries_created += len(entries_batch)
                        entries_batch = []
                        if total_processed % 5000 == 0:
                            logger.info(f"  Processed {total_processed:,} entries...")

                except Exception as e:
                    result.errors.append(f"Error processing {filename}: {e}")

            if limit and total_processed >= limit:
                break

        # Flush remaining
        if entries_batch:
            CommentaryEntry.objects.bulk_create(entries_batch, ignore_conflicts=True)
            result.entries_created += len(entries_batch)

        # Update source stats
        catena_source.entry_count = CommentaryEntry.objects.filter(source=catena_source).count()
        catena_source.save(update_fields=["entry_count"])

        result.duration_seconds = time.time() - start
        return result

    def _parse_commentary_file(
        self, filepath: str, source: CommentarySource, result: ImportResult
    ) -> list[CommentaryEntry]:
        """Parse a single Catena Bible JSON file into CommentaryEntry objects."""
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        verse_ref = data.get("verse_reference", "")
        commentaries = data.get("commentaries", [])

        if not commentaries:
            return []

        # Resolve book from file path
        # Path: .../catena_bible/new_testament/pauline_epistles/romans/verses/rom_12_01.json
        # or:   .../catena_bible/old_testament/pentateuch/gn/verses/gn_01_01.json
        filename = os.path.basename(filepath)
        book_part, chapter, verse = self._parse_verse_ref(filename)

        if not chapter or not verse:
            return []

        # Try to find book from the direct parent of "verses/" directory
        # e.g., .../romans/verses/rom_12_01.json → parent of verses/ = "romans"
        verses_dir = os.path.dirname(filepath)  # .../romans/verses
        book_dir = os.path.basename(os.path.dirname(verses_dir))  # "romans" or "gn"
        book = self._resolve_book(book_dir)

        if not book:
            # Try book_part from filename (e.g., "gn" from "gn_01_01.json")
            if book_part:
                book = self._resolve_book(book_part)
        if not book:
            # Try grandparent (category dir like "pentateuch")
            grandparent = os.path.basename(os.path.dirname(os.path.dirname(verses_dir)))
            book = self._resolve_book(grandparent)
        if not book:
            result.books_not_found += 1
            return []

        entries = []
        for idx, commentary in enumerate(commentaries):
            author_name = commentary.get("author", "")
            content = commentary.get("content", "")
            period = commentary.get("period", "")

            if not content or len(content.strip()) < 10:
                result.entries_skipped += 1
                continue

            # Resolve author
            author = self._resolve_author(author_name)

            entries.append(
                CommentaryEntry(
                    source=source,
                    author=author,
                    book=book,
                    chapter=chapter,
                    verse_start=verse,
                    verse_end=verse,
                    original_reference=verse_ref,
                    body_text=content.strip(),
                    extraction_method="beautifulsoup",
                    content_type="full",
                    is_complete=True,
                    original_language="en",
                    word_count=len(content.split()),
                    display_order=idx,
                    confidence_score=0.9,
                )
            )

        return entries

    def _resolve_author(self, dataset_name: str) -> Author | None:
        """Resolve a dataset author name to an Author record."""
        if dataset_name in self._author_cache:
            return self._author_cache[dataset_name]

        # Try exact match
        author = Author.objects.filter(name__iexact=dataset_name).first()
        if not author:
            # Try short_name
            author = Author.objects.filter(short_name__iexact=dataset_name).first()

        self._author_cache[dataset_name] = author
        return author

    def _warm_author_cache(self):
        """Pre-load all authors into cache keyed by dataset_name."""
        if not self.authors_json.exists():
            return

        with open(self.authors_json, encoding="utf-8") as f:
            data = json.load(f)

        # Build dataset_name → canonical_name mapping
        name_map = {}
        for a in data.get("authors", []):
            ds_name = a.get("dataset_name", "")
            canonical = a.get("canonical_name", "")
            if ds_name and canonical:
                name_map[ds_name] = canonical

        # Load all DB authors
        for author in Author.objects.all():
            self._author_cache[author.name] = author
            # Also cache by any dataset_name that maps to this canonical name
            for ds_name, canonical in name_map.items():
                if canonical == author.name:
                    self._author_cache[ds_name] = author

    # ─── Status ───────────────────────────────────────────────

    def get_status(self) -> dict:
        """Get current import status."""
        return {
            "total_authors": Author.objects.count(),
            "total_sources": CommentarySource.objects.count(),
            "total_entries": CommentaryEntry.objects.count(),
            "by_author_type": dict(
                Author.objects.values_list("author_type").annotate(
                    count=__import__("django.db.models", fromlist=["Count"]).Count("id")
                )
            ),
            "sources": list(
                CommentarySource.objects.values("short_code", "name", "entry_count")
            ),
        }
