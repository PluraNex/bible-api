"""
Topic Import Service - Imports topics from V3 dataset into database.

Usage:
    from bible.topics.services.importer import TopicImporter
    
    importer = TopicImporter()
    result = importer.import_all()  # Import all topics
    result = importer.import_letter("A")  # Import only letter A
    result = importer.import_single("abraham")  # Import single topic
"""

import gzip
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from django.db import DatabaseError, IntegrityError, transaction
from django.utils import timezone
from django.utils.text import slugify

from bible.models import (
    CanonicalBook,
    CrossReference,
    Language,
    Theme,
    Topic,
    TopicAspect,
    TopicContent,
    TopicCrossReference,
    TopicDefinition,
    TopicName,
    TopicPipelineMetadata,
    TopicRelation,
    TopicThemeLink,
    TopicVerse,
    Verse,
)
from bible.entities.models import (
    CanonicalEntity,
    EntityNamespace,
    EntityRelationship,
    RelationshipType,
)

logger = logging.getLogger(__name__)


@dataclass
class ImportStats:
    """Statistics for import operation."""

    topics_created: int = 0
    topics_updated: int = 0
    topics_skipped: int = 0
    aspects_created: int = 0
    definitions_created: int = 0
    verses_linked: int = 0
    themes_linked: int = 0
    crossrefs_linked: int = 0
    # Phase 0 processed data
    ai_aspects_created: int = 0
    entities_linked: int = 0
    relationships_created: int = 0
    errors: list = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        return self.topics_created + self.topics_updated + self.topics_skipped


@dataclass
class ImportResult:
    """Result of import operation."""

    success: bool
    stats: ImportStats
    error_message: str | None = None
    duration_seconds: float = 0.0


