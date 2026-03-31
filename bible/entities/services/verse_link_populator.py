"""
Populate EntityVerseLink from entity key_refs and SymbolOccurrence from symbol bible_examples.

Reads processed gazetteer data and creates verse-level links using the ref_parser.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from django.db import transaction

from bible.entities.models import CanonicalEntity, EntityVerseLink
from bible.models import CanonicalBook, Verse, Version
from bible.symbols.models import BiblicalSymbol, SymbolMeaning, SymbolOccurrence
from bible.utils.ref_parser import parse_ref

logger = logging.getLogger(__name__)


@dataclass
class PopulateStats:
    entity_links_created: int = 0
    entity_links_skipped: int = 0
    symbol_occurrences_created: int = 0
    symbol_occurrences_skipped: int = 0
    refs_parsed: int = 0
    refs_failed: int = 0
    verses_not_found: int = 0
    errors: list = field(default_factory=list)
    duration_seconds: float = 0.0


class VerseLinkPopulator:
    """
    Populate EntityVerseLink + SymbolOccurrence from processed gazetteer key_refs.

    Usage:
        populator = VerseLinkPopulator()
        stats = populator.populate_all()
    """

    def __init__(self, processed_dir: str | Path | None = None, version_code: str = "ACF"):
        if processed_dir is None:
            base = Path(__file__).resolve().parents[3]
            processed_dir = base / "data" / "processed" / "gazetteers"
        self.processed_dir = Path(processed_dir)
        self.version_code = version_code

        self._book_cache: dict[str, CanonicalBook] = {}
        self._verse_cache: dict[str, Verse] = {}
        self._version: Version | None = None

    def populate_all(self, clear_existing: bool = False) -> PopulateStats:
        start = time.time()
        stats = PopulateStats()

        self._version = Version.objects.filter(code=self.version_code).first()
        if not self._version:
            stats.errors.append(f"Version {self.version_code} not found")
            return stats

        self._build_book_cache()

        if clear_existing:
            e_del = EntityVerseLink.objects.all().delete()[0]
            s_del = SymbolOccurrence.objects.all().delete()[0]
            logger.info(f"Cleared {e_del} entity links + {s_del} symbol occurrences")

        self._populate_entity_links(stats)
        self._populate_symbol_occurrences(stats)

        stats.duration_seconds = time.time() - start
        logger.info(
            f"Population complete in {stats.duration_seconds:.1f}s: "
            f"{stats.entity_links_created} entity links, "
            f"{stats.symbol_occurrences_created} symbol occurrences, "
            f"{stats.refs_failed} refs failed, "
            f"{stats.verses_not_found} verses not found"
        )
        return stats

    def _build_book_cache(self):
        for book in CanonicalBook.objects.all():
            self._book_cache[book.osis_code] = book

    def _find_verse(self, osis_code: str, chapter: int, verse_num: int) -> Verse | None:
        key = f"{osis_code}:{chapter}:{verse_num}"
        if key in self._verse_cache:
            return self._verse_cache[key]

        book = self._book_cache.get(osis_code)
        if not book:
            return None

        verse = (
            Verse.objects
            .filter(book=book, version=self._version, chapter=chapter, number=verse_num)
            .first()
        )
        self._verse_cache[key] = verse
        return verse

    def _populate_entity_links(self, stats: PopulateStats):
        logger.info("Populating EntityVerseLink from key_refs...")

        entities_dir = self.processed_dir / "entities"
        if not entities_dir.exists():
            stats.errors.append(f"Entities dir not found: {entities_dir}")
            return

        # Load all entities from DB indexed by canonical_id
        entity_map = {e.canonical_id: e for e in CanonicalEntity.objects.only("id", "canonical_id")}
        logger.info(f"  Entities in DB: {len(entity_map)}")

        links_batch = []

        for fn in sorted(os.listdir(entities_dir)):
            if not fn.endswith('.json'):
                continue

            with open(entities_dir / fn, encoding="utf-8") as f:
                entries = json.load(f)

            for entry in entries:
                cid = entry.get("canonical_id", "")
                entity = entity_map.get(cid)
                if not entity:
                    continue

                for ref_str in entry.get("key_refs", []):
                    osis, chapter, vs, ve = parse_ref(ref_str)
                    if not osis:
                        stats.refs_failed += 1
                        continue

                    stats.refs_parsed += 1

                    # For ranges, link to each verse
                    if vs is None:
                        # Chapter-only ref — skip (too broad)
                        continue

                    for v_num in range(vs, (ve or vs) + 1):
                        verse = self._find_verse(osis, chapter, v_num)
                        if not verse:
                            stats.verses_not_found += 1
                            continue

                        links_batch.append(
                            EntityVerseLink(
                                entity=entity,
                                verse=verse,
                                mention_type="explicit",
                                relevance=1.0,
                                is_primary_subject=True,
                            )
                        )

            # Batch create periodically
            if len(links_batch) >= 1000:
                self._bulk_create_entity_links(links_batch, stats)
                links_batch = []

        # Final batch
        if links_batch:
            self._bulk_create_entity_links(links_batch, stats)

        logger.info(f"  Entity links created: {stats.entity_links_created}")

    def _bulk_create_entity_links(self, batch: list, stats: PopulateStats):
        created = EntityVerseLink.objects.bulk_create(batch, ignore_conflicts=True)
        stats.entity_links_created += len(created)
        skipped = len(batch) - len(created)
        stats.entity_links_skipped += skipped

    def _populate_symbol_occurrences(self, stats: PopulateStats):
        logger.info("Populating SymbolOccurrence from bible_examples...")

        symbols_dir = self.processed_dir / "symbols"
        if not symbols_dir.exists():
            stats.errors.append(f"Symbols dir not found: {symbols_dir}")
            return

        symbol_map = {s.canonical_id: s for s in BiblicalSymbol.objects.only("id", "canonical_id")}
        logger.info(f"  Symbols in DB: {len(symbol_map)}")

        occ_batch = []

        for fn in sorted(os.listdir(symbols_dir)):
            if not fn.endswith('.json'):
                continue

            with open(symbols_dir / fn, encoding="utf-8") as f:
                entries = json.load(f)

            for entry in entries:
                cid = entry.get("canonical_id", "")
                symbol = symbol_map.get(cid)
                if not symbol:
                    continue

                # Get first meaning for linking
                meaning = SymbolMeaning.objects.filter(symbol=symbol).first()

                for example in entry.get("bible_examples", []):
                    ref_str = example.get("ref", "")
                    context = example.get("context", "")

                    osis, chapter, vs, ve = parse_ref(ref_str)
                    if not osis:
                        stats.refs_failed += 1
                        continue

                    stats.refs_parsed += 1

                    if vs is None:
                        continue

                    for v_num in range(vs, (ve or vs) + 1):
                        verse = self._find_verse(osis, chapter, v_num)
                        if not verse:
                            stats.verses_not_found += 1
                            continue

                        occ_batch.append(
                            SymbolOccurrence(
                                symbol=symbol,
                                verse=verse,
                                meaning=meaning,
                                usage_type="symbolic",
                                context_note=context[:500] if context else "",
                            )
                        )

            if len(occ_batch) >= 500:
                self._bulk_create_symbol_occurrences(occ_batch, stats)
                occ_batch = []

        if occ_batch:
            self._bulk_create_symbol_occurrences(occ_batch, stats)

        logger.info(f"  Symbol occurrences created: {stats.symbol_occurrences_created}")

    def _bulk_create_symbol_occurrences(self, batch: list, stats: PopulateStats):
        created = SymbolOccurrence.objects.bulk_create(batch, ignore_conflicts=True)
        stats.symbol_occurrences_created += len(created)
        skipped = len(batch) - len(created)
        stats.symbol_occurrences_skipped += skipped
