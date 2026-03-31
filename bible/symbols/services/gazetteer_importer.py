"""
Symbols Gazetteer Importer - Import biblical symbols from processed gazetteer data.

Reads from: data/processed/gazetteers/symbols/ (v3.1 per-namespace format)
Writes to: BiblicalSymbol, SymbolMeaning
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from django.db import transaction

from bible.symbols.models import (
    BiblicalSymbol,
    SymbolMeaning,
    SymbolNamespace,
    SymbolStatus,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class ImportStats:
    """Statistics for import operation."""

    symbols_created: int = 0
    symbols_updated: int = 0
    symbols_skipped: int = 0
    meanings_created: int = 0
    errors: list = field(default_factory=list)
    duration_seconds: float = 0.0


class SymbolsImporter:
    """
    Import biblical symbols from processed gazetteer v3 data.

    Usage:
        importer = SymbolsImporter()
        stats = importer.import_all()
    """

    # Mapping from processed namespace → model namespace
    NAMESPACE_MAP = {
        "NATURAL": SymbolNamespace.NATURAL,
        "OBJECT": SymbolNamespace.OBJECT,
        "ACTION": SymbolNamespace.ACTION,
        "NUMBER": SymbolNamespace.NUMBER,
        "COLOR": SymbolNamespace.COLOR,
        "PERSON_TYPE": SymbolNamespace.PERSON_TYPE,
        "PLANT": SymbolNamespace.PLANT,
        # Mappings for namespaces not in model
        "CELESTIAL": SymbolNamespace.COSMIC,
        "CREATURE": SymbolNamespace.ANIMAL,
        "FOOD": SymbolNamespace.OBJECT,
        "MATERIAL": SymbolNamespace.OBJECT,
        "PLACE": SymbolNamespace.NATURAL,
    }

    def __init__(self, gazetteer_dir: str | Path | None = None):
        if gazetteer_dir is None:
            base_path = Path(__file__).resolve().parents[3]  # bible-api/
            gazetteer_dir = base_path / "data" / "processed" / "gazetteers"

        self.gazetteer_dir = Path(gazetteer_dir)

    def import_all(self, update_existing: bool = False) -> ImportStats:
        """Import all symbols from processed gazetteer data."""
        import time
        start_time = time.time()

        stats = self.import_symbols(update_existing=update_existing)
        stats.duration_seconds = time.time() - start_time

        return stats

    def import_symbols(self, update_existing: bool = False) -> ImportStats:
        """Import symbols from v3 per-namespace JSON files."""
        stats = ImportStats()

        meta_path = self.gazetteer_dir / "_meta.json"
        if not meta_path.exists():
            stats.errors.append(f"_meta.json not found in {self.gazetteer_dir}")
            return stats

        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)

        logger.info(f"Importing symbols from {self.gazetteer_dir} (v{meta.get('version', '?')})")

        for ns_key, ns_info in meta.get("symbol_namespaces", {}).items():
            namespace = self.NAMESPACE_MAP.get(ns_key)
            if not namespace:
                logger.warning(f"  Unknown symbol namespace {ns_key}, skipping")
                continue

            filepath = self.gazetteer_dir / ns_info["file"]
            if not filepath.exists():
                stats.errors.append(f"File not found: {filepath}")
                continue

            with open(filepath, encoding="utf-8") as f:
                entries = json.load(f)

            logger.info(f"  {ns_key}: {len(entries)} symbols")

            for entry in entries:
                try:
                    self._import_symbol(entry, namespace, stats, update_existing)
                except Exception as e:
                    cid = entry.get("canonical_id", "?")
                    error_msg = f"Error importing {cid}: {e}"
                    logger.error(error_msg)
                    stats.errors.append(error_msg)

        logger.info(
            f"Symbols import complete: "
            f"{stats.symbols_created} created, "
            f"{stats.symbols_updated} updated, "
            f"{stats.symbols_skipped} skipped, "
            f"{stats.meanings_created} meanings"
        )
        return stats

    @transaction.atomic
    def _import_symbol(
        self,
        entry: dict,
        namespace: str,
        stats: ImportStats,
        update_existing: bool,
    ):
        """Import a single symbol with its meanings."""
        canonical_id = entry.get("canonical_id", "")
        if not canonical_id:
            stats.symbols_skipped += 1
            return

        name = entry.get("name", "")

        existing = BiblicalSymbol.objects.filter(canonical_id=canonical_id).first()
        if existing and not update_existing:
            stats.symbols_skipped += 1
            return

        defaults = {
            "namespace": namespace,
            "primary_name": name,
            "primary_name_pt": name,
            "aliases": entry.get("aliases", []),
            "literal_meaning": entry.get("literal_meaning", ""),
            "literal_meaning_pt": entry.get("literal_meaning", ""),
            "description": entry.get("description", ""),
            "description_pt": entry.get("description", ""),
            "associated_concepts": entry.get("associated_concepts", []),
            "boost": entry.get("boost") or 1.0,
            "priority": entry.get("priority") or 50,
            "status": SymbolStatus.APPROVED,
            "source_gazetteer": "processed_gazetteers_v3",
        }

        symbol, created = BiblicalSymbol.objects.update_or_create(
            canonical_id=canonical_id,
            defaults=defaults,
        )

        if created:
            stats.symbols_created += 1
        else:
            stats.symbols_updated += 1

        # Import symbolic meanings
        symbolic_meanings = entry.get("symbolic_meaning", [])
        if symbolic_meanings:
            if not created and update_existing:
                symbol.meanings.all().delete()

            for idx, meaning_text in enumerate(symbolic_meanings):
                if not meaning_text or len(meaning_text.strip()) < 2:
                    continue

                meaning_clean = meaning_text.strip()

                existing_meaning = symbol.meanings.filter(
                    meaning__iexact=meaning_clean
                ).exists()

                if not existing_meaning:
                    SymbolMeaning.objects.create(
                        symbol=symbol,
                        meaning=meaning_clean,
                        meaning_pt=meaning_clean,
                        is_primary_meaning=(idx == 0),
                        frequency=1,
                    )
                    stats.meanings_created += 1

        # Import bible examples as supporting references
        bible_examples = entry.get("bible_examples", [])
        if bible_examples and symbol.meanings.exists():
            first_meaning = symbol.meanings.first()
            refs = [ex.get("ref", "") for ex in bible_examples[:10] if ex.get("ref")]
            if refs and first_meaning:
                first_meaning.supporting_references = refs
                first_meaning.save(update_fields=["supporting_references"])

    def get_status(self) -> dict:
        """Get current status of symbols in database."""
        from django.db.models import Count

        total = BiblicalSymbol.objects.count()
        by_namespace = dict(
            BiblicalSymbol.objects.values("namespace")
            .annotate(count=Count("id"))
            .values_list("namespace", "count")
        )
        by_status = dict(
            BiblicalSymbol.objects.values("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )
        meanings_count = SymbolMeaning.objects.count()

        return {
            "total_symbols": total,
            "by_namespace": by_namespace,
            "by_status": by_status,
            "meanings": meanings_count,
        }