class TopicImporter:
    """
    Imports topics from V3 JSON dataset into database models.
    
    Features:
    - Idempotent: can be run multiple times safely
    - Incremental: can import by letter or single topic
    - Progress tracking: logs progress during import
    - Error handling: continues on error, collects all errors
    """

    # Path to processed topics from Phase 0 pipeline
    DATASET_PATH = Path("scripts/topical_pipeline/data/topics_v3")
    
    # Book abbreviation mapping (from topic references to OSIS codes)
    BOOK_ABBREV_TO_OSIS = {
        # Old Testament
        "gen": "Gen", "exo": "Exod", "lev": "Lev", "num": "Num", "deu": "Deut",
        "jos": "Josh", "jdg": "Judg", "rut": "Ruth", "1sa": "1Sam", "2sa": "2Sam",
        "1ki": "1Kgs", "2ki": "2Kgs", "1ch": "1Chr", "2ch": "2Chr", "ezr": "Ezra",
        "neh": "Neh", "est": "Esth", "job": "Job", "psa": "Ps", "pro": "Prov",
        "ecc": "Eccl", "sng": "Song", "isa": "Isa", "jer": "Jer", "lam": "Lam",
        "ezk": "Ezek", "dan": "Dan", "hos": "Hos", "jol": "Joel", "amo": "Amos",
        "oba": "Obad", "jon": "Jonah", "mic": "Mic", "nah": "Nah", "hab": "Hab",
        "zep": "Zeph", "hag": "Hag", "zec": "Zech", "mal": "Mal",
        # New Testament
        "mat": "Matt", "mrk": "Mark", "luk": "Luke", "jhn": "John", "act": "Acts",
        "rom": "Rom", "1co": "1Cor", "2co": "2Cor", "gal": "Gal", "eph": "Eph",
        "php": "Phil", "col": "Col", "1th": "1Thess", "2th": "2Thess",
        "1ti": "1Tim", "2ti": "2Tim", "tit": "Titus", "phm": "Phlm", "heb": "Heb",
        "jas": "Jas", "1pe": "1Pet", "2pe": "2Pet", "1jn": "1John", "2jn": "2John",
        "3jn": "3John", "jud": "Jude", "rev": "Rev",
        # Alternative abbreviations
        "psalm": "Ps", "psalms": "Ps", "song": "Song",
    }

    def __init__(self, dataset_path: Path | None = None):
        self.dataset_path = dataset_path or self.DATASET_PATH
        self._book_cache: dict[str, CanonicalBook] = {}
        self._language_cache: dict[str, Language] = {}
        self._theme_cache: dict[str, Theme] = {}
        self._verse_cache: dict[str, Verse] = {}

    def import_all(self, update_existing: bool = False, limit: int | None = None) -> ImportResult:
        """Import all topics from dataset."""
        start_time = datetime.now()
        stats = ImportStats()

        try:
            # Get all letters
            letters = sorted([
                d.name for d in self.dataset_path.iterdir()
                if d.is_dir() and len(d.name) == 1
            ])

            total_files = 0
            for letter in letters:
                letter_dir = self.dataset_path / letter
                total_files += len(list(letter_dir.glob("*.json")))

            logger.info(f"📚 Starting import of {total_files} topics from {len(letters)} letters")

            processed = 0
            for letter in letters:
                letter_stats = self._import_letter(letter, update_existing)
                stats.topics_created += letter_stats.topics_created
                stats.topics_updated += letter_stats.topics_updated
                stats.topics_skipped += letter_stats.topics_skipped
                stats.aspects_created += letter_stats.aspects_created
                stats.definitions_created += letter_stats.definitions_created
                stats.verses_linked += letter_stats.verses_linked
                stats.themes_linked += letter_stats.themes_linked
                stats.crossrefs_linked += letter_stats.crossrefs_linked
                stats.errors.extend(letter_stats.errors)

                processed += letter_stats.total_processed
                if limit and processed >= limit:
                    logger.info(f"⏸️ Reached limit of {limit} topics")
                    break

            duration = (datetime.now() - start_time).total_seconds()
            return ImportResult(success=True, stats=stats, duration_seconds=duration)

        except Exception as e:
            logger.exception(f"Import failed: {e}")
            duration = (datetime.now() - start_time).total_seconds()
            return ImportResult(
                success=False,
                stats=stats,
                error_message=str(e),
                duration_seconds=duration,
            )

    def import_letter(self, letter: str, update_existing: bool = False) -> ImportResult:
        """Import all topics for a specific letter."""
        start_time = datetime.now()
        
        try:
            stats = self._import_letter(letter.upper(), update_existing)
            duration = (datetime.now() - start_time).total_seconds()
            return ImportResult(success=True, stats=stats, duration_seconds=duration)
        except Exception as e:
            logger.exception(f"Import letter {letter} failed: {e}")
            duration = (datetime.now() - start_time).total_seconds()
            return ImportResult(
                success=False,
                stats=ImportStats(errors=[str(e)]),
                error_message=str(e),
                duration_seconds=duration,
            )

    def import_single(self, slug: str, update_existing: bool = True) -> ImportResult:
        """Import a single topic by slug."""
        start_time = datetime.now()
        stats = ImportStats()

        try:
            # Find the topic file
            letter = slug[0].upper()
            topic_file = self.dataset_path / letter / f"{slug}.json"

            if not topic_file.exists():
                return ImportResult(
                    success=False,
                    stats=stats,
                    error_message=f"Topic file not found: {topic_file}",
                )

            with open(topic_file, encoding="utf-8") as f:
                data = json.load(f)

            self._import_topic(data, stats, update_existing)
            duration = (datetime.now() - start_time).total_seconds()
            return ImportResult(success=True, stats=stats, duration_seconds=duration)

        except Exception as e:
            logger.exception(f"Import single topic {slug} failed: {e}")
            duration = (datetime.now() - start_time).total_seconds()
            return ImportResult(
                success=False,
                stats=stats,
                error_message=str(e),
                duration_seconds=duration,
            )

    def _import_letter(self, letter: str, update_existing: bool) -> ImportStats:
        """Import all topics for a letter."""
        stats = ImportStats()
        letter_dir = self.dataset_path / letter

        if not letter_dir.exists():
            logger.warning(f"Letter directory not found: {letter_dir}")
            return stats

        topic_files = sorted(letter_dir.glob("*.json"))
        logger.info(f"📁 Importing letter {letter}: {len(topic_files)} topics")

        for i, topic_file in enumerate(topic_files, 1):
            try:
                with open(topic_file, encoding="utf-8") as f:
                    data = json.load(f)

                self._import_topic(data, stats, update_existing)

                if i % 100 == 0:
                    logger.info(f"   Progress: {i}/{len(topic_files)}")

            except Exception as e:
                error_msg = f"Error importing {topic_file.name}: {e}"
                logger.error(error_msg)
                stats.errors.append(error_msg)

        logger.info(
            f"✅ Letter {letter} complete: "
            f"{stats.topics_created} created, "
            f"{stats.topics_updated} updated, "
            f"{stats.topics_skipped} skipped"
        )
        return stats

    @transaction.atomic
    def _import_topic(self, data: dict, stats: ImportStats, update_existing: bool):
        """Import a single topic with all related data."""
        slug = data.get("slug", "").lower()
        canonical_name = data.get("topic", "")
        
        if not slug or not canonical_name:
            stats.errors.append(f"Invalid topic data: missing slug or topic name")
            return

        # Check if topic exists
        existing = Topic.objects.filter(slug=slug).first()

        if existing and not update_existing:
            stats.topics_skipped += 1
            return

        # Create or update topic
        topic, created = Topic.objects.update_or_create(
            slug=slug,
            defaults=self._build_topic_defaults(data),
        )

        if created:
            stats.topics_created += 1
        else:
            stats.topics_updated += 1

        # Import related data
        self._import_names(topic, data)
        self._import_content(topic, data)
        stats.definitions_created += self._import_definitions(topic, data)
        stats.aspects_created += self._import_aspects(topic, data)
        stats.verses_linked += self._import_verses(topic, data)
        stats.themes_linked += self._import_themes(topic, data)
        stats.crossrefs_linked += self._import_crossrefs(topic, data)
        self._import_pipeline_metadata(topic, data)

    def _build_topic_defaults(self, data: dict) -> dict:
        """Build defaults dict for Topic model."""
        stats = data.get("stats", {})
        ai_enrichment = data.get("ai_enrichment", {})

        # Determine topic type from entity_links
        topic_type = Topic.TopicType.CONCEPT
        entity_links = data.get("entity_links", [])
        if entity_links:
            namespace = entity_links[0].get("namespace", "").upper()
            if namespace == "PERSON":
                topic_type = Topic.TopicType.PERSON
            elif namespace == "PLACE":
                topic_type = Topic.TopicType.PLACE
            elif namespace == "OBJECT":
                topic_type = Topic.TopicType.OBJECT
            elif namespace == "EVENT":
                topic_type = Topic.TopicType.EVENT

        return {
            "canonical_id": f"UNIFIED:{data.get('slug', '')}",
            "canonical_name": data.get("topic", ""),
            "name_normalized": data.get("slug", "").lower(),
            "topic_type": topic_type,
            "primary_source": data.get("sources", ["NAV"])[0] if data.get("sources") else "NAV",
            "available_sources": data.get("sources", []),
            "total_verses": stats.get("total_verses", 0),
            "ot_refs": stats.get("ot_refs", 0),
            "nt_refs": stats.get("nt_refs", 0),
            "books_count": len(stats.get("books", [])) if isinstance(stats.get("books"), list) else 0,
            "aspects_count": stats.get("entries_count", 0),
            "ai_enriched": bool(ai_enrichment),
            "ai_model": ai_enrichment.get("model", ""),
            "ai_confidence": ai_enrichment.get("confidence", 0.0),
            "ai_enriched_at": self._parse_datetime(ai_enrichment.get("generated_at")),
            "ai_run_id": ai_enrichment.get("run_id", ""),
        }

    def _import_names(self, topic: Topic, data: dict):
        """Import topic names (i18n)."""
        en_lang = self._get_language("en")
        pt_lang = self._get_language("pt")

        # English name (canonical)
        TopicName.objects.update_or_create(
            topic=topic,
            language=en_lang,
            defaults={
                "name": data.get("topic", ""),
                "aliases": data.get("aliases", []),
            },
        )

        # Portuguese name if available in AI enrichment
        ai_enrichment = data.get("ai_enrichment", {})
        if ai_enrichment and pt_lang:
            # AI enrichment summary is in Portuguese
            TopicName.objects.update_or_create(
                topic=topic,
                language=pt_lang,
                defaults={
                    "name": data.get("topic", ""),  # Keep canonical for now
                    "aliases": [],
                },
            )

    def _import_content(self, topic: Topic, data: dict):
        """Import topic content (i18n)."""
        ai_enrichment = data.get("ai_enrichment", {})
        if not ai_enrichment:
            return

        pt_lang = self._get_language("pt")
        if not pt_lang:
            return

        TopicContent.objects.update_or_create(
            topic=topic,
            language=pt_lang,
            defaults={
                "summary": ai_enrichment.get("summary", ""),
                "outline": ai_enrichment.get("outline", []),
                "key_concepts": ai_enrichment.get("key_concepts", []),
                "theological_significance": ai_enrichment.get("theological_significance", ""),
            },
        )

    def _import_definitions(self, topic: Topic, data: dict) -> int:
        """Import dictionary definitions."""
        definitions = data.get("definitions", [])
        count = 0

        for defn in definitions:
            source = defn.get("source", "")
            text = defn.get("text", "")
            
            if not source or not text:
                continue

            TopicDefinition.objects.update_or_create(
                topic=topic,
                source=source,
                defaults={
                    "text": text,
                    "extracted_refs": defn.get("extracted_refs", []),
                    "processed_at": timezone.now(),
                },
            )
            count += 1

        return count

    def _import_aspects(self, topic: Topic, data: dict) -> int:
        """Import topic aspects (reference_groups)."""
        reference_groups = data.get("reference_groups", [])
        count = 0

        # Clear existing aspects for clean import
        topic.aspects.all().delete()

        for order, group in enumerate(reference_groups):
            label = group.get("name", "")
            if not label:
                continue

            # Extract raw references
            raw_refs = group.get("references", [])

            # Calculate stats from references
            ot_refs = sum(1 for ref in raw_refs if self._is_ot_reference(ref))
            nt_refs = len(raw_refs) - ot_refs

            # Truncate very long labels (max 500 chars in DB)
            canonical_label = label[:500] if len(label) > 500 else label

            aspect = TopicAspect.objects.create(
                topic=topic,
                canonical_label=canonical_label,
                slug=slugify(label[:100]),
                order=order,
                raw_references=raw_refs,
                verse_count=len(raw_refs),
                ot_refs=ot_refs,
                nt_refs=nt_refs,
                source=data.get("sources", ["NAV"])[0] if data.get("sources") else "NAV",
            )

            # Create English label (truncated to fit DB constraint)
            en_lang = self._get_language("en")
            if en_lang:
                TopicAspectLabel.objects.create(
                    aspect=aspect,
                    language=en_lang,
                    label=label[:500] if len(label) > 500 else label,
                )

            count += 1

            # Handle sub_groups recursively if needed
            for sub_order, sub_group in enumerate(group.get("sub_groups", [])):
                sub_label = sub_group.get("name", "")
                if sub_label:
                    # Truncate combined label if too long
                    combined_label = f"{label} > {sub_label}"
                    if len(combined_label) > 500:
                        combined_label = combined_label[:500]

                    sub_aspect = TopicAspect.objects.create(
                        topic=topic,
                        canonical_label=combined_label,
                        slug=slugify(f"{label[:50]}-{sub_label[:50]}"),
                        order=order * 1000 + sub_order,
                        raw_references=sub_group.get("references", []),
                        verse_count=len(sub_group.get("references", [])),
                        source=data.get("sources", ["NAV"])[0] if data.get("sources") else "NAV",
                    )
                    count += 1

        return count

    def _import_verses(self, topic: Topic, data: dict) -> int:
        """Import topic-verse links."""
        biblical_refs = data.get("biblical_references", [])
        count = 0

        # Clear existing links for clean import
        topic.verse_links.all().delete()

        for ref in biblical_refs:
            book_abbrev = ref.get("book_abbrev", "").lower()
            chapter = ref.get("chapter")
            verses = ref.get("verses", [])

            if not book_abbrev or not chapter or not verses:
                continue

            osis_code = self.BOOK_ABBREV_TO_OSIS.get(book_abbrev)
            if not osis_code:
                continue

            book = self._get_book(osis_code)
            if not book:
                continue

            for verse_num in verses:
                verse = self._get_verse(book, chapter, verse_num)
                if verse:
                    TopicVerse.objects.get_or_create(
                        topic=topic,
                        verse=verse,
                        defaults={"relevance_score": 1.0},
                    )
                    count += 1

        return count

    def _import_themes(self, topic: Topic, data: dict) -> int:
        """Import AI-extracted theme links."""
        ai_themes = data.get("ai_themes_normalized", [])
        count = 0

        # Clear existing theme links for clean import
        topic.theme_links.all().delete()

        for theme_data in ai_themes:
            label_original = theme_data.get("label_original", "")
            # Handle explicit None values in JSON (proposal_id can be null)
            proposal_id = theme_data.get("proposal_id") or ""
            theme_id_str = theme_data.get("theme_id") or ""

            if not label_original:
                continue

            # Try to find existing theme by theme_id or create placeholder
            theme = None
            if theme_id_str and theme_id_str.startswith("THEME:"):
                # Try to find by canonical ID
                theme_slug = theme_id_str.replace("THEME:", "")
                theme = Theme.objects.filter(name__iexact=theme_slug).first()
            
            if not theme:
                theme = self._get_or_create_theme(label_original)
            
            if not theme:
                continue

            TopicThemeLink.objects.create(
                topic=topic,
                theme=theme,
                proposal_id=proposal_id,
                label_original=label_original,
                label_en=label_original,  # Same for now
                label_normalized=slugify(label_original),
                source=theme_data.get("source") or "ai_enrichment",
                confidence=0.95,  # Default high confidence for AI themes
            )
            count += 1

        return count

    def _import_crossrefs(self, topic: Topic, data: dict) -> int:
        """Import cross-reference links."""
        crossref_network = data.get("cross_reference_network", {})
        count = 0

        if not crossref_network:
            return 0

        # Clear existing for clean import
        topic.cross_references.all().delete()

        for from_ref, xrefs in crossref_network.items():
            if not isinstance(xrefs, list):
                continue

            for xref_data in xrefs[:10]:  # Limit to top 10 per source verse
                to_verse = xref_data.get("to_verse", "")
                score = xref_data.get("score", 0)

                if not to_verse or score < 5:  # Skip weak references
                    continue

                # Try to find matching CrossReference in DB
                crossref = self._find_crossref(from_ref, to_verse)
                if crossref:
                    TopicCrossReference.objects.get_or_create(
                        topic=topic,
                        cross_reference=crossref,
                        defaults={"relevance_score": min(score / 10.0, 1.0)},
                    )
                    count += 1

        return count

    def _import_pipeline_metadata(self, topic: Topic, data: dict):
        """Import pipeline processing metadata."""
        phase1 = data.get("phase1_discovery", {})

        # Compress raw JSON for storage
        raw_json = json.dumps(data, ensure_ascii=False)
        compressed = gzip.compress(raw_json.encode("utf-8"))

        TopicPipelineMetadata.objects.update_or_create(
            topic=topic,
            defaults={
                "phase0_processed_at": self._parse_datetime(data.get("metadata", {}).get("created_at")),
                "phase1_processed_at": self._parse_datetime(phase1.get("processed_at")),
                "phase1_summary": phase1.get("summary", {}),
                "phase1_results": phase1.get("results", []),
                "raw_json_backup": compressed,
                "pipeline_version": data.get("version", "3.0.0"),
            },
        )

    # === Helper Methods ===

    def _get_language(self, code: str) -> Language | None:
        """Get language from cache or DB."""
        if code not in self._language_cache:
            try:
                self._language_cache[code] = Language.objects.get(code=code)
            except Language.DoesNotExist:
                # Try with region
                try:
                    self._language_cache[code] = Language.objects.get(code__startswith=code)
                except Language.DoesNotExist:
                    return None
        return self._language_cache.get(code)

    def _get_book(self, osis_code: str) -> CanonicalBook | None:
        """Get book from cache or DB."""
        if osis_code not in self._book_cache:
            try:
                self._book_cache[osis_code] = CanonicalBook.objects.get(osis_code=osis_code)
            except CanonicalBook.DoesNotExist:
                return None
        return self._book_cache.get(osis_code)

    def _get_verse(self, book: CanonicalBook, chapter: int, verse: int) -> Verse | None:
        """Get verse from cache or DB."""
        cache_key = f"{book.osis_code}.{chapter}.{verse}"
        if cache_key not in self._verse_cache:
            try:
                # Get any verse for this reference (any version)
                self._verse_cache[cache_key] = Verse.objects.filter(
                    book__osis_code=book.osis_code,
                    chapter=chapter,
                    verse=verse,
                ).first()
            except (DatabaseError, IntegrityError, ValueError):
                return None
        return self._verse_cache.get(cache_key)

    def _get_or_create_theme(self, label: str) -> Theme | None:
        """Get or create a theme."""
        normalized = slugify(label)
        if normalized not in self._theme_cache:
            theme, _ = Theme.objects.get_or_create(
                name=label,
                defaults={
                    "description": "",
                },
            )
            self._theme_cache[normalized] = theme
        return self._theme_cache.get(normalized)

    def _find_crossref(self, from_ref: str, to_ref: str) -> CrossReference | None:
        """Find a CrossReference matching the refs."""
        # Parse from_ref (e.g., "Genesis 12:1")
        try:
            from_parts = from_ref.replace(":", " ").split()
            if len(from_parts) < 3:
                return None

            from_book_name = from_parts[0]
            from_chapter = int(from_parts[1])
            from_verse = int(from_parts[2])

            # Parse to_ref (e.g., "GEN.12.1")
            to_parts = to_ref.split(".")
            if len(to_parts) < 3:
                return None

            to_book_abbrev = to_parts[0].lower()
            to_chapter = int(to_parts[1])
            to_verse = int(to_parts[2])

            to_osis = self.BOOK_ABBREV_TO_OSIS.get(to_book_abbrev)
            if not to_osis:
                return None

            # Find matching CrossReference
            return CrossReference.objects.filter(
                from_chapter=from_chapter,
                from_verse=from_verse,
                to_chapter=to_chapter,
                to_verse_start=to_verse,
                to_book__osis_code=to_osis,
            ).first()

        except (ValueError, IndexError):
            return None

    def _is_ot_reference(self, ref: str) -> bool:
        """Check if reference is Old Testament."""
        ot_books = {
            "Gen", "Exod", "Lev", "Num", "Deut", "Josh", "Judg", "Ruth",
            "1Sam", "2Sam", "1Kgs", "2Kgs", "1Chr", "2Chr", "Ezra", "Neh",
            "Esth", "Job", "Ps", "Prov", "Eccl", "Song", "Isa", "Jer",
            "Lam", "Ezek", "Dan", "Hos", "Joel", "Amos", "Obad", "Jonah",
            "Mic", "Nah", "Hab", "Zeph", "Hag", "Zech", "Mal",
        }
        # Parse book from reference like "Gen 1:1" or "Genesis 1:1"
        parts = ref.split()
        if parts:
            book = parts[0]
            # Check both abbreviation and full name
            return book in ot_books or any(
                book.lower().startswith(ob.lower()[:3]) for ob in ot_books
            )
        return False

    def _parse_datetime(self, dt_str: str | None) -> datetime | None:
        """Parse datetime string to datetime object."""
        if not dt_str:
            return None
        try:
            # Handle ISO format with timezone
            if "T" in dt_str:
                dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                # Ensure timezone-aware
                if dt.tzinfo is None:
                    from django.utils import timezone as tz
                    dt = tz.make_aware(dt)
                return dt
            return None
        except (ValueError, TypeError):
            return None

    # === Phase 0 Processed Data Update Methods ===

    def update_from_processed(
        self,
        limit: int | None = None,
        letter: str | None = None,
    ) -> ImportResult:
        """
        Update existing topics with Phase 0 processed data.
        
        This adds:
        - ai_discovered_aspects → TopicAspect with source='ai_discovery'
        - ai_entities → Link to CanonicalEntity (create if needed)
        - ai_relationships → EntityRelationship with source_topic
        - ai_reference_groups → TopicAspect with parsed references
        
        Args:
            limit: Maximum number of topics to update
            letter: Specific letter to update (e.g., 'A')
        """
        start_time = datetime.now()
        stats = ImportStats()
        
        try:
            # Determine which directories to process
            if letter:
                letters = [letter.upper()]
            else:
                letters = sorted([
                    d.name for d in self.dataset_path.iterdir()
                    if d.is_dir() and len(d.name) == 1
                ])
            
            total_files = 0
            for let in letters:
                letter_dir = self.dataset_path / let
                if letter_dir.exists():
                    total_files += len(list(letter_dir.glob("*.json")))
            
            logger.info(f"🔄 Updating {total_files} topics with Phase 0 data from {len(letters)} letters")
            
            processed = 0
            for let in letters:
                letter_stats = self._update_letter_from_processed(let)
                stats.topics_updated += letter_stats.topics_updated
                stats.topics_skipped += letter_stats.topics_skipped
                stats.ai_aspects_created += letter_stats.ai_aspects_created
                stats.entities_linked += letter_stats.entities_linked
                stats.relationships_created += letter_stats.relationships_created
                stats.errors.extend(letter_stats.errors)
                
                processed += letter_stats.topics_updated + letter_stats.topics_skipped
                if limit and processed >= limit:
                    logger.info(f"⏸️ Reached limit of {limit} topics")
                    break
            
            duration = (datetime.now() - start_time).total_seconds()
            return ImportResult(success=True, stats=stats, duration_seconds=duration)
            
        except Exception as e:
            logger.exception(f"Update from processed failed: {e}")
            duration = (datetime.now() - start_time).total_seconds()
            return ImportResult(
                success=False,
                stats=stats,
                error_message=str(e),
                duration_seconds=duration,
            )

    def _update_letter_from_processed(self, letter: str) -> ImportStats:
        """Update all topics for a letter with Phase 0 data."""
        stats = ImportStats()
        letter_dir = self.dataset_path / letter
        
        if not letter_dir.exists():
            logger.warning(f"Letter directory not found: {letter_dir}")
            return stats
        
        topic_files = sorted(letter_dir.glob("*.json"))
        logger.info(f"📁 Updating letter {letter}: {len(topic_files)} topics")
        
        for i, topic_file in enumerate(topic_files, 1):
            try:
                with open(topic_file, encoding="utf-8") as f:
                    data = json.load(f)
                
                self._update_topic_from_processed(data, stats)
                
                if i % 100 == 0:
                    logger.info(f"   Progress: {i}/{len(topic_files)}")
                    
            except Exception as e:
                error_msg = f"Error updating {topic_file.name}: {e}"
                logger.error(error_msg)
                stats.errors.append(error_msg)
        
        logger.info(
            f"✅ Letter {letter} update complete: "
            f"{stats.topics_updated} updated, "
            f"{stats.topics_skipped} skipped, "
            f"{stats.ai_aspects_created} AI aspects, "
            f"{stats.entities_linked} entities linked, "
            f"{stats.relationships_created} relationships"
        )
        return stats

    @transaction.atomic
    def _update_topic_from_processed(self, data: dict, stats: ImportStats):
        """Update a single topic with Phase 0 processed data."""
        slug = data.get("slug", "").lower()
        
        if not slug:
            stats.errors.append("Invalid topic data: missing slug")
            return
        
        # Find existing topic
        topic = Topic.objects.filter(slug=slug).first()
        if not topic:
            stats.topics_skipped += 1
            logger.debug(f"Topic not found in DB: {slug}")
            return
        
        # Update with Phase 0 data
        ai_aspects = data.get("ai_discovered_aspects", [])
        ai_entities = data.get("ai_entities", [])
        ai_relationships = data.get("ai_relationships", [])
        ai_reference_groups = data.get("ai_reference_groups", [])
        
        # Import AI-discovered aspects
        aspects_created = self._import_ai_discovered_aspects(topic, ai_aspects)
        stats.ai_aspects_created += aspects_created
        
        # Import AI reference groups as aspects
        ref_aspects_created = self._import_ai_reference_groups(topic, ai_reference_groups)
        stats.ai_aspects_created += ref_aspects_created
        
        # Link entities
        entities_linked = self._link_ai_entities(topic, ai_entities)
        stats.entities_linked += entities_linked
        
        # Create relationships
        relationships_created = self._create_ai_relationships(topic, ai_relationships)
        stats.relationships_created += relationships_created
        
        # Update topic metadata
        if ai_aspects or ai_entities or ai_relationships or ai_reference_groups:
            topic.ai_enriched = True
            topic.ai_enriched_at = timezone.now()
            topic.save(update_fields=["ai_enriched", "ai_enriched_at", "updated_at"])
        
        stats.topics_updated += 1

    def _import_ai_discovered_aspects(self, topic: Topic, ai_aspects: list) -> int:
        """
        Import AI-discovered aspects as TopicAspect with source='AI'.
        
        Structure:
        {
            "label": "Aspect Label",
            "references": ["Gen.12.1", "Gen.15.6"],
            "rationale": "Why this aspect is relevant",
            "source": "ai_discovery"
        }
        """
        count = 0
        
        for aspect_data in ai_aspects:
            label = aspect_data.get("label", "").strip()
            if not label:
                continue
            
            references = aspect_data.get("references", [])
            
            # Create aspect with source=AI (max 10 chars)
            aspect, created = TopicAspect.objects.update_or_create(
                topic=topic,
                canonical_label=label,
                source="AI",
                defaults={
                    "verse_count": len(references),
                    "raw_references": references,
                },
            )
            
            if created:
                count += 1
                
                # Link verses
                for ref in references:
                    self._link_aspect_verse(aspect, ref)
        
        return count

    def _import_ai_reference_groups(self, topic: Topic, reference_groups: list) -> int:
        """
        Import AI reference groups as TopicAspect entries.
        
        Structure:
        {
            "name": "Aspect name",
            "ai_group_id": "grp:topic:aspect",
            "source": "ai_discovery",
            "source_verses": ["Exodus 4:30", "Exodus 7:2"],
            "references": [{"book": "Exodus", "chapter": 4, "verses": [30], "raw": "Exodus 4:30"}],
            "quality": {"verse_count": 2, "confidence": 0.8, "relevance": "direct"},
            ...
        }
        """
        count = 0
        
        for ref_data in reference_groups:
            name = ref_data.get("name", "").strip()
            if not name:
                continue
            
            # Get quality info - it's a dict now
            quality_info = ref_data.get("quality", {})
            confidence = quality_info.get("confidence", 0.5) if isinstance(quality_info, dict) else 0.5
            
            # Skip low confidence groups
            if confidence < 0.5:
                continue
            
            # Collect source verses (raw references)
            source_verses = ref_data.get("source_verses", [])
            
            aspect, created = TopicAspect.objects.update_or_create(
                topic=topic,
                canonical_label=name,
                source="AI_REF",  # max 10 chars
                defaults={
                    "verse_count": len(source_verses),
                    "raw_references": source_verses,
                },
            )
            
            if created:
                count += 1
                
                # Link verses from parsed references
                references = ref_data.get("references", [])
                for ref in references:
                    if isinstance(ref, dict):
                        # Parse structured reference
                        book = ref.get("book", "")
                        chapter = ref.get("chapter", 0)
                        verses = ref.get("verses", [])
                        for verse_num in verses:
                            self._link_aspect_verse_structured(aspect, book, chapter, verse_num)
        
        return count

    def _link_aspect_verse_structured(self, aspect: TopicAspect, book_name: str, chapter: int, verse_num: int):
        """Link a verse to an aspect by structured reference."""
        try:
            # Map common book names to OSIS codes
            book_name_lower = book_name.lower()
            osis = self._map_book_name_to_osis(book_name_lower)
            if not osis:
                return
            
            book = self._get_book(osis)
            if not book:
                return
            
            verse = self._get_verse(book, chapter, verse_num)
            if verse:
                aspect.verses.add(verse)
                
        except (ValueError, IndexError):
            pass

    def _map_book_name_to_osis(self, book_name: str) -> str | None:
        """Map full book name to OSIS code."""
        name_map = {
            "genesis": "Gen",
            "exodus": "Exod",
            "leviticus": "Lev",
            "numbers": "Num",
            "deuteronomy": "Deut",
            "joshua": "Josh",
            "judges": "Judg",
            "ruth": "Ruth",
            "1 samuel": "1Sam",
            "2 samuel": "2Sam",
            "1 kings": "1Kgs",
            "2 kings": "2Kgs",
            "1 chronicles": "1Chr",
            "2 chronicles": "2Chr",
            "ezra": "Ezra",
            "nehemiah": "Neh",
            "esther": "Esth",
            "job": "Job",
            "psalms": "Ps",
            "psalm": "Ps",
            "proverbs": "Prov",
            "ecclesiastes": "Eccl",
            "song of solomon": "Song",
            "song of songs": "Song",
            "isaiah": "Isa",
            "jeremiah": "Jer",
            "lamentations": "Lam",
            "ezekiel": "Ezek",
            "daniel": "Dan",
            "hosea": "Hos",
            "joel": "Joel",
            "amos": "Amos",
            "obadiah": "Obad",
            "jonah": "Jonah",
            "micah": "Mic",
            "nahum": "Nah",
            "habakkuk": "Hab",
            "zephaniah": "Zeph",
            "haggai": "Hag",
            "zechariah": "Zech",
            "malachi": "Mal",
            "matthew": "Matt",
            "mark": "Mark",
            "luke": "Luke",
            "john": "John",
            "acts": "Acts",
            "romans": "Rom",
            "1 corinthians": "1Cor",
            "2 corinthians": "2Cor",
            "galatians": "Gal",
            "ephesians": "Eph",
            "philippians": "Phil",
            "colossians": "Col",
            "1 thessalonians": "1Thess",
            "2 thessalonians": "2Thess",
            "1 timothy": "1Tim",
            "2 timothy": "2Tim",
            "titus": "Titus",
            "philemon": "Phlm",
            "hebrews": "Heb",
            "james": "Jas",
            "1 peter": "1Pet",
            "2 peter": "2Pet",
            "1 john": "1John",
            "2 john": "2John",
            "3 john": "3John",
            "jude": "Jude",
            "revelation": "Rev",
        }
        return name_map.get(book_name.lower())

    def _link_aspect_verse(self, aspect: TopicAspect, ref: str):
        """Link a verse to an aspect by parsed reference (e.g., 'GEN.12.1')."""
        try:
            parts = ref.split(".")
            if len(parts) < 3:
                return
            
            book_abbrev = parts[0].lower()
            chapter = int(parts[1])
            verse_num = int(parts[2].split("-")[0])  # Handle verse ranges
            
            osis = self.BOOK_ABBREV_TO_OSIS.get(book_abbrev)
            if not osis:
                return
            
            book = self._get_book(osis)
            if not book:
                return
            
            verse = self._get_verse(book, chapter, verse_num)
            if verse:
                aspect.verses.add(verse)
                
        except (ValueError, IndexError):
            pass

    def _link_ai_entities(self, topic: Topic, ai_entities: list) -> int:
        """
        Link AI-extracted entities to CanonicalEntity.
        
        Structure:
        {
            "name": "Abraão",
            "type": "PERSON",
            "canonical_id": null,  # May be set if matched
            "context": "Pai da fé..."
        }
        """
        count = 0
        
        for entity_data in ai_entities:
            name = entity_data.get("name", "").strip()
            entity_type = entity_data.get("type", "CONCEPT")
            canonical_id = entity_data.get("canonical_id")
            
            if not name:
                continue
            
            # Try to find existing entity
            entity = None
            
            # First by canonical_id if provided
            if canonical_id:
                entity = CanonicalEntity.objects.filter(canonical_id=canonical_id).first()
            
            # Then by name and namespace
            if not entity:
                namespace = self._map_entity_type_to_namespace(entity_type)
                entity = CanonicalEntity.objects.filter(
                    primary_name__iexact=name,
                    namespace=namespace,
                ).first()
            
            if entity:
                # Update source_topics to include this topic
                source_topics = entity.source_topics or []
                if topic.slug not in source_topics:
                    source_topics.append(topic.slug)
                    entity.source_topics = source_topics
                    entity.save(update_fields=["source_topics", "updated_at"])
                count += 1
            else:
                # Create new entity from AI data
                namespace = self._map_entity_type_to_namespace(entity_type)
                new_id = f"{namespace[:3].upper()}:{slugify(name)}"
                
                entity, created = CanonicalEntity.objects.get_or_create(
                    canonical_id=new_id,
                    defaults={
                        "namespace": namespace,
                        "primary_name": name,
                        "description": entity_data.get("context", ""),
                        "source_topics": [topic.slug],
                        "ai_enriched": True,
                        "ai_enriched_at": timezone.now(),
                    },
                )
                if created:
                    count += 1
        
        return count

    def _create_ai_relationships(self, topic: Topic, ai_relationships: list) -> int:
        """
        Create EntityRelationship from AI-extracted relationships.
        
        Structure:
        {
            "target": "Terá",
            "type": "PARENT_OF",
            "description": "Pai de Abraão",
            "target_type": "PERSON",
            "source": "ai_discovery"
        }
        """
        count = 0
        
        for rel_data in ai_relationships:
            target_name = rel_data.get("target", "").strip()
            rel_type = rel_data.get("type", "ASSOCIATED_WITH")
            target_type = rel_data.get("target_type", "CONCEPT")
            description = rel_data.get("description", "")
            
            if not target_name:
                continue
            
            # Find source entity (from topic's linked entities)
            # Use the primary entity of the topic if available
            source_entity = None
            
            # Try to find entity that matches the topic
            source_entity = CanonicalEntity.objects.filter(
                source_topics__contains=[topic.slug]
            ).first()
            
            if not source_entity:
                # Create a placeholder entity for the topic
                namespace = self._get_topic_namespace(topic)
                source_id = f"{namespace[:3].upper()}:{topic.slug}"
                
                source_entity, _ = CanonicalEntity.objects.get_or_create(
                    canonical_id=source_id,
                    defaults={
                        "namespace": namespace,
                        "primary_name": topic.canonical_name,
                        "source_topics": [topic.slug],
                    },
                )
            
            # Find or create target entity
            target_namespace = self._map_entity_type_to_namespace(target_type)
            target_id = f"{target_namespace[:3].upper()}:{slugify(target_name)}"
            
            target_entity, _ = CanonicalEntity.objects.get_or_create(
                canonical_id=target_id,
                defaults={
                    "namespace": target_namespace,
                    "primary_name": target_name,
                },
            )
            
            # Map relationship type
            relationship_type = self._map_relationship_type(rel_type)
            
            # Create relationship
            _, created = EntityRelationship.objects.get_or_create(
                source=source_entity,
                target=target_entity,
                relationship_type=relationship_type,
                defaults={
                    "description": description,
                    "source_topic": topic.slug,
                    "ai_enriched": True,
                },
            )
            
            if created:
                count += 1
        
        return count

    def _map_entity_type_to_namespace(self, entity_type: str) -> str:
        """Map entity type string to EntityNamespace."""
        type_map = {
            "PERSON": EntityNamespace.PERSON,
            "DEITY": EntityNamespace.DEITY,
            "PLACE": EntityNamespace.PLACE,
            "ANGEL": EntityNamespace.ANGEL,
            "CONCEPT": EntityNamespace.CONCEPT,
            "OBJECT": EntityNamespace.OBJECT,
            "EVENT": EntityNamespace.EVENT,
            "LITERARY_WORK": EntityNamespace.LITERARY_WORK,
            "GROUP": EntityNamespace.GROUP,
            "CREATURE": EntityNamespace.CREATURE,
        }
        return type_map.get(entity_type.upper(), EntityNamespace.CONCEPT)

    def _get_topic_namespace(self, topic: Topic) -> str:
        """Get namespace from topic type."""
        type_map = {
            Topic.TopicType.PERSON: EntityNamespace.PERSON,
            Topic.TopicType.PLACE: EntityNamespace.PLACE,
            Topic.TopicType.OBJECT: EntityNamespace.OBJECT,
            Topic.TopicType.EVENT: EntityNamespace.EVENT,
            Topic.TopicType.CONCEPT: EntityNamespace.CONCEPT,
        }
        return type_map.get(topic.topic_type, EntityNamespace.CONCEPT)

    def _map_relationship_type(self, rel_type: str) -> str:
        """Map relationship type string to RelationshipType."""
        type_map = {
            "PARENT_OF": RelationshipType.PARENT_OF,
            "CHILD_OF": RelationshipType.CHILD_OF,
            "SIBLING": RelationshipType.SIBLING,
            "SPOUSE_OF": RelationshipType.SPOUSE_OF,
            "ANCESTOR_OF": RelationshipType.ANCESTOR_OF,
            "DESCENDANT_OF": RelationshipType.DESCENDANT_OF,
            "KING_OF": RelationshipType.KING_OF,
            "SUBJECT_OF": RelationshipType.SUBJECT_OF,
            "SERVANT_OF": RelationshipType.SERVANT_OF,
            "MASTER_OF": RelationshipType.MASTER_OF,
            "LEADER_OF": RelationshipType.LEADER_OF,
            "MEMBER_OF": RelationshipType.MEMBER_OF,
            "DISCIPLE_OF": RelationshipType.DISCIPLE_OF,
            "TEACHER_OF": RelationshipType.TEACHER_OF,
            "SUCCESSOR_OF": RelationshipType.SUCCESSOR_OF,
            "PREDECESSOR_OF": RelationshipType.PREDECESSOR_OF,
            "ANOINTED_BY": RelationshipType.ANOINTED_BY,
            "ENEMY_OF": RelationshipType.ENEMY_OF,
            "ALLY_OF": RelationshipType.ALLY_OF,
            "BETRAYED_BY": RelationshipType.BETRAYED_BY,
            "KILLED_BY": RelationshipType.KILLED_BY,
            "PERSECUTOR_OF": RelationshipType.PERSECUTOR_OF,
            "BORN_IN": RelationshipType.BORN_IN,
            "DIED_IN": RelationshipType.DIED_IN,
            "LIVED_IN": RelationshipType.LIVED_IN,
            "TRAVELED_TO": RelationshipType.TRAVELED_TO,
            "EXILED_TO": RelationshipType.EXILED_TO,
            "CONQUERED": RelationshipType.CONQUERED,
            "FOUNDED": RelationshipType.FOUNDED,
            "BUILT": RelationshipType.BUILT,
            "TYPE_OF": RelationshipType.TYPE_OF,
            "ANTITYPE_OF": RelationshipType.ANTITYPE_OF,
            "FORESHADOWS": RelationshipType.FORESHADOWS,
            "FULFILLS": RelationshipType.FULFILLS,
            "PARALLELS": RelationshipType.PARALLELS,
            "CONTRASTS": RelationshipType.CONTRASTS,
            "ASSOCIATED_WITH": RelationshipType.ASSOCIATED_WITH,
            "PART_OF": RelationshipType.PART_OF,
            "CONTEMPORARY_OF": RelationshipType.CONTEMPORARY_OF,
        }
        return type_map.get(rel_type.upper(), RelationshipType.ASSOCIATED_WITH)
