"""
Topic Import Service - Imports topics from JSON files to database.

This service handles the complete import of topics from the JSON files
in scripts/topical_pipeline/data/topics_v3/ to the database models.
"""

import gzip
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from django.db import transaction
from django.utils.text import slugify

from bible.models import Language, Theme, Verse
from bible.models.topics import (
    Topic,
    TopicAspect,
    TopicAspectLabel,
    TopicContent,
    TopicCrossReference,
    TopicDefinition,
    TopicName,
    TopicPipelineMetadata,
    TopicRelation,
    TopicThemeLink,
    TopicVerse,
)

logger = logging.getLogger(__name__)


@dataclass
class ImportStats:
    """Statistics for the import process."""

    topics_created: int = 0
    topics_updated: int = 0
    topics_skipped: int = 0
    aspects_created: int = 0
    definitions_created: int = 0
    theme_links_created: int = 0
    cross_refs_created: int = 0
    relations_created: int = 0
    errors: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "topics_created": self.topics_created,
            "topics_updated": self.topics_updated,
            "topics_skipped": self.topics_skipped,
            "aspects_created": self.aspects_created,
            "definitions_created": self.definitions_created,
            "theme_links_created": self.theme_links_created,
            "cross_refs_created": self.cross_refs_created,
            "relations_created": self.relations_created,
            "total_topics": self.topics_created + self.topics_updated,
            "errors_count": len(self.errors),
        }


