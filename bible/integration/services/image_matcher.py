"""
Image-Entity Matching Pipeline.

Matches character names from ImageTag.characters against:
1. CanonicalEntity (primary_name + aliases) — for biblical characters
2. Person hub — for post-biblical saints/authors

Match strategy (in priority order):
1. Exact match on CanonicalEntity.primary_name (case-insensitive)
2. Alias match on EntityAlias.name (case-insensitive)
3. Fuzzy match via SequenceMatcher (≥ 0.85 threshold)

Skips GROUP characters (Crowd, Soldiers, etc.) — they don't map to entities.
"""

from __future__ import annotations

import logging
import time
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from django.db import transaction

from bible.entities.models import CanonicalEntity, EntityAlias
from bible.images.models import ImageTag
from bible.integration.models import ImageEntityLink
from bible.people.models import Person

logger = logging.getLogger(__name__)

FUZZY_THRESHOLD = 0.85
SKIP_TYPES = {"GROUP"}  # Generic groups don't map to entities


@dataclass
class MatchStats:
    """Statistics for matching pipeline run."""

    tags_processed: int = 0
    characters_processed: int = 0
    characters_skipped: int = 0
    exact_matches: int = 0
    alias_matches: int = 0
    fuzzy_matches: int = 0
    person_matches: int = 0
    unmatched: int = 0
    links_created: int = 0
    links_existing: int = 0
    errors: list = field(default_factory=list)
    duration_seconds: float = 0.0


