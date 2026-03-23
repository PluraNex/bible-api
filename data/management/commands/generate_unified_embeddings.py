"""
Management command to generate unified verse embeddings from multiple Bible versions.

Combines embeddings from NAA, ARA, NVI (and other versions) to create more robust
semantic representations for improved search accuracy.

Examples:
  python manage.py generate_unified_embeddings \
    --versions=NAA,ARA,NVI \
    --strategy=weighted_average \
    --batch-size=64

  # Only update missing unified embeddings
  python manage.py generate_unified_embeddings \
    --versions=NAA,ARA \
    --only-missing \
    --dry-run

  # Custom fusion weights
  python manage.py generate_unified_embeddings \
    --versions=NAA,ARA,NVI \
    --weights=NAA:0.5,ARA:0.3,NVI:0.2

Fusion strategies:
  - weighted_average: Weighted combination (recommended)
  - simple_average: Equal weights for all versions
  - max_pooling: Element-wise maximum across versions
"""
import logging
import os
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import numpy as np
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from django.db.models import Q

from bible.models import UnifiedVerseEmbedding, Verse, VerseEmbedding

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate unified embeddings by fusing multiple Bible versions"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "--versions",
            type=str,
            default="NAA,ARA,NVI",
            help="Comma-separated list of version codes to fuse (default: NAA,ARA,NVI)"
        )
        parser.add_argument(
            "--weights",
            type=str,
            help="Custom weights as version:weight pairs (e.g. NAA:0.5,ARA:0.3,NVI:0.2)"
        )
        parser.add_argument(
            "--strategy",
            choices=["weighted_average", "simple_average", "max_pooling"],
            default="weighted_average",
            help="Fusion strategy (default: weighted_average)"
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Batch size for processing (default: 100)"
        )
        parser.add_argument(
            "--only-missing",
            action="store_true",
            help="Only generate missing unified embeddings"
        )
        parser.add_argument(
            "--force-update",
            action="store_true",
            help="Force update existing unified embeddings"
        )
        parser.add_argument(
            "--book-filter",
            type=str,
            help="Filter by book OSIS codes (e.g. 'Gen,Exod,Matt')"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without actually processing"
        )

    def handle(self, *args, **options):
        versions = [v.strip() for v in options["versions"].split(",")]
        strategy = options["strategy"]
        batch_size = options["batch_size"]
        only_missing = options["only_missing"]
        force_update = options["force_update"]
        book_filter = options.get("book_filter")
        dry_run = options["dry_run"]

        # Parse custom weights
        weights = self._parse_weights(options.get("weights"), versions)

        self.stdout.write(
            self.style.SUCCESS(
                f"🚀 Generating unified embeddings for versions: {', '.join(versions)}"
            )
        )
        self.stdout.write(f"Strategy: {strategy}")
        self.stdout.write(f"Weights: {weights}")
        self.stdout.write(f"Batch size: {batch_size}")

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN MODE - No changes will be made"))

        # Get candidate verses
        candidates = self._get_candidate_verses(
            versions, only_missing, force_update, book_filter
        )

        if not candidates:
            self.stdout.write(self.style.WARNING("No candidates found to process"))
            return

        self.stdout.write(f"Found {len(candidates)} verses to process")

        if dry_run:
            self._show_dry_run_summary(candidates, versions)
            return

        # Process in batches
        total_processed = 0
        total_created = 0
        total_updated = 0
        start_time = time.time()

        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i + batch_size]

            batch_created, batch_updated = self._process_batch(
                batch, versions, weights, strategy
            )

            total_processed += len(batch)
            total_created += batch_created
            total_updated += batch_updated

            self.stdout.write(
                f"Processed {total_processed}/{len(candidates)} "
                f"(+{batch_created} created, +{batch_updated} updated)"
            )

        duration = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Complete! Processed {total_processed} verses in {duration:.1f}s\n"
                f"   Created: {total_created}, Updated: {total_updated}"
            )
        )

    def _parse_weights(self, weights_str: Optional[str], versions: List[str]) -> Dict[str, float]:
        """Parse custom weights or use defaults."""
        if weights_str:
            weights = {}
            for pair in weights_str.split(","):
                version, weight = pair.split(":")
                weights[version.strip()] = float(weight)
            return weights

        # Default weights (favor NAA slightly)
        if "NAA" in versions and "ARA" in versions and "NVI" in versions:
            return {"NAA": 0.4, "ARA": 0.35, "NVI": 0.25}
        elif "NAA" in versions and "ARA" in versions:
            return {"NAA": 0.6, "ARA": 0.4}
        else:
            # Equal weights for unknown combinations
            weight = 1.0 / len(versions)
            return {v: weight for v in versions}

    def _get_candidate_verses(
        self,
        versions: List[str],
        only_missing: bool,
        force_update: bool,
        book_filter: Optional[str]
    ) -> List[str]:
        """Get list of canonical verse IDs that need processing."""

        # Get all canonical references that have embeddings in ALL required versions
        from collections import defaultdict

        canonical_verses = defaultdict(set)

        # Group verses by canonical reference and track which versions have embeddings
        verses_with_embeddings = (
            Verse.objects
            .filter(
                embedding__version_code__in=versions,
                embedding__embedding_small__isnull=False
            )
            .select_related("book", "version")
            .values("book__osis_code", "chapter", "number", "version__code")
            .distinct()
        )

        for verse_data in verses_with_embeddings:
            canonical_id = f"{verse_data['book__osis_code']}.{verse_data['chapter']}.{verse_data['number']}"
            canonical_verses[canonical_id].add(verse_data['version__code'])

        # Filter for verses that have ALL required versions
        valid_candidates = []
        for canonical_id, available_versions in canonical_verses.items():
            if set(versions).issubset(available_versions):
                valid_candidates.append(canonical_id)

        # Apply book filter
        if book_filter:
            book_codes = [b.strip() for b in book_filter.split(",")]
            valid_candidates = [
                cid for cid in valid_candidates
                if cid.split(".")[0] in book_codes
            ]

        # Filter based on existing unified embeddings
        if only_missing and not force_update:
            existing = set(
                UnifiedVerseEmbedding.objects
                .values_list("canonical_verse_id", flat=True)
            )
            valid_candidates = [cid for cid in valid_candidates if cid not in existing]
        elif not force_update:
            # Skip verses that already have unified embeddings with same versions
            # For now, skip if any unified embedding exists since we're starting fresh
            existing = set(
                UnifiedVerseEmbedding.objects
                .values_list("canonical_verse_id", flat=True)
            )
            valid_candidates = [cid for cid in valid_candidates if cid not in existing]

        return sorted(valid_candidates)

    def _show_dry_run_summary(self, candidates: List[str], versions: List[str]):
        """Show dry run summary."""
        self.stdout.write("\n📊 DRY RUN SUMMARY:")
        self.stdout.write(f"  Candidates: {len(candidates)}")

        if candidates:
            # Sample some examples
            sample_size = min(5, len(candidates))
            self.stdout.write(f"  Examples: {', '.join(candidates[:sample_size])}")
            if len(candidates) > sample_size:
                self.stdout.write(f"  ... and {len(candidates) - sample_size} more")

        # Show fusion cost estimate
        total_embeddings = len(candidates) * len(versions)
        self.stdout.write(f"  Total embeddings to process: {total_embeddings}")
        self.stdout.write(f"  Estimated processing time: {total_embeddings * 0.01:.1f}s")

    def _process_batch(
        self,
        canonical_ids: List[str],
        versions: List[str],
        weights: Dict[str, float],
        strategy: str
    ) -> Tuple[int, int]:
        """Process a batch of canonical verse IDs."""
        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for canonical_id in canonical_ids:
                try:
                    # Get embeddings for all versions
                    version_embeddings = self._get_version_embeddings(canonical_id, versions)

                    if not version_embeddings:
                        logger.warning(f"No embeddings found for {canonical_id}")
                        continue

                    # Fuse embeddings
                    unified_small, unified_large = self._fuse_embeddings(
                        version_embeddings, weights, strategy
                    )

                    # Calculate quality score
                    quality_score = self._calculate_quality_score(version_embeddings, weights)

                    # Create or update unified embedding
                    unified, created = UnifiedVerseEmbedding.objects.update_or_create(
                        canonical_verse_id=canonical_id,
                        defaults={
                            "source_versions": versions,
                            "version_weights": weights,
                            "unified_embedding_small": unified_small,
                            "unified_embedding_large": unified_large,
                            "fusion_strategy": strategy,
                            "quality_score": quality_score,
                        }
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                except Exception as e:
                    logger.error(f"Error processing {canonical_id}: {e}")
                    continue

        return created_count, updated_count

    def _get_version_embeddings(
        self, canonical_id: str, versions: List[str]
    ) -> Dict[str, Dict[str, List[float]]]:
        """Get embeddings for a canonical verse from all versions."""
        parts = canonical_id.split(".")
        osis_code, chapter, verse_number = parts[0], int(parts[1]), int(parts[2])

        embeddings = {}

        for version in versions:
            try:
                verse_embedding = (
                    VerseEmbedding.objects
                    .select_related("verse__book")
                    .get(
                        verse__book__osis_code=osis_code,
                        verse__chapter=chapter,
                        verse__number=verse_number,
                        version_code=version
                    )
                )

                embeddings[version] = {
                    "small": verse_embedding.embedding_small,
                    "large": verse_embedding.embedding_large,
                }
            except VerseEmbedding.DoesNotExist:
                logger.warning(f"Missing embedding for {canonical_id} in version {version}")
                continue

        return embeddings

    def _fuse_embeddings(
        self,
        version_embeddings: Dict[str, Dict[str, List[float]]],
        weights: Dict[str, float],
        strategy: str
    ) -> Tuple[List[float], Optional[List[float]]]:
        """Fuse embeddings from multiple versions."""

        # Get all small embeddings
        small_embeddings = []
        small_weights = []
        for version, emb_data in version_embeddings.items():
            if emb_data["small"]:
                small_embeddings.append(np.array(emb_data["small"]))
                small_weights.append(weights.get(version, 0.0))

        # Get all large embeddings (if available)
        large_embeddings = []
        large_weights = []
        for version, emb_data in version_embeddings.items():
            if emb_data["large"]:
                large_embeddings.append(np.array(emb_data["large"]))
                large_weights.append(weights.get(version, 0.0))

        # Fuse small embeddings
        unified_small = self._apply_fusion_strategy(
            small_embeddings, small_weights, strategy
        )

        # Fuse large embeddings (if available)
        unified_large = None
        if large_embeddings:
            unified_large = self._apply_fusion_strategy(
                large_embeddings, large_weights, strategy
            )

        return unified_small.tolist(), unified_large.tolist() if unified_large is not None else None

    def _apply_fusion_strategy(
        self,
        embeddings: List[np.ndarray],
        weights: List[float],
        strategy: str
    ) -> np.ndarray:
        """Apply the specified fusion strategy."""
        if not embeddings:
            raise ValueError("No embeddings to fuse")

        if strategy == "weighted_average":
            # Normalize weights
            total_weight = sum(weights)
            normalized_weights = [w / total_weight for w in weights]

            # Weighted average
            result = np.zeros_like(embeddings[0])
            for emb, weight in zip(embeddings, normalized_weights):
                result += emb * weight
            return result

        elif strategy == "simple_average":
            # Simple average
            return np.mean(embeddings, axis=0)

        elif strategy == "max_pooling":
            # Element-wise maximum
            return np.maximum.reduce(embeddings)

        else:
            raise ValueError(f"Unknown fusion strategy: {strategy}")

    def _calculate_quality_score(
        self,
        version_embeddings: Dict[str, Dict[str, List[float]]],
        weights: Dict[str, float]
    ) -> float:
        """Calculate quality score based on version coverage and weight distribution."""

        # Base score: percentage of versions that have embeddings
        available_versions = len(version_embeddings)
        total_versions = len(weights)
        coverage_score = available_versions / total_versions

        # Weight distribution score (higher entropy = better distribution)
        weight_values = list(weights.values())
        if len(weight_values) > 1:
            # Simple entropy approximation
            normalized_weights = np.array(weight_values) / sum(weight_values)
            entropy = -sum(w * np.log(w + 1e-10) for w in normalized_weights if w > 0)
            max_entropy = np.log(len(weight_values))
            distribution_score = entropy / max_entropy if max_entropy > 0 else 1.0
        else:
            distribution_score = 1.0

        # Combined score
        return (coverage_score * 0.7 + distribution_score * 0.3)