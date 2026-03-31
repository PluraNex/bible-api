"""
Gazetteer Data Quality Pipeline — Fase 0.

Reads raw gazetteer data (bible-gazetteers-dataset) + tagger index (bible-image-tagger),
cleans, merges, validates, and outputs processed data ready for DB import.

Inputs (read-only, never modified):
  - bible-gazetteers-dataset/data/pt/  (v3 per-namespace JSONs)
  - bible-image-tagger/data/lookup/gazetteer_index.json

Output (deletable, regenerable):
  - bible-api/data/processed/gazetteers/
      ├── entities/          (cleaned per-namespace JSONs)
      ├── symbols/           (cleaned per-namespace JSONs)
      ├── relationships.json (cleaned relationships)
      ├── aliases_unified.json (EN+PT alias index)
      ├── metrics/           (entity_scores.json + symbol_scores.json)
      ├── _meta.json         (updated metadata)
      └── quality_report.json
"""

from __future__ import annotations

import json
import logging
import re
import time
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Valid OSIS book codes (from bible.utils.osis_maps)
VALID_OSIS_BOOKS = {
    "Gen", "Exod", "Lev", "Num", "Deut", "Josh", "Judg", "Ruth",
    "1Sam", "2Sam", "1Kgs", "2Kgs", "1Chr", "2Chr", "Ezra", "Neh", "Esth",
    "Job", "Ps", "Prov", "Eccl", "Song", "Isa", "Jer", "Lam", "Ezek",
    "Dan", "Hos", "Joel", "Amos", "Obad", "Jonah", "Mic", "Nah", "Hab",
    "Zeph", "Hag", "Zech", "Mal",
    "Matt", "Mark", "Luke", "John", "Acts", "Rom", "1Cor", "2Cor", "Gal",
    "Eph", "Phil", "Col", "1Thess", "2Thess", "1Tim", "2Tim", "Titus",
    "Phlm", "Heb", "Jas", "1Pet", "2Pet", "1John", "2John", "3John",
    "Jude", "Rev",
}

# Canonical prefix for each entity namespace
ENTITY_PREFIX_MAP = {
    "PERSON": "PER",
    "PLACE": "PLC",
    "CONCEPT": "CPT",
    "OBJECT": "OBJ",
    "GROUP": "GRP",
    "EVENT": "EVT",
    "LITERARY_WORK": "LIT",
    "LITERARY_FORM": "FRM",
    "DEITY": "DIV",
    "CREATURE": "CRE",
    "RITUAL": "RIT",
    "PLANT": "PLN",
    "ANGEL": "ANG",
}

# Canonical prefix for each symbol namespace
SYMBOL_PREFIX_MAP = {
    "OBJECT": "OBJ",
    "NATURAL": "NAT",
    "ACTION": "ACT",
    "COLOR": "CLR",
    "PERSON_TYPE": "PER",
    "NUMBER": "NUM",
    "MATERIAL": "MAT",
    "PLACE": "PLC",
    "FOOD": "FOD",
    "CREATURE": "CRE",
    "PLANT": "PLT",
    "CELESTIAL": "CEL",
}


@dataclass
class ProcessingReport:
    """Quality report for the processing pipeline."""

    # Counts
    entities_total: int = 0
    symbols_total: int = 0
    relationships_total: int = 0
    aliases_en_added: int = 0
    aliases_pt_existing: int = 0

    # Fixes applied
    prefix_fixes: list = field(default_factory=list)
    duplicate_merges: list = field(default_factory=list)
    canonical_id_fixes: list = field(default_factory=list)

    # Validation
    invalid_refs: list = field(default_factory=list)
    duplicate_ids: list = field(default_factory=list)
    alias_conflicts: list = field(default_factory=list)
    missing_fields: list = field(default_factory=list)

    # Per-namespace counts
    entity_counts: dict = field(default_factory=dict)
    symbol_counts: dict = field(default_factory=dict)

    # Metrics
    duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "summary": {
                "entities_total": self.entities_total,
                "symbols_total": self.symbols_total,
                "relationships_total": self.relationships_total,
                "aliases_en_added": self.aliases_en_added,
                "aliases_pt_existing": self.aliases_pt_existing,
                "duration_seconds": round(self.duration_seconds, 2),
            },
            "entity_counts": self.entity_counts,
            "symbol_counts": self.symbol_counts,
            "fixes_applied": {
                "prefix_fixes": len(self.prefix_fixes),
                "prefix_fix_details": self.prefix_fixes[:50],
                "duplicate_merges": len(self.duplicate_merges),
                "duplicate_merge_details": self.duplicate_merges[:50],
                "canonical_id_fixes": len(self.canonical_id_fixes),
                "canonical_id_fix_details": self.canonical_id_fixes[:50],
            },
            "validation": {
                "invalid_refs_count": len(self.invalid_refs),
                "invalid_refs": self.invalid_refs[:100],
                "duplicate_ids_count": len(self.duplicate_ids),
                "duplicate_ids": self.duplicate_ids[:50],
                "alias_conflicts_count": len(self.alias_conflicts),
                "alias_conflicts": self.alias_conflicts[:50],
                "missing_fields_count": len(self.missing_fields),
                "missing_fields": self.missing_fields[:50],
            },
        }