class ImageEntityMatcher:
    """
    Batch pipeline to match image tag characters against entities and persons.

    Usage:
        matcher = ImageEntityMatcher()
        stats = matcher.match_all()
    """

    def __init__(self):
        self._entity_name_cache: dict[str, CanonicalEntity] = {}
        self._alias_cache: dict[str, CanonicalEntity] = {}
        self._person_name_cache: dict[str, Person] = {}
        self._entity_names: list[tuple[str, CanonicalEntity]] = []

    def match_all(self, clear_existing: bool = False) -> MatchStats:
        """Run matching on all tagged images."""
        start = time.time()
        stats = MatchStats()

        if clear_existing:
            deleted = ImageEntityLink.objects.all().delete()[0]
            logger.info(f"Cleared {deleted} existing links")

        # Build caches
        self._build_caches()

        # Process all tags with characters
        tags = ImageTag.objects.exclude(characters=[]).select_related("image")
        logger.info(f"Processing {tags.count()} tagged images")

        for tag in tags.iterator():
            stats.tags_processed += 1
            self._process_tag(tag, stats)

            if stats.tags_processed % 500 == 0:
                logger.info(f"  Processed {stats.tags_processed} tags...")

        stats.duration_seconds = time.time() - start
        logger.info(
            f"Matching complete in {stats.duration_seconds:.1f}s: "
            f"{stats.links_created} links created, "
            f"{stats.exact_matches} exact, {stats.alias_matches} alias, "
            f"{stats.fuzzy_matches} fuzzy, {stats.person_matches} person, "
            f"{stats.unmatched} unmatched"
        )
        return stats

    def _build_caches(self):
        """Build in-memory lookup caches for fast matching."""
        logger.info("Building entity name caches...")

        # Primary names (case-insensitive)
        for entity in CanonicalEntity.objects.only("id", "canonical_id", "primary_name"):
            key = self._normalize(entity.primary_name)
            self._entity_name_cache[key] = entity
            self._entity_names.append((key, entity))

        logger.info(f"  Entity names: {len(self._entity_name_cache)}")

        # Aliases
        for alias in EntityAlias.objects.select_related("entity").only(
            "name", "entity__id", "entity__canonical_id", "entity__primary_name"
        ):
            key = self._normalize(alias.name)
            if key not in self._entity_name_cache:
                self._alias_cache[key] = alias.entity

        logger.info(f"  Alias names: {len(self._alias_cache)}")

        # Person hub (for post-biblical saints)
        for person in Person.objects.only("id", "canonical_name", "slug"):
            key = self._normalize(person.canonical_name)
            self._person_name_cache[key] = person

        logger.info(f"  Person names: {len(self._person_name_cache)}")

    @transaction.atomic
    def _process_tag(self, tag: ImageTag, stats: MatchStats):
        """Process all characters in a single image tag."""
        for char_data in tag.characters:
            name = char_data.get("name", "").strip()
            char_type = char_data.get("type", "")

            if not name:
                continue

            stats.characters_processed += 1

            # Skip generic groups
            if char_type in SKIP_TYPES:
                stats.characters_skipped += 1
                continue

            # Check if link already exists
            existing = ImageEntityLink.objects.filter(
                image=tag.image,
                character_name=name,
            ).exists()

            if existing:
                stats.links_existing += 1
                continue

            # Try matching
            entity, person, method, confidence = self._match_character(name, char_type)

            # Create link
            ImageEntityLink.objects.create(
                image=tag.image,
                entity=entity,
                person=person,
                character_name=name,
                character_type=char_type,
                match_method=method,
                confidence=confidence,
            )
            stats.links_created += 1

            if method == "exact":
                stats.exact_matches += 1
            elif method == "alias":
                stats.alias_matches += 1
            elif method == "fuzzy":
                stats.fuzzy_matches += 1
            elif entity is None and person is not None:
                stats.person_matches += 1
            else:
                stats.unmatched += 1

    def _match_character(
        self, name: str, char_type: str
    ) -> tuple[CanonicalEntity | None, Person | None, str, float]:
        """
        Try to match a character name to an entity or person.

        Returns: (entity, person, method, confidence)
        """
        normalized = self._normalize(name)

        # 1. Exact match on entity primary_name
        entity = self._entity_name_cache.get(normalized)
        if entity:
            return entity, None, "exact", 1.0

        # 2. Alias match
        entity = self._alias_cache.get(normalized)
        if entity:
            return entity, None, "alias", 0.95

        # 3. Person hub match (for post-biblical saints like "Saint Jerome")
        person = self._person_name_cache.get(normalized)
        if person:
            return None, person, "exact", 0.9

        # 4. Fuzzy match against entity names
        best_ratio = 0.0
        best_entity = None
        for entity_name, entity_obj in self._entity_names:
            ratio = SequenceMatcher(None, normalized, entity_name).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_entity = entity_obj

        if best_ratio >= FUZZY_THRESHOLD:
            return best_entity, None, "fuzzy", round(best_ratio, 3)

        # 5. Fuzzy match against person names
        best_ratio_person = 0.0
        best_person = None
        for person_name, person_obj in self._person_name_cache.items():
            ratio = SequenceMatcher(None, normalized, person_name).ratio()
            if ratio > best_ratio_person:
                best_ratio_person = ratio
                best_person = person_obj

        if best_ratio_person >= FUZZY_THRESHOLD:
            return None, best_person, "fuzzy", round(best_ratio_person, 3)

        # No match — create unlinked record
        return None, None, "exact", 0.0

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize text for matching: lowercase, strip accents."""
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")
        return text.lower().strip()

    @staticmethod
    def get_status() -> dict:
        """Get current matching status."""
        from django.db.models import Count

        total = ImageEntityLink.objects.count()
        by_method = dict(
            ImageEntityLink.objects.values("match_method")
            .annotate(count=Count("id"))
            .values_list("match_method", "count")
        )

        with_entity = ImageEntityLink.objects.filter(entity__isnull=False).count()
        with_person = ImageEntityLink.objects.filter(person__isnull=False).count()
        unlinked = ImageEntityLink.objects.filter(entity__isnull=True, person__isnull=True).count()

        return {
            "total_links": total,
            "with_entity": with_entity,
            "with_person": with_person,
            "unlinked": unlinked,
            "by_method": by_method,
        }