class TopicImportService:
    """Service to import topics from JSON files to database."""

    def __init__(
        self,
        topics_dir: str = "scripts/topical_pipeline/data/topics_v3",
        dry_run: bool = False,
        update_existing: bool = False,
    ):
        self.topics_dir = Path(topics_dir)
        self.dry_run = dry_run
        self.update_existing = update_existing
        self.stats = ImportStats()

        # Cache for lookups
        self._language_cache: dict[str, Language] = {}
        self._theme_cache: dict[str, Theme] = {}
        self._verse_cache: dict[str, Verse] = {}

    def get_language(self, code: str) -> Language | None:
        """Get or cache a language by code."""
        if code not in self._language_cache:
            try:
                self._language_cache[code] = Language.objects.get(code=code)
            except Language.DoesNotExist:
                logger.warning(f"Language not found: {code}")
                return None
        return self._language_cache[code]

    def get_or_create_theme(self, label_normalized: str, label_original: str) -> Theme | None:
        """Get or create a theme by normalized label."""
        if label_normalized not in self._theme_cache:
            theme, created = Theme.objects.get_or_create(
                name_normalized=label_normalized,
                defaults={
                    "name": label_original,
                    "slug": slugify(label_normalized),
                },
            )
            self._theme_cache[label_normalized] = theme
        return self._theme_cache[label_normalized]

    def get_json_files(self, letter: str | None = None, limit: int | None = None) -> list[Path]:
        """Get all JSON files from the topics directory."""
        if not self.topics_dir.exists():
            raise FileNotFoundError(f"Topics directory not found: {self.topics_dir}")

        files = []
        if letter:
            letter_dir = self.topics_dir / letter.upper()
            if letter_dir.exists():
                files = list(letter_dir.glob("*.json"))
        else:
            for letter_dir in sorted(self.topics_dir.iterdir()):
                if letter_dir.is_dir() and len(letter_dir.name) == 1:
                    files.extend(letter_dir.glob("*.json"))

        files = sorted(files)
        if limit:
            files = files[:limit]

        return files

    def import_all(
        self,
        letter: str | None = None,
        limit: int | None = None,
    ) -> ImportStats:
        """Import all topics from JSON files."""
        files = self.get_json_files(letter=letter, limit=limit)
        total = len(files)

        logger.info(f"Found {total} topic files to import")

        for i, file_path in enumerate(files, 1):
            try:
                if i % 50 == 0:
                    logger.info(f"Processing {i}/{total}: {file_path.stem}")

                self.import_topic_file(file_path)
            except Exception as e:
                self.stats.errors.append(f"{file_path.name}: {e}")
                logger.error(f"Error importing {file_path.name}: {e}")

        logger.info(f"Import completed: {self.stats.to_dict()}")
        return self.stats

    def import_topic_file(self, file_path: Path) -> Topic | None:
        """Import a single topic from a JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return self.import_topic(data, file_path)

    @transaction.atomic
    def import_topic(self, data: dict, source_path: Path | None = None) -> Topic | None:
        """Import a topic from JSON data."""
        slug = data.get("slug")
        if not slug:
            logger.warning("Skipping topic without slug")
            self.stats.topics_skipped += 1
            return None

        # Check if topic exists
        existing = Topic.objects.filter(slug=slug).first()
        if existing and not self.update_existing:
            logger.debug(f"Skipping existing topic: {slug}")
            self.stats.topics_skipped += 1
            return existing

        if self.dry_run:
            if existing:
                self.stats.topics_updated += 1
            else:
                self.stats.topics_created += 1
            return None

        # Determine topic type
        raw_type = data.get("type", "concept")
        topic_type = self._map_topic_type(raw_type)

        # Calculate stats
        stats = data.get("stats", {})
        ot_refs = stats.get("ot_refs", 0)
        nt_refs = stats.get("nt_refs", 0)
        total_verses = stats.get("total_verses", ot_refs + nt_refs)

        # Count aspects
        reference_groups = data.get("reference_groups", [])
        aspects_count = len(reference_groups)

        # Get books count from biblical_references
        biblical_refs = data.get("biblical_references", [])
        books = set()
        for ref in biblical_refs:
            if "book" in ref:
                books.add(ref["book"])
        books_count = len(books)

        # AI enrichment data
        ai_enrichment = data.get("ai_enrichment", {})
        ai_enriched = bool(ai_enrichment)
        ai_model = ai_enrichment.get("model", "")
        ai_confidence = ai_enrichment.get("confidence", 0.0)
        ai_run_id = ai_enrichment.get("run_id", "")
        ai_enriched_at = None
        if ai_enrichment.get("generated_at"):
            try:
                ai_enriched_at = datetime.fromisoformat(ai_enrichment["generated_at"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        # Primary source
        sources = data.get("sources", [])
        primary_source = sources[0] if sources else "NAV"

        # Create or update topic
        topic_data = {
            "canonical_id": f"UNIFIED:{slug}",
            "canonical_name": data.get("topic", slug.upper()),
            "name_normalized": slug.lower(),
            "topic_type": topic_type,
            "primary_source": primary_source,
            "available_sources": sources,
            "total_verses": total_verses,
            "ot_refs": ot_refs,
            "nt_refs": nt_refs,
            "books_count": books_count,
            "aspects_count": aspects_count,
            "ai_enriched": ai_enriched,
            "ai_model": ai_model,
            "ai_confidence": ai_confidence,
            "ai_run_id": ai_run_id,
            "ai_enriched_at": ai_enriched_at,
        }

        if existing:
            for key, value in topic_data.items():
                setattr(existing, key, value)
            existing.save()
            topic = existing
            self.stats.topics_updated += 1
        else:
            topic = Topic.objects.create(slug=slug, **topic_data)
            self.stats.topics_created += 1

        # Import related data
        self._import_names(topic, data)
        self._import_content(topic, data)
        self._import_definitions(topic, data)
        self._import_aspects(topic, data)
        self._import_theme_links(topic, data)
        self._import_cross_references(topic, data)
        self._import_relations(topic, data)
        self._import_pipeline_metadata(topic, data, source_path)

        return topic

    def _map_topic_type(self, raw_type: str) -> str:
        """Map JSON type to Topic.TopicType."""
        type_mapping = {
            "person": Topic.TopicType.PERSON,
            "place": Topic.TopicType.PLACE,
            "concept": Topic.TopicType.CONCEPT,
            "event": Topic.TopicType.EVENT,
            "object": Topic.TopicType.OBJECT,
            "literary": Topic.TopicType.LITERARY,
            "both": Topic.TopicType.CONCEPT,  # "both" = person+concept
            "topic": Topic.TopicType.CONCEPT,
        }
        return type_mapping.get(raw_type.lower(), Topic.TopicType.CONCEPT)

    def _import_names(self, topic: Topic, data: dict):
        """Import topic names for different languages."""
        # Clear existing names if updating
        if self.update_existing:
            topic.names.all().delete()

        # English name
        en_lang = self.get_language("en")
        if en_lang:
            canonical_name = data.get("topic", topic.slug.upper())
            aliases = data.get("aliases", [])

            TopicName.objects.get_or_create(
                topic=topic,
                language=en_lang,
                defaults={
                    "name": canonical_name.title(),
                    "aliases": aliases,
                },
            )

        # Portuguese name (from AI enrichment if available)
        pt_lang = self.get_language("pt")
        if pt_lang:
            ai_enrichment = data.get("ai_enrichment", {})
            # Use summary first word or canonical name
            pt_name = data.get("topic", topic.slug).title()

            TopicName.objects.get_or_create(
                topic=topic,
                language=pt_lang,
                defaults={
                    "name": pt_name,
                    "aliases": [],
                },
            )

    def _import_content(self, topic: Topic, data: dict):
        """Import topic content (summary, outline, etc.)."""
        ai_enrichment = data.get("ai_enrichment", {})
        if not ai_enrichment:
            return

        # Clear existing content if updating
        if self.update_existing:
            topic.contents.all().delete()

        # Portuguese content (primary from AI)
        pt_lang = self.get_language("pt")
        if pt_lang:
            TopicContent.objects.get_or_create(
                topic=topic,
                language=pt_lang,
                defaults={
                    "summary": ai_enrichment.get("summary", ""),
                    "outline": ai_enrichment.get("outline", []),
                    "key_concepts": ai_enrichment.get("key_concepts", []),
                    "theological_significance": ai_enrichment.get("theological_significance", ""),
                },
            )

    def _import_definitions(self, topic: Topic, data: dict):
        """Import dictionary definitions."""
        definitions = data.get("definitions", [])
        if not definitions:
            return

        # Clear existing definitions if updating
        if self.update_existing:
            topic.definitions.all().delete()

        for defn in definitions:
            source = defn.get("source", "").upper()
            if source not in ["EAS", "SMI", "NAV", "TOR", "ATS", "ISB"]:
                continue

            text = defn.get("text", "")
            extracted_refs = defn.get("extracted_refs", [])

            TopicDefinition.objects.get_or_create(
                topic=topic,
                source=source,
                defaults={
                    "text": text,
                    "extracted_refs": extracted_refs,
                },
            )
            self.stats.definitions_created += 1

    def _import_aspects(self, topic: Topic, data: dict):
        """Import topic aspects (reference groups)."""
        reference_groups = data.get("reference_groups", [])
        if not reference_groups:
            return

        # Clear existing aspects if updating
        if self.update_existing:
            topic.aspects.all().delete()

        en_lang = self.get_language("en")
        pt_lang = self.get_language("pt")

        for order, group in enumerate(reference_groups):
            name = group.get("name", "")
            if not name:
                continue

            references = group.get("references", [])

            # Calculate stats from references
            ot_refs = sum(1 for r in references if self._is_ot_reference(r))
            nt_refs = len(references) - ot_refs

            # Extract books from references
            books = []
            for ref in references:
                book = self._extract_book_from_ref(ref)
                if book and book not in books:
                    books.append(book)

            aspect = TopicAspect.objects.create(
                topic=topic,
                canonical_label=name,
                order=order,
                raw_references=references,
                verse_count=len(references),
                ot_refs=ot_refs,
                nt_refs=nt_refs,
                books=books,
                source=topic.primary_source,
            )
            self.stats.aspects_created += 1

            # Create labels
            if en_lang:
                TopicAspectLabel.objects.create(
                    aspect=aspect,
                    language=en_lang,
                    label=name,
                )

    def _import_theme_links(self, topic: Topic, data: dict):
        """Import AI-extracted themes."""
        themes = data.get("ai_themes_normalized", [])
        if not themes:
            return

        # Clear existing theme links if updating
        if self.update_existing:
            topic.theme_links.all().delete()

        for theme_data in themes:
            label_normalized = theme_data.get("label_normalized", "")
            label_original = theme_data.get("label_original", "")
            if not label_normalized:
                continue

            # Get or create the theme
            theme = self.get_or_create_theme(label_normalized, label_original)
            if not theme:
                continue

            # Map theological domain
            domain = theme_data.get("theological_domain", "")
            domain_value = self._map_theological_domain(domain)

            # Map anchor source
            anchor_source = theme_data.get("anchor_source", "ai_trusted")
            anchor_source_value = self._map_anchor_source(anchor_source)

            TopicThemeLink.objects.create(
                topic=topic,
                theme=theme,
                proposal_id=theme_data.get("proposal_id", ""),
                label_original=label_original,
                label_en=theme_data.get("label_en", ""),
                label_normalized=label_normalized,
                anchor_verses=theme_data.get("anchor_verses", []),
                anchor_source=anchor_source_value,
                anchor_meta=theme_data.get("anchor_meta", {}),
                semantic_keywords=theme_data.get("semantic_keywords", []),
                theological_domain=domain_value,
                aspect=theme_data.get("aspect", ""),
                relevance_score=theme_data.get("relevance_score", 0.0),
                confidence=theme_data.get("confidence", 1.0) if theme_data.get("confidence") else 1.0,
                source=theme_data.get("source", "ai_enrichment"),
            )
            self.stats.theme_links_created += 1

    def _import_cross_references(self, topic: Topic, data: dict):
        """Import cross-reference network."""
        cross_ref_network = data.get("cross_reference_network", {})
        if not cross_ref_network:
            return

        # Clear existing cross references if updating
        if self.update_existing:
            topic.cross_references.all().delete()

        for from_verse, refs in cross_ref_network.items():
            for ref in refs[:20]:  # Limit to top 20 per verse
                to_verse = ref.get("to_verse", "")
                score = ref.get("score", 0)
                votes = ref.get("votes", 0)
                strength = ref.get("strength", "weak")

                # Map strength
                strength_value = {
                    "strong": TopicCrossReference.Strength.STRONG,
                    "moderate": TopicCrossReference.Strength.MODERATE,
                    "weak": TopicCrossReference.Strength.WEAK,
                }.get(strength, TopicCrossReference.Strength.WEAK)

                TopicCrossReference.objects.create(
                    topic=topic,
                    from_verse_ref=from_verse,
                    to_verse_ref=to_verse,
                    score=score,
                    votes=votes,
                    strength=strength_value,
                )
                self.stats.cross_refs_created += 1

    def _import_relations(self, topic: Topic, data: dict):
        """Import topic relations (see_also)."""
        see_also = data.get("see_also", [])
        if not see_also:
            return

        # Clear existing relations if updating
        if self.update_existing:
            topic.outgoing_relations.all().delete()

        for related_slug in see_also:
            # Try to find target topic
            target = Topic.objects.filter(slug=slugify(related_slug)).first()
            if not target:
                # Create placeholder relation for future resolution
                continue

            TopicRelation.objects.get_or_create(
                source=topic,
                target=target,
                relation_type=TopicRelation.RelationType.SEE_ALSO,
            )
            self.stats.relations_created += 1

    def _import_pipeline_metadata(self, topic: Topic, data: dict, source_path: Path | None):
        """Import pipeline processing metadata."""
        phase1 = data.get("phase1_discovery", {})
        metadata_data = data.get("metadata", {})

        # Compress original JSON for backup
        raw_json = json.dumps(data, ensure_ascii=False)
        compressed = gzip.compress(raw_json.encode("utf-8"))

        TopicPipelineMetadata.objects.update_or_create(
            topic=topic,
            defaults={
                "phase0_processed_at": datetime.now(timezone.utc),
                "phase0_run_id": metadata_data.get("created_at", ""),
                "phase1_processed_at": (
                    datetime.fromisoformat(phase1["processed_at"].replace("Z", "+00:00"))
                    if phase1.get("processed_at")
                    else None
                ),
                "phase1_summary": phase1.get("summary", {}),
                "phase1_results": phase1.get("results", []),
                "raw_json_backup": compressed,
                "pipeline_version": data.get("version", "3.0.0"),
            },
        )

    def _map_theological_domain(self, domain: str) -> str:
        """Map theological domain string to model choice."""
        domain_mapping = {
            "theology_proper": TopicThemeLink.TheologicalDomain.THEOLOGY_PROPER,
            "christology": TopicThemeLink.TheologicalDomain.CHRISTOLOGY,
            "pneumatology": TopicThemeLink.TheologicalDomain.PNEUMATOLOGY,
            "anthropology": TopicThemeLink.TheologicalDomain.ANTHROPOLOGY,
            "hamartiology": TopicThemeLink.TheologicalDomain.HAMARTIOLOGY,
            "soteriology": TopicThemeLink.TheologicalDomain.SOTERIOLOGY,
            "ecclesiology": TopicThemeLink.TheologicalDomain.ECCLESIOLOGY,
            "eschatology": TopicThemeLink.TheologicalDomain.ESCHATOLOGY,
            "bibliology": TopicThemeLink.TheologicalDomain.BIBLIOLOGY,
            "angelology": TopicThemeLink.TheologicalDomain.ANGELOLOGY,
            "ethics": TopicThemeLink.TheologicalDomain.ETHICS,
            "worship": TopicThemeLink.TheologicalDomain.WORSHIP,
        }
        return domain_mapping.get(domain.lower(), "")

    def _map_anchor_source(self, source: str) -> str:
        """Map anchor source string to model choice."""
        source_mapping = {
            "ai_trusted": TopicThemeLink.AnchorSource.AI_TRUSTED,
            "ai_fallback": TopicThemeLink.AnchorSource.AI_FALLBACK,
            "manual": TopicThemeLink.AnchorSource.MANUAL,
            "derived": TopicThemeLink.AnchorSource.DERIVED,
        }
        return source_mapping.get(source.lower(), TopicThemeLink.AnchorSource.AI_TRUSTED)

    def _is_ot_reference(self, ref: str) -> bool:
        """Check if a reference is from the Old Testament."""
        ot_books = {
            "gen", "exod", "lev", "num", "deut", "josh", "judg", "ruth",
            "1sam", "2sam", "1kgs", "2kgs", "1chr", "2chr", "ezra", "neh",
            "esth", "job", "ps", "prov", "eccl", "song", "isa", "jer",
            "lam", "ezek", "dan", "hos", "joel", "amos", "obad", "jonah",
            "mic", "nah", "hab", "zeph", "hag", "zech", "mal",
            "genesis", "exodus", "leviticus", "numbers", "deuteronomy",
        }
        ref_lower = ref.lower()
        for book in ot_books:
            if ref_lower.startswith(book):
                return True
        return False

    def _extract_book_from_ref(self, ref: str) -> str:
        """Extract book code from a reference string."""
        # Handle formats like "Gen 1:1", "Genesis 1:1", "1Chr 1:1"
        match = re.match(r"^(\d?\s*[A-Za-z]+)", ref)
        if match:
            return match.group(1).strip()
        return ""
