"""
Gazetteer Importer - Import entities and relationships from processed gazetteer data.

Reads from: data/processed/gazetteers/ (v3.1 per-namespace format)
Writes to: CanonicalEntity, EntityAlias, EntityRelationship
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from django.db import transaction

from bible.entities.models import (
    CanonicalEntity,
    EntityAlias,
    EntityNamespace,
    EntityRelationship,
    EntityStatus,
    RelationshipType,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class ImportStats:
    """Statistics for import operation."""

    entities_created: int = 0
    entities_updated: int = 0
    entities_skipped: int = 0
    aliases_created: int = 0
    relationships_created: int = 0
    relationships_skipped: int = 0
    errors: list = field(default_factory=list)
    duration_seconds: float = 0.0


class GazetteerImporter:
    """
    Import entities and relationships from processed gazetteer v3 data.

    Usage:
        importer = GazetteerImporter()  # defaults to data/processed/gazetteers/
        stats = importer.import_all()
    """

    # Mapping from gazetteer namespace → model namespace
    NAMESPACE_MAP = {
        "PERSON": EntityNamespace.PERSON,
        "DEITY": EntityNamespace.DEITY,
        "PLACE": EntityNamespace.PLACE,
        "ANGEL": EntityNamespace.ANGEL,
        "CONCEPT": EntityNamespace.CONCEPT,
        "OBJECT": EntityNamespace.OBJECT,
        "EVENT": EntityNamespace.EVENT,
        "LITERARY_WORK": EntityNamespace.LITERARY_WORK,
        "LITERARY_FORM": EntityNamespace.LITERARY_FORM,
        "GROUP": EntityNamespace.GROUP,
        "CREATURE": EntityNamespace.CREATURE,
        "PLANT": EntityNamespace.PLANT,
        "RITUAL": EntityNamespace.RITUAL,
    }

    # Mapping from gazetteer relationship types → model types
    RELATIONSHIP_MAP = {
        # Family
        "PARENT_OF": RelationshipType.PARENT_OF,
        "CHILD_OF": RelationshipType.CHILD_OF,
        "SIBLING": RelationshipType.SIBLING,
        "SIBLING_OF": RelationshipType.SIBLING,
        "SPOUSE_OF": RelationshipType.SPOUSE_OF,
        "ANCESTOR_OF": RelationshipType.ANCESTOR_OF,
        "DESCENDANT_OF": RelationshipType.DESCENDANT_OF,
        "FATHER_OF": RelationshipType.PARENT_OF,
        "MOTHER_OF": RelationshipType.PARENT_OF,
        "GRANDCHILD_OF": RelationshipType.DESCENDANT_OF,
        "GRANDFATHER_OF": RelationshipType.ANCESTOR_OF,
        "GRANDPARENT_OF": RelationshipType.ANCESTOR_OF,
        "UNCLE_OF": RelationshipType.ASSOCIATED_WITH,
        "RELATIVE_OF": RelationshipType.ASSOCIATED_WITH,
        # Social/Political
        "KING_OF": RelationshipType.KING_OF,
        "SUBJECT_OF": RelationshipType.SUBJECT_OF,
        "SERVANT_OF": RelationshipType.SERVANT_OF,
        "MASTER_OF": RelationshipType.MASTER_OF,
        "LEADER_OF": RelationshipType.LEADER_OF,
        "MEMBER_OF": RelationshipType.MEMBER_OF,
        "RULER_OF": RelationshipType.KING_OF,
        "RULED_BY": RelationshipType.SUBJECT_OF,
        "SUCCESSOR_OF": RelationshipType.SUCCESSOR_OF,
        "PREDECESSOR_OF": RelationshipType.PREDECESSOR_OF,
        "COLLABORATOR_OF": RelationshipType.ALLY_OF,
        "CONTEMPORARY_OF": RelationshipType.CONTEMPORARY_OF,
        # Spiritual
        "DISCIPLE_OF": RelationshipType.DISCIPLE_OF,
        "TEACHER_OF": RelationshipType.TEACHER_OF,
        "TEACHES": RelationshipType.TEACHER_OF,
        "MENTOR_OF": RelationshipType.TEACHER_OF,
        "ANOINTED_BY": RelationshipType.ANOINTED_BY,
        # Conflict
        "ENEMY_OF": RelationshipType.ENEMY_OF,
        "ALLY_OF": RelationshipType.ALLY_OF,
        "BETRAYED_BY": RelationshipType.BETRAYED_BY,
        "KILLED_BY": RelationshipType.KILLED_BY,
        "PERSECUTOR_OF": RelationshipType.PERSECUTOR_OF,
        "OPPOSED_BY": RelationshipType.ENEMY_OF,
        "CONTRASTS_WITH": RelationshipType.CONTRASTS,
        # Place
        "BORN_IN": RelationshipType.BORN_IN,
        "DIED_IN": RelationshipType.DIED_IN,
        "LIVED_IN": RelationshipType.LIVED_IN,
        "TRAVELED_TO": RelationshipType.TRAVELED_TO,
        "EXILED_TO": RelationshipType.EXILED_TO,
        "CONQUERED": RelationshipType.CONQUERED,
        "FOUNDED": RelationshipType.FOUNDED,
        "BUILT": RelationshipType.BUILT,
        "LOCATED_IN": RelationshipType.LIVED_IN,
        "NEAR": RelationshipType.ASSOCIATED_WITH,
        "CONTAINS": RelationshipType.PART_OF,
        "PART_OF": RelationshipType.PART_OF,
        "REGION_OF": RelationshipType.PART_OF,
        "CAPITAL_OF": RelationshipType.PART_OF,
        "ROUTE_TO": RelationshipType.ASSOCIATED_WITH,
        # Typological
        "TYPE_OF": RelationshipType.TYPE_OF,
        "ANTITYPE_OF": RelationshipType.ANTITYPE_OF,
        "FORESHADOWS": RelationshipType.FORESHADOWS,
        "FULFILLS": RelationshipType.FULFILLS,
        "FULFILLED_BY": RelationshipType.FULFILLS,
        "TYPIFIES": RelationshipType.TYPE_OF,
        "PARALLELS": RelationshipType.PARALLELS,
        "CONTRASTS": RelationshipType.CONTRASTS,
        # Association
        "ASSOCIATED_WITH": RelationshipType.ASSOCIATED_WITH,
        "RELATED_TO": RelationshipType.ASSOCIATED_WITH,
        "MANIFESTATION_OF": RelationshipType.TYPE_OF,
        "ASPECT_OF": RelationshipType.ASSOCIATED_WITH,
        "PROPHECY_ABOUT": RelationshipType.FORESHADOWS,
        "PROPHESIED_BY": RelationshipType.FORESHADOWS,
        # Actions
        "HEALED_BY": RelationshipType.ASSOCIATED_WITH,
        "HOSTED_BY": RelationshipType.ASSOCIATED_WITH,
        "FORTIFIED_BY": RelationshipType.BUILT,
        "CREATED_BY": RelationshipType.FOUNDED,
        "AUTHOR_OF": RelationshipType.ASSOCIATED_WITH,
        "RESULTED_IN": RelationshipType.ASSOCIATED_WITH,
        "PARTICIPANT_IN": RelationshipType.MEMBER_OF,
        "PROMISED_TO": RelationshipType.ASSOCIATED_WITH,
        "WORSHIPPED_AT": RelationshipType.ASSOCIATED_WITH,
    }

    def __init__(self, gazetteer_dir: str | Path | None = None):
        if gazetteer_dir is None:
            base_path = Path(__file__).resolve().parents[3]  # bible-api/
            gazetteer_dir = base_path / "data" / "processed" / "gazetteers"

        self.gazetteer_dir = Path(gazetteer_dir)
        self._entity_cache: dict[str, CanonicalEntity] = {}

    def import_all(self, update_existing: bool = False) -> ImportStats:
        """Import all entities + relationships from processed gazetteer data."""
        import time
        start_time = time.time()

        stats = ImportStats()

        # Import entities first
        entity_stats = self.import_entities(update_existing=update_existing)
        stats.entities_created = entity_stats.entities_created
        stats.entities_updated = entity_stats.entities_updated
        stats.entities_skipped = entity_stats.entities_skipped
        stats.aliases_created = entity_stats.aliases_created
        stats.errors.extend(entity_stats.errors)

        # Then import relationships (need entities to exist)
        rel_stats = self.import_relationships()
        stats.relationships_created = rel_stats.relationships_created
        stats.relationships_skipped = rel_stats.relationships_skipped
        stats.errors.extend(rel_stats.errors)

        stats.duration_seconds = time.time() - start_time
        return stats

    def import_entities(self, update_existing: bool = False) -> ImportStats:
        """Import entities from v3 per-namespace JSON files."""
        stats = ImportStats()

        meta_path = self.gazetteer_dir / "_meta.json"
        if not meta_path.exists():
            stats.errors.append(f"_meta.json not found in {self.gazetteer_dir}")
            return stats

        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)

        logger.info(f"Importing entities from {self.gazetteer_dir} (v{meta.get('version', '?')})")

        for ns_key, ns_info in meta.get("entity_namespaces", {}).items():
            namespace = self.NAMESPACE_MAP.get(ns_key)
            if not namespace:
                logger.warning(f"  Unknown namespace {ns_key}, skipping")
                continue

            filepath = self.gazetteer_dir / ns_info["file"]
            if not filepath.exists():
                stats.errors.append(f"File not found: {filepath}")
                continue

            with open(filepath, encoding="utf-8") as f:
                entries = json.load(f)

            logger.info(f"  {ns_key}: {len(entries)} entities")

            for entry in entries:
                try:
                    self._import_entity(entry, namespace, stats, update_existing)
                except Exception as e:
                    cid = entry.get("canonical_id", "?")
                    error_msg = f"Error importing {cid}: {e}"
                    logger.error(error_msg)
                    stats.errors.append(error_msg)

        logger.info(
            f"Entities import complete: "
            f"{stats.entities_created} created, "
            f"{stats.entities_updated} updated, "
            f"{stats.entities_skipped} skipped, "
            f"{stats.aliases_created} aliases"
        )
        return stats

    @transaction.atomic
    def _import_entity(
        self,
        entry: dict,
        namespace: str,
        stats: ImportStats,
        update_existing: bool,
    ):
        """Import a single entity from processed data."""
        canonical_id = entry.get("canonical_id", "")
        if not canonical_id:
            stats.entities_skipped += 1
            return

        name = entry.get("name", "")

        existing = CanonicalEntity.objects.filter(canonical_id=canonical_id).first()
        if existing and not update_existing:
            stats.entities_skipped += 1
            self._entity_cache[canonical_id] = existing
            self._entity_cache[name] = existing
            return

        defaults = {
            "namespace": namespace,
            "primary_name": name,
            "description": entry.get("description", ""),
            "description_pt": entry.get("description", ""),
            "boost": entry.get("boost") or 1.0,
            "priority": entry.get("priority") or 50,
            "categories": entry.get("categories", []),
            "status": EntityStatus.APPROVED,
            "source_gazetteer": "processed_gazetteers_v3",
        }

        entity, created = CanonicalEntity.objects.update_or_create(
            canonical_id=canonical_id,
            defaults=defaults,
        )

        if created:
            stats.entities_created += 1
        else:
            stats.entities_updated += 1

        self._entity_cache[canonical_id] = entity
        self._entity_cache[name] = entity

        # Import aliases with language tagging
        en_aliases = set(a.lower() for a in entry.get("aliases_en", []))
        all_aliases = entry.get("aliases", [])

        for alias_name in all_aliases:
            if not alias_name or alias_name == name:
                continue

            lang = "en" if alias_name.lower() in en_aliases else "pt"

            _, alias_created = EntityAlias.objects.get_or_create(
                entity=entity,
                name=alias_name,
                defaults={
                    "language_code": lang,
                    "is_primary": False,
                },
            )
            if alias_created:
                stats.aliases_created += 1

    def import_relationships(self) -> ImportStats:
        """Import relationships from processed relationships.json."""
        stats = ImportStats()

        rel_file = self.gazetteer_dir / "relationships.json"
        if not rel_file.exists():
            stats.errors.append(f"Relationships file not found: {rel_file}")
            return stats

        with open(rel_file, encoding="utf-8") as f:
            relationships = json.load(f)

        logger.info(f"Importing {len(relationships)} relationships")

        for rel_data in relationships:
            try:
                self._import_relationship(rel_data, stats)
            except Exception as e:
                error_msg = f"Error importing relationship: {e}"
                logger.error(error_msg)
                stats.errors.append(error_msg)

        logger.info(
            f"Relationships import complete: "
            f"{stats.relationships_created} created, "
            f"{stats.relationships_skipped} skipped"
        )
        return stats

    @transaction.atomic
    def _import_relationship(self, rel_data: dict, stats: ImportStats):
        """Import a single relationship."""
        source_name = rel_data.get("source", "")
        target_name = rel_data.get("target", "")
        rel_type = rel_data.get("type", "")

        if not source_name or not target_name or not rel_type:
            stats.relationships_skipped += 1
            return

        source_entity = self._find_entity(source_name)
        target_entity = self._find_entity(target_name)

        if not source_entity or not target_entity:
            stats.relationships_skipped += 1
            return

        mapped_type = self.RELATIONSHIP_MAP.get(rel_type, RelationshipType.ASSOCIATED_WITH)

        existing = EntityRelationship.objects.filter(
            source=source_entity,
            target=target_entity,
            relationship_type=mapped_type,
        ).exists()

        if existing:
            stats.relationships_skipped += 1
            return

        EntityRelationship.objects.create(
            source=source_entity,
            target=target_entity,
            relationship_type=mapped_type,
            description=rel_data.get("description", ""),
            description_pt=rel_data.get("description", ""),
            source_topic=rel_data.get("source_topic", ""),
        )
        stats.relationships_created += 1

    def _find_entity(self, name: str) -> CanonicalEntity | None:
        """Find entity by name, canonical_id, or alias."""
        if name in self._entity_cache:
            return self._entity_cache[name]

        # Try case-insensitive name match
        entity = CanonicalEntity.objects.filter(primary_name__iexact=name).first()
        if entity:
            self._entity_cache[name] = entity
            return entity

        # Try alias
        alias = EntityAlias.objects.filter(name__iexact=name).first()
        if alias:
            self._entity_cache[name] = alias.entity
            return alias.entity

        return None

    def get_status(self) -> dict:
        """Get current status of entities in database."""
        from django.db.models import Count

        total = CanonicalEntity.objects.count()
        by_namespace = dict(
            CanonicalEntity.objects.values("namespace")
            .annotate(count=Count("id"))
            .values_list("namespace", "count")
        )
        by_status = dict(
            CanonicalEntity.objects.values("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )
        relationships_count = EntityRelationship.objects.count()
        aliases_count = EntityAlias.objects.count()

        return {
            "total_entities": total,
            "by_namespace": by_namespace,
            "by_status": by_status,
            "relationships": relationships_count,
            "aliases": aliases_count,
        }
