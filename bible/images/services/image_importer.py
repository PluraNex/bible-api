"""
Import biblical images from WikiArt metadata and Gemini Vision tags.

Sources:
1. WikiArt metadata (16,914 JSONs) → Artist + BiblicalImage
2. Gemini Vision tags (2,999 JSONs) → ImageTag + ImageVerseLink
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from django.db import transaction
from django.db.models import Count

from bible.models import CanonicalBook
from bible.utils.osis_maps import parse_osis_ref

from ..models import Artist, BiblicalImage, ImageTag, ImageVerseLink

logger = logging.getLogger(__name__)

METADATA_PATH = Path("E:/bible-images-dataset/data/00_raw/wikiart/metadata")
TAGS_PATH = Path("C:/Users/Iury Coelho/Desktop/bible-image-tagger/data/output")


@dataclass
class ImportResult:
    artists_created: int = 0
    images_created: int = 0
    images_skipped: int = 0
    tags_created: int = 0
    verse_links_created: int = 0
    verse_links_skipped: int = 0
    errors: list = field(default_factory=list)
    duration_seconds: float = 0.0


class ImageImporter:

    def __init__(self, metadata_path: str | None = None, tags_path: str | None = None):
        self.metadata_path = Path(metadata_path) if metadata_path else METADATA_PATH
        self.tags_path = Path(tags_path) if tags_path else TAGS_PATH
        self._artist_cache: dict[str, Artist] = {}
        self._book_cache: dict[str, CanonicalBook | None] = {}

    # ─── Metadata Import ──────────────────────────────────

    def import_metadata(self, limit: int | None = None) -> ImportResult:
        """Import 16,914 WikiArt metadata → Artist + BiblicalImage."""
        result = ImportResult()
        start = time.time()

        if not self.metadata_path.exists():
            result.errors.append(f"Metadata path not found: {self.metadata_path}")
            return result

        files = sorted(self.metadata_path.glob("*.json"))
        if limit:
            files = files[:limit]

        logger.info(f"Importing {len(files)} image metadata files...")

        batch = []
        for i, filepath in enumerate(files):
            try:
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)

                artist = self._get_or_create_artist(data, result)
                if not artist:
                    continue

                key = data.get("key", "")
                if not key or BiblicalImage.objects.filter(key=key).exists():
                    result.images_skipped += 1
                    continue

                batch.append(BiblicalImage(
                    key=key,
                    title=data.get("title", "")[:500],
                    artist=artist,
                    completion_year=data.get("completion") if isinstance(data.get("completion"), int) else None,
                    styles=data.get("styles", []),
                    genres=data.get("genres", []),
                    media=data.get("media", []),
                    width=data.get("width"),
                    height=data.get("height"),
                    image_url=data.get("img_url", ""),
                    source="wikiart",
                ))

                if len(batch) >= 500:
                    BiblicalImage.objects.bulk_create(batch, ignore_conflicts=True)
                    result.images_created += len(batch)
                    batch = []
                    if (i + 1) % 5000 == 0:
                        logger.info(f"  {i + 1}/{len(files)} processed...")

            except Exception as e:
                result.errors.append(f"{filepath.name}: {e}")

        if batch:
            BiblicalImage.objects.bulk_create(batch, ignore_conflicts=True)
            result.images_created += len(batch)

        # Update artist image counts
        self._update_artist_counts()

        result.duration_seconds = time.time() - start
        return result

    def _get_or_create_artist(self, data: dict, result: ImportResult) -> Artist | None:
        artist_name = data.get("artist", "").strip()
        if not artist_name:
            return None

        if artist_name in self._artist_cache:
            return self._artist_cache[artist_name]

        artist, created = Artist.objects.get_or_create(
            name=artist_name,
            defaults={
                "birth_date": data.get("artist_birth", "") or "",
                "death_date": data.get("artist_death", "") or "",
                "nations": data.get("artist_nations", []),
                "movements": data.get("artist_movements", []),
                "source": "wikiart",
            },
        )
        if created:
            result.artists_created += 1

        self._artist_cache[artist_name] = artist
        return artist

    def _update_artist_counts(self):
        """Recalculate denormalized image_count for all artists."""
        for artist in Artist.objects.all():
            count = artist.images.count()
            if artist.image_count != count:
                artist.image_count = count
                artist.save(update_fields=["image_count"])

    # ─── Tags Import ──────────────────────────────────────

    def import_tags(self, limit: int | None = None) -> ImportResult:
        """Import 2,999 Gemini Vision tags → ImageTag + ImageVerseLink."""
        result = ImportResult()
        start = time.time()

        if not self.tags_path.exists():
            result.errors.append(f"Tags path not found: {self.tags_path}")
            return result

        files = sorted(self.tags_path.glob("*.json"))
        if limit:
            files = files[:limit]

        logger.info(f"Importing {len(files)} image tag files...")

        for i, filepath in enumerate(files):
            try:
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)

                self._import_tag(data, result)

                if (i + 1) % 1000 == 0:
                    logger.info(f"  {i + 1}/{len(files)} tags processed...")

            except Exception as e:
                result.errors.append(f"{filepath.name}: {e}")

        result.duration_seconds = time.time() - start
        return result

    @transaction.atomic
    def _import_tag(self, data: dict, result: ImportResult):
        """Import a single tag file."""
        meta = data.get("_meta", {})
        key = meta.get("key", "")

        if not key:
            return

        image = BiblicalImage.objects.filter(key=key).first()
        if not image:
            return

        # Skip if already tagged
        if ImageTag.objects.filter(image=image).exists():
            return

        tag = ImageTag.objects.create(
            image=image,
            characters=data.get("characters", []),
            event=data.get("event", "")[:500],
            tag_list=data.get("tags", []),
            symbols=data.get("symbols", []),
            description=data.get("description", ""),
            theological_description=data.get("theological_description", ""),
            scripture_refs=data.get("scripture_refs", []),
            scene_type=data.get("scene_type", "")[:50],
            moods=data.get("mood", []),
            period=data.get("period", "")[:100],
            tagging_model=meta.get("model", ""),
        )
        result.tags_created += 1

        # Mark image as tagged
        image.is_tagged = True
        image.save(update_fields=["is_tagged"])

        # Create verse links from scripture_refs
        for ref_data in data.get("scripture_refs", []):
            ref_str = ref_data.get("ref", "")
            osis_code, chapter, vs, ve = parse_osis_ref(ref_str)

            if not osis_code:
                result.verse_links_skipped += 1
                continue

            book = self._resolve_book(osis_code)
            if not book:
                result.verse_links_skipped += 1
                continue

            _, created = ImageVerseLink.objects.get_or_create(
                image=image,
                book=book,
                chapter=chapter,
                verse_start=vs,
                defaults={
                    "verse_end": ve,
                    "relevance_type": ref_data.get("relevance", "primary"),
                    "reason": ref_data.get("reason", ""),
                },
            )
            if created:
                result.verse_links_created += 1
            else:
                result.verse_links_skipped += 1

    def _resolve_book(self, osis_code: str) -> CanonicalBook | None:
        if osis_code in self._book_cache:
            return self._book_cache[osis_code]

        try:
            book = CanonicalBook.objects.get(osis_code=osis_code)
            self._book_cache[osis_code] = book
            return book
        except CanonicalBook.DoesNotExist:
            self._book_cache[osis_code] = None
            return None

    # ─── Status ───────────────────────────────────────────

    def get_status(self) -> dict:
        return {
            "artists": Artist.objects.count(),
            "images": BiblicalImage.objects.count(),
            "tagged": BiblicalImage.objects.filter(is_tagged=True).count(),
            "untagged": BiblicalImage.objects.filter(is_tagged=False).count(),
            "tags": ImageTag.objects.count(),
            "verse_links": ImageVerseLink.objects.count(),
        }