class GazetteerProcessor:
    """
    Data quality pipeline for gazetteer data.

    Usage:
        processor = GazetteerProcessor(
            source_dir="path/to/bible-gazetteers-dataset/data/pt",
            tagger_index_path="path/to/gazetteer_index.json",
            output_dir="path/to/bible-api/data/processed/gazetteers",
        )
        report = processor.process()
    """

    def __init__(
        self,
        source_dir: str | Path,
        tagger_index_path: str | Path | None = None,
        output_dir: str | Path | None = None,
    ):
        self.source_dir = Path(source_dir)
        self.tagger_index_path = Path(tagger_index_path) if tagger_index_path else None
        if output_dir is None:
            base = Path(__file__).resolve().parents[2]  # bible-api/
            output_dir = base / "data" / "processed" / "gazetteers"
        self.output_dir = Path(output_dir)

        # Internal state
        self._entities: dict[str, list[dict]] = {}  # namespace → list of entries
        self._symbols: dict[str, list[dict]] = {}
        self._relationships: list[dict] = []
        self._entity_metrics: dict[str, dict] = {}
        self._symbol_metrics: dict[str, dict] = {}
        self._tagger_entity_by_name: dict[str, list[dict]] = {}
        self._tagger_symbol_by_name: dict[str, list[dict]] = {}
        self._tagger_entity_by_id: dict[str, dict] = {}
        self._tagger_symbol_by_id: dict[str, dict] = {}
        self._tagger_translations: dict[str, dict] = {}
        self._report = ProcessingReport()

    def process(self) -> ProcessingReport:
        """Run the full data quality pipeline."""
        start = time.time()

        logger.info("=== Gazetteer Data Quality Pipeline ===")

        # Step 1: Read source data
        self._read_source_data()

        # Step 2: Read tagger index (if available)
        if self.tagger_index_path and self.tagger_index_path.exists():
            self._read_tagger_index()

        # Step 3: Normalize & fix
        self._normalize_prefixes()
        self._normalize_canonical_ids()
        self._deduplicate_entities()
        self._deduplicate_symbols()

        # Step 4: Merge EN aliases from tagger
        self._merge_tagger_aliases()

        # Step 5: Merge metrics
        self._merge_metrics()

        # Step 6: Validate
        self._validate_refs()
        self._validate_unique_ids()
        self._detect_alias_conflicts()
        self._validate_required_fields()

        # Step 7: Write output
        self._write_output()

        self._report.duration_seconds = time.time() - start
        logger.info(
            f"=== Pipeline complete in {self._report.duration_seconds:.1f}s: "
            f"{self._report.entities_total} entities, "
            f"{self._report.symbols_total} symbols, "
            f"{self._report.relationships_total} relationships ==="
        )

        return self._report

    # ── Step 1: Read source data ──────────────────────────────────

    def _read_source_data(self):
        """Read v3 per-namespace files from source directory."""
        meta_path = self.source_dir / "_meta.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"_meta.json not found in {self.source_dir}")

        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)

        logger.info(f"Reading source: v{meta.get('version', '?')} ({meta.get('lang', '?')})")

        # Read entities
        for ns_name, ns_info in meta.get("entity_namespaces", {}).items():
            filepath = self.source_dir / ns_info["file"]
            if filepath.exists():
                with open(filepath, encoding="utf-8") as f:
                    entries = json.load(f)
                self._entities[ns_name] = entries
                logger.info(f"  Entities/{ns_name}: {len(entries)} entries")
            else:
                logger.warning(f"  Entities/{ns_name}: file not found ({filepath})")

        # Read symbols
        for ns_name, ns_info in meta.get("symbol_namespaces", {}).items():
            filepath = self.source_dir / ns_info["file"]
            if filepath.exists():
                with open(filepath, encoding="utf-8") as f:
                    entries = json.load(f)
                self._symbols[ns_name] = entries
                logger.info(f"  Symbols/{ns_name}: {len(entries)} entries")
            else:
                logger.warning(f"  Symbols/{ns_name}: file not found ({filepath})")

        # Read relationships
        rels_path = self.source_dir / "relationships.json"
        if rels_path.exists():
            with open(rels_path, encoding="utf-8") as f:
                self._relationships = json.load(f)
            logger.info(f"  Relationships: {len(self._relationships)}")

        # Read metrics
        metrics_dir = self.source_dir / "metrics"
        if metrics_dir.exists():
            esc_path = metrics_dir / "entity_scores.json"
            if esc_path.exists():
                with open(esc_path, encoding="utf-8") as f:
                    self._entity_metrics = json.load(f)
                logger.info(f"  Entity metrics: {len(self._entity_metrics)}")

            ssc_path = metrics_dir / "symbol_scores.json"
            if ssc_path.exists():
                with open(ssc_path, encoding="utf-8") as f:
                    self._symbol_metrics = json.load(f)
                logger.info(f"  Symbol metrics: {len(self._symbol_metrics)}")

    # ── Step 2: Read tagger index ─────────────────────────────────

    def _read_tagger_index(self):
        """Read gazetteer_index.json from tagger (large file, ~7.7 MB)."""
        logger.info(f"Reading tagger index: {self.tagger_index_path}")

        with open(self.tagger_index_path, encoding="utf-8") as f:
            data = json.load(f)

        self._tagger_entity_by_name = data.get("entity_by_name", {})
        self._tagger_symbol_by_name = data.get("symbol_by_name", {})
        self._tagger_entity_by_id = data.get("entity_by_id", {})
        self._tagger_symbol_by_id = data.get("symbol_by_id", {})
        self._tagger_translations = data.get("translation_tables", {})

        meta = data.get("meta", {})
        logger.info(
            f"  Tagger index loaded: "
            f"{meta.get('total_entity_names', 0)} entity names, "
            f"{meta.get('total_symbol_names', 0)} symbol names"
        )

    # ── Step 3: Normalize & fix ───────────────────────────────────

    def _normalize_prefixes(self):
        """Fix inconsistent prefixes (PLA: → PLC: for places)."""
        for ns_name, entries in self._entities.items():
            canonical_prefix = ENTITY_PREFIX_MAP.get(ns_name, ns_name[:3].upper())
            for entry in entries:
                cid = entry.get("canonical_id", "")
                if not cid:
                    continue

                parts = cid.split(":", 1)
                if len(parts) != 2:
                    continue

                current_prefix, slug = parts
                if current_prefix != canonical_prefix:
                    new_id = f"{canonical_prefix}:{slug}"
                    self._report.prefix_fixes.append(
                        f"{cid} → {new_id} (namespace={ns_name})"
                    )
                    entry["canonical_id"] = new_id
                    entry["_old_canonical_id"] = cid

        logger.info(f"  Prefix fixes: {len(self._report.prefix_fixes)}")

    def _normalize_canonical_ids(self):
        """Ensure canonical_ids are lowercase slugs, no accents in slug part."""
        for ns_name, entries in self._entities.items():
            for entry in entries:
                cid = entry.get("canonical_id", "")
                if not cid:
                    # Generate canonical_id
                    prefix = ENTITY_PREFIX_MAP.get(ns_name, ns_name[:3].upper())
                    slug = self._slugify(entry.get("name", "unknown"))
                    entry["canonical_id"] = f"{prefix}:{slug}"
                    self._report.canonical_id_fixes.append(
                        f"Generated {entry['canonical_id']} for '{entry.get('name', '')}'"
                    )
                    continue

                parts = cid.split(":", 1)
                if len(parts) == 2:
                    prefix, slug = parts
                    normalized_slug = self._slugify(slug)
                    if normalized_slug != slug:
                        new_id = f"{prefix}:{normalized_slug}"
                        self._report.canonical_id_fixes.append(f"{cid} → {new_id}")
                        entry["_old_canonical_id"] = entry.get("_old_canonical_id", cid)
                        entry["canonical_id"] = new_id

        for ns_name, entries in self._symbols.items():
            canonical_prefix = SYMBOL_PREFIX_MAP.get(ns_name, "SYM")
            for entry in entries:
                cid = entry.get("canonical_id", "")
                if not cid:
                    slug = self._slugify(entry.get("name", "unknown"))
                    entry["canonical_id"] = f"{canonical_prefix}:{slug}"
                    self._report.canonical_id_fixes.append(
                        f"Generated {entry['canonical_id']} for symbol '{entry.get('name', '')}'"
                    )
                    continue

                # Fix wrong prefix (e.g., SYM: → NAT: for NATURAL namespace)
                parts = cid.split(":", 1)
                if len(parts) == 2:
                    current_prefix, slug = parts
                    # Normalize slug accents
                    normalized_slug = self._slugify(slug)
                    needs_fix = False
                    if current_prefix != canonical_prefix:
                        needs_fix = True
                    if normalized_slug != slug:
                        needs_fix = True
                    if needs_fix:
                        new_id = f"{canonical_prefix}:{normalized_slug}"
                        if new_id != cid:
                            self._report.canonical_id_fixes.append(
                                f"Symbol {cid} → {new_id} (namespace={ns_name})"
                            )
                            entry["_old_canonical_id"] = entry.get("_old_canonical_id", cid)
                            entry["canonical_id"] = new_id

        logger.info(f"  Canonical ID fixes: {len(self._report.canonical_id_fixes)}")

    def _deduplicate_entities(self):
        """Detect and merge entities with same canonical_id or near-identical names."""
        for ns_name, entries in self._entities.items():
            seen: dict[str, int] = {}  # canonical_id → index in entries
            merged_count = 0

            i = 0
            while i < len(entries):
                entry = entries[i]
                cid = entry.get("canonical_id", "")

                if cid in seen:
                    # Merge into existing
                    existing = entries[seen[cid]]
                    self._merge_entity(existing, entry)
                    entries.pop(i)
                    merged_count += 1
                    self._report.duplicate_merges.append(
                        f"{cid}: merged duplicate in {ns_name}"
                    )
                else:
                    seen[cid] = i
                    i += 1

            if merged_count:
                logger.info(f"  Dedup {ns_name}: merged {merged_count} duplicates")

        # Cross-namespace dedup: check for same slug across namespaces
        all_ids = Counter()
        for ns_name, entries in self._entities.items():
            for entry in entries:
                all_ids[entry.get("canonical_id", "")] += 1

        for cid, count in all_ids.items():
            if count > 1 and cid:
                self._report.duplicate_ids.append(
                    f"{cid}: appears {count} times across namespaces"
                )

    def _deduplicate_symbols(self):
        """Detect and merge symbols with same canonical_id."""
        for ns_name, entries in self._symbols.items():
            seen: dict[str, int] = {}
            merged_count = 0

            i = 0
            while i < len(entries):
                entry = entries[i]
                cid = entry.get("canonical_id", "")

                if cid in seen:
                    existing = entries[seen[cid]]
                    self._merge_symbol(existing, entry)
                    entries.pop(i)
                    merged_count += 1
                    self._report.duplicate_merges.append(
                        f"{cid}: merged duplicate symbol in {ns_name}"
                    )
                else:
                    seen[cid] = i
                    i += 1

            if merged_count:
                logger.info(f"  Dedup symbols/{ns_name}: merged {merged_count}")

    # ── Step 4: Merge EN aliases from tagger ──────────────────────

    def _merge_tagger_aliases(self):
        """Enrich entities/symbols with English aliases from tagger index."""
        if not self._tagger_entity_by_name:
            logger.info("  Tagger index not loaded, skipping alias merge")
            return

        en_added = 0

        # Build reverse map: canonical_id → set of all names that resolve to it
        # entity_by_name has lowercase keys that map to canonical_ids
        entity_reverse: dict[str, set[str]] = defaultdict(set)
        for name_key, matches in self._tagger_entity_by_name.items():
            for match in matches:
                cid = match.get("canonical_id", "")
                if cid:
                    entity_reverse[cid].add(name_key)

        symbol_reverse: dict[str, set[str]] = defaultdict(set)
        for name_key, matches in self._tagger_symbol_by_name.items():
            for match in matches:
                cid = match.get("canonical_id", "")
                if cid:
                    symbol_reverse[cid].add(name_key)

        # Entities: add tagger name lookups as EN aliases
        for ns_name, entries in self._entities.items():
            for entry in entries:
                cid = entry.get("canonical_id", "")
                old_cid = entry.get("_old_canonical_id", "")

                # Find all names in tagger that resolve to this entity
                tagger_names = entity_reverse.get(cid, set())
                if old_cid:
                    tagger_names = tagger_names | entity_reverse.get(old_cid, set())

                if not tagger_names:
                    continue

                # Current aliases — normalized (no accents, lowercase) for comparison
                existing_norm = set()
                for a in entry.get("aliases", []):
                    existing_norm.add(self._normalize_for_compare(a))
                existing_norm.add(self._normalize_for_compare(entry.get("name", "")))

                new_aliases = []
                for name in sorted(tagger_names):
                    if name and self._normalize_for_compare(name) not in existing_norm:
                        new_aliases.append(name)
                        existing_norm.add(self._normalize_for_compare(name))

                if new_aliases:
                    entry.setdefault("aliases", []).extend(new_aliases)
                    entry.setdefault("aliases_en", []).extend(new_aliases)
                    en_added += len(new_aliases)

                # Enrich with tagger name_meaning if missing
                tagger_data = self._tagger_entity_by_id.get(cid) or self._tagger_entity_by_id.get(old_cid, {})
                if not entry.get("name_meaning") and tagger_data.get("name_meaning"):
                    entry["name_meaning"] = tagger_data["name_meaning"]

        # Symbols: add tagger name lookups + translation table EN keys
        for ns_name, entries in self._symbols.items():
            for entry in entries:
                cid = entry.get("canonical_id", "")
                tagger_names = symbol_reverse.get(cid, set())

                if not tagger_names:
                    continue

                existing_norm = set()
                for a in entry.get("aliases", []):
                    existing_norm.add(self._normalize_for_compare(a))
                existing_norm.add(self._normalize_for_compare(entry.get("name", "")))

                new_aliases = []
                for name in sorted(tagger_names):
                    if name and self._normalize_for_compare(name) not in existing_norm:
                        new_aliases.append(name)
                        existing_norm.add(self._normalize_for_compare(name))

                if new_aliases:
                    entry.setdefault("aliases", []).extend(new_aliases)
                    entry.setdefault("aliases_en", []).extend(new_aliases)
                    en_added += len(new_aliases)

                # Enrich visual_correlations from tagger
                tagger_data = self._tagger_symbol_by_id.get(cid, {})
                if not entry.get("visual_correlations") and tagger_data.get("visual_correlations"):
                    entry["visual_correlations"] = tagger_data["visual_correlations"]

        # Also add EN→PT from translation tables as aliases
        en_from_translations = self._merge_translation_table_aliases()
        en_added += en_from_translations

        self._report.aliases_en_added = en_added
        logger.info(f"  EN aliases added from tagger: {en_added}")

    def _merge_translation_table_aliases(self) -> int:
        """Add EN names from translation_tables as aliases to matching symbols/entities."""
        added = 0
        sym_translations = self._tagger_translations.get("symbols", {})

        # For each EN→PT symbol translation, find the symbol and add EN as alias
        for en_name, pt_slug in sym_translations.items():
            pt_slug_normalized = self._slugify(pt_slug)
            found = False
            for ns_name, entries in self._symbols.items():
                if found:
                    break
                for entry in entries:
                    entry_slug = self._slugify(entry.get("name", ""))
                    if entry_slug == pt_slug_normalized:
                        existing = set(a.lower() for a in entry.get("aliases", []))
                        if en_name.lower() not in existing:
                            entry.setdefault("aliases", []).append(en_name)
                            entry.setdefault("aliases_en", []).append(en_name)
                            added += 1
                        found = True
                        break

        # Characters translations → entity aliases
        char_translations = self._tagger_translations.get("characters", {})
        for en_name, pt_slug in char_translations.items():
            pt_slug_normalized = self._slugify(pt_slug)
            found = False
            for ns_name, entries in self._entities.items():
                if found:
                    break
                for entry in entries:
                    entry_slug = self._slugify(entry.get("name", ""))
                    if entry_slug == pt_slug_normalized:
                        existing = set(a.lower() for a in entry.get("aliases", []))
                        if en_name.lower() not in existing:
                            entry.setdefault("aliases", []).append(en_name)
                            entry.setdefault("aliases_en", []).append(en_name)
                            added += 1
                        found = True
                        break

        return added

    # ── Step 5: Merge metrics ─────────────────────────────────────

    def _merge_metrics(self):
        """Merge metrics (boost, priority, etc.) into entity/symbol records.

        Also remaps metrics keys to match fixed canonical_ids so the output
        metrics file uses the same IDs as the processed entities.
        """
        merged = 0
        remapped_entity_metrics = {}

        for ns_name, entries in self._entities.items():
            for entry in entries:
                cid = entry.get("canonical_id", "")
                old_cid = entry.get("_old_canonical_id", "")

                metrics = self._entity_metrics.get(cid)
                if not metrics and old_cid:
                    metrics = self._entity_metrics.get(old_cid)

                if metrics:
                    entry["boost"] = metrics.get("boost", 1.0)
                    entry["priority"] = metrics.get("priority", 0)
                    entry["frequency"] = metrics.get("frequency", 0)
                    entry["coverage"] = metrics.get("coverage", 0)
                    entry["total_score"] = metrics.get("total_score", 0)
                    entry["centrality"] = metrics.get("centrality", 0)
                    remapped_entity_metrics[cid] = metrics
                    merged += 1

        # Replace entity metrics with remapped keys
        if remapped_entity_metrics:
            self._entity_metrics = remapped_entity_metrics

        remapped_symbol_metrics = {}
        for ns_name, entries in self._symbols.items():
            for entry in entries:
                cid = entry.get("canonical_id", "")
                old_cid = entry.get("_old_canonical_id", "")

                metrics = self._symbol_metrics.get(cid)
                if not metrics and old_cid:
                    metrics = self._symbol_metrics.get(old_cid)

                if metrics:
                    entry["boost"] = metrics.get("boost", 1.0)
                    entry["priority"] = metrics.get("priority", 0)
                    entry["frequency"] = metrics.get("frequency", 0)
                    entry["coverage"] = metrics.get("coverage", 0)
                    entry["total_score"] = metrics.get("total_score", 0)
                    entry["meaning_richness"] = metrics.get("meaning_richness", 0)
                    remapped_symbol_metrics[cid] = metrics
                    merged += 1

        if remapped_symbol_metrics:
            self._symbol_metrics = remapped_symbol_metrics

        logger.info(f"  Metrics merged: {merged} records")

    # ── Step 6: Validate ──────────────────────────────────────────

    def _validate_refs(self):
        """Validate biblical references in key_refs fields."""
        ref_pattern = re.compile(
            r"^(?:(?:\d\s)?[A-Za-zÀ-ÿ]+)\s+\d+(?::\d+(?:-\d+)?)?$"
        )

        for ns_name, entries in self._entities.items():
            for entry in entries:
                for ref in entry.get("key_refs", []):
                    if not ref or not ref.strip():
                        continue
                    # Refs can be in various formats: "Exodus 4:14", "Numbers 26:59"
                    # We just validate they have a basic structure
                    cleaned = ref.strip()
                    if not ref_pattern.match(cleaned):
                        # Try simpler pattern for refs like "Gn 1:2"
                        simple = re.match(
                            r"^[A-Za-zÀ-ÿ0-9]+\s+\d+(?:[:.]\d+(?:-\d+)?)?$",
                            cleaned,
                        )
                        if not simple:
                            self._report.invalid_refs.append(
                                f"{entry.get('canonical_id', '?')}: '{ref}'"
                            )

        for ns_name, entries in self._symbols.items():
            for entry in entries:
                for example in entry.get("bible_examples", []):
                    ref = example.get("ref", "")
                    if ref and not re.match(r"^[A-Za-zÀ-ÿ0-9]+\s+\d+", ref.strip()):
                        self._report.invalid_refs.append(
                            f"{entry.get('canonical_id', '?')}: '{ref}'"
                        )

        logger.info(f"  Invalid refs found: {len(self._report.invalid_refs)}")

    def _validate_unique_ids(self):
        """Ensure all canonical_ids are unique within their domain."""
        entity_ids = Counter()
        for ns_name, entries in self._entities.items():
            for entry in entries:
                cid = entry.get("canonical_id", "")
                entity_ids[cid] += 1

        for cid, count in entity_ids.items():
            if count > 1:
                self._report.duplicate_ids.append(
                    f"Entity {cid}: {count} occurrences"
                )

        symbol_ids = Counter()
        for ns_name, entries in self._symbols.items():
            for entry in entries:
                cid = entry.get("canonical_id", "")
                symbol_ids[cid] += 1

        for cid, count in symbol_ids.items():
            if count > 1:
                self._report.duplicate_ids.append(
                    f"Symbol {cid}: {count} occurrences"
                )

        logger.info(f"  Duplicate IDs: {len(self._report.duplicate_ids)}")

    def _detect_alias_conflicts(self):
        """Detect when the same alias name maps to different entities."""
        alias_map: dict[str, list[str]] = defaultdict(list)  # alias → [canonical_ids]

        for ns_name, entries in self._entities.items():
            for entry in entries:
                cid = entry.get("canonical_id", "")
                name = entry.get("name", "").lower().strip()
                if name:
                    alias_map[name].append(cid)
                for alias in entry.get("aliases", []):
                    if alias:
                        alias_map[alias.lower().strip()].append(cid)

        for alias, cids in alias_map.items():
            unique_cids = list(set(cids))
            if len(unique_cids) > 1:
                self._report.alias_conflicts.append(
                    f"'{alias}' → {unique_cids}"
                )

        logger.info(f"  Alias conflicts: {len(self._report.alias_conflicts)}")

    def _validate_required_fields(self):
        """Check for missing required fields."""
        for ns_name, entries in self._entities.items():
            for entry in entries:
                cid = entry.get("canonical_id", "")
                if not entry.get("name"):
                    self._report.missing_fields.append(f"{cid}: missing 'name'")
                if not entry.get("description"):
                    self._report.missing_fields.append(f"{cid}: missing 'description'")
                if not entry.get("type"):
                    self._report.missing_fields.append(f"{cid}: missing 'type'")

        for ns_name, entries in self._symbols.items():
            for entry in entries:
                cid = entry.get("canonical_id", "")
                if not entry.get("name"):
                    self._report.missing_fields.append(f"{cid}: missing 'name'")

        logger.info(f"  Missing fields: {len(self._report.missing_fields)}")

    # ── Step 7: Write output ──────────────────────────────────────

    def _write_output(self):
        """Write all processed data to output directory."""
        # Clean output dir (with safety guard)
        if self.output_dir.exists():
            import shutil
            # Safety: only delete if it looks like our output (has _meta.json or is empty)
            has_meta = (self.output_dir / "_meta.json").exists()
            is_empty = not any(self.output_dir.iterdir())
            if has_meta or is_empty:
                shutil.rmtree(self.output_dir)
            else:
                raise RuntimeError(
                    f"Refusing to delete {self.output_dir}: no _meta.json found. "
                    "Delete manually or use a different output directory."
                )

        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "entities").mkdir()
        (self.output_dir / "symbols").mkdir()
        (self.output_dir / "metrics").mkdir()

        # Write entities
        entity_total = 0
        entity_meta = {}
        for ns_name, entries in sorted(self._entities.items()):
            # Clean internal fields before writing
            clean_entries = []
            for entry in entries:
                clean = {k: v for k, v in entry.items() if not k.startswith("_")}
                clean_entries.append(clean)

            filename = f"{ns_name.lower()}.json"
            filepath = self.output_dir / "entities" / filename
            self._write_json(filepath, clean_entries)
            entity_total += len(clean_entries)
            entity_meta[ns_name] = {
                "file": f"entities/{filename}",
                "count": len(clean_entries),
            }
            self._report.entity_counts[ns_name] = len(clean_entries)

        self._report.entities_total = entity_total

        # Write symbols
        symbol_total = 0
        symbol_meta = {}
        for ns_name, entries in sorted(self._symbols.items()):
            clean_entries = []
            for entry in entries:
                clean = {k: v for k, v in entry.items() if not k.startswith("_")}
                clean_entries.append(clean)

            filename = f"{ns_name.lower()}.json"
            filepath = self.output_dir / "symbols" / filename
            self._write_json(filepath, clean_entries)
            symbol_total += len(clean_entries)
            symbol_meta[ns_name] = {
                "file": f"symbols/{filename}",
                "count": len(clean_entries),
            }
            self._report.symbol_counts[ns_name] = len(clean_entries)

        self._report.symbols_total = symbol_total

        # Write relationships
        self._write_json(self.output_dir / "relationships.json", self._relationships)
        self._report.relationships_total = len(self._relationships)

        # Write unified aliases
        aliases_unified = self._build_alias_index()
        self._write_json(self.output_dir / "aliases_unified.json", aliases_unified)

        # Write metrics (copy through)
        if self._entity_metrics:
            self._write_json(
                self.output_dir / "metrics" / "entity_scores.json",
                self._entity_metrics,
            )
        if self._symbol_metrics:
            self._write_json(
                self.output_dir / "metrics" / "symbol_scores.json",
                self._symbol_metrics,
            )

        # Write _meta.json
        meta = {
            "version": "3.1.0",
            "lang": "pt",
            "processed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "source": str(self.source_dir),
            "tagger_index": str(self.tagger_index_path) if self.tagger_index_path else None,
            "entity_namespaces": entity_meta,
            "symbol_namespaces": symbol_meta,
            "total_entities": entity_total,
            "total_symbols": symbol_total,
            "total_relationships": len(self._relationships),
        }
        self._write_json(self.output_dir / "_meta.json", meta)

        # Write quality report
        self._write_json(
            self.output_dir / "quality_report.json",
            self._report.to_dict(),
        )

        logger.info(f"  Output written to {self.output_dir}")

    def _build_alias_index(self) -> dict:
        """Build unified alias index: name → [canonical_ids] for both EN and PT."""
        index: dict[str, list] = defaultdict(list)

        def _add_to_index(entries_by_ns: dict[str, list], kind: str):
            for ns_name, entries in entries_by_ns.items():
                for entry in entries:
                    cid = entry.get("canonical_id", "")
                    record = {"canonical_id": cid, "type": entry.get("type", ns_name), "kind": kind}

                    name = entry.get("name", "")
                    if name:
                        key = name.lower().strip()
                        if record not in index[key]:
                            index[key].append(record)

                    for alias in entry.get("aliases", []):
                        if alias:
                            key = alias.lower().strip()
                            if record not in index[key]:
                                index[key].append(record)

        _add_to_index(self._entities, "entity")
        _add_to_index(self._symbols, "symbol")

        # Count PT vs EN
        pt_count = 0
        for domain in (self._entities, self._symbols):
            for ns_name, entries in domain.items():
                for entry in entries:
                    pt_count += len(entry.get("aliases", [])) - len(entry.get("aliases_en", []))

        self._report.aliases_pt_existing = max(0, pt_count)

        return {
            "meta": {
                "total_names": len(index),
                "total_mappings": sum(len(v) for v in index.values()),
            },
            "index": dict(index),
        }

    # ── Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _merge_entity(target: dict, source: dict):
        """Merge source entity into target, keeping the richest data."""
        # Merge aliases
        existing = set(a.lower() for a in target.get("aliases", []))
        for alias in source.get("aliases", []):
            if alias and alias.lower() not in existing:
                target.setdefault("aliases", []).append(alias)
                existing.add(alias.lower())

        # Merge categories
        existing_cats = set(target.get("categories", []))
        for cat in source.get("categories", []):
            if cat not in existing_cats:
                target.setdefault("categories", []).append(cat)
                existing_cats.add(cat)

        # Merge key_refs
        existing_refs = set(target.get("key_refs", []))
        for ref in source.get("key_refs", []):
            if ref not in existing_refs:
                target.setdefault("key_refs", []).append(ref)
                existing_refs.add(ref)

        # Merge sources
        existing_src = set(target.get("sources", []))
        for src in source.get("sources", []):
            if src not in existing_src:
                target.setdefault("sources", []).append(src)
                existing_src.add(src)

        # Fill missing fields
        for field_name in ("description", "name_meaning", "canon", "type"):
            if not target.get(field_name) and source.get(field_name):
                target[field_name] = source[field_name]

    @staticmethod
    def _merge_symbol(target: dict, source: dict):
        """Merge source symbol into target."""
        # Merge aliases
        existing = set(a.lower() for a in target.get("aliases", []))
        for alias in source.get("aliases", []):
            if alias and alias.lower() not in existing:
                target.setdefault("aliases", []).append(alias)
                existing.add(alias.lower())

        # Merge symbolic_meaning
        existing_meanings = set(target.get("symbolic_meaning", []))
        for m in source.get("symbolic_meaning", []):
            if m not in existing_meanings:
                target.setdefault("symbolic_meaning", []).append(m)
                existing_meanings.add(m)

        # Merge bible_examples
        existing_refs = set(e.get("ref", "") for e in target.get("bible_examples", []))
        for ex in source.get("bible_examples", []):
            if ex.get("ref") not in existing_refs:
                target.setdefault("bible_examples", []).append(ex)
                existing_refs.add(ex.get("ref", ""))

        # Fill missing fields
        for field_name in ("literal_meaning", "type"):
            if not target.get(field_name) and source.get(field_name):
                target[field_name] = source[field_name]

    @staticmethod
    def _normalize_for_compare(text: str) -> str:
        """Normalize text for alias comparison: lowercase, strip accents, strip spaces."""
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")
        return text.lower().strip()

    @staticmethod
    def _slugify(text: str) -> str:
        """Create a normalized slug: lowercase, no accents, hyphens for spaces."""
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")
        text = text.lower().strip()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[-\s]+", "-", text)
        return text[:60]

    @staticmethod
    def _write_json(path: Path, data) -> None:
        """Write JSON with consistent formatting."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
