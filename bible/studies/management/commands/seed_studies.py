"""
Management command to seed studies from validation README.md files using AI.

The AI reads the full README as a theologian would and composes a proper
narrative study article with the correct block types.

Usage:
    # Dry-run (no AI, just metadata)
    python manage.py seed_studies --dry-run

    # Seed single study (test)
    python manage.py seed_studies --filter=v3_hard_06

    # Seed all with GPT-4o (better quality)
    python manage.py seed_studies --model=gpt-4o

    # Seed all (default: gpt-4o-mini, faster/cheaper)
    python manage.py seed_studies
"""

import fnmatch
import time
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from bible.studies.models import Study
from bible.studies.services.study_seeder import (
    extract_metadata_only,
    parse_readme_with_ai,
)

User = get_user_model()

DEFAULT_SOURCE = r"C:\Users\Iury Coelho\Desktop\bible-hybrid-search\experiments\queries\validations"
DEFAULT_AUTHOR = "bible-api-curated"


class Command(BaseCommand):
    help = "Seed Study Hub with validation studies using AI to compose narrative articles"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-dir",
            type=str,
            default=DEFAULT_SOURCE,
            help="Path to validations directory",
        )
        parser.add_argument(
            "--author-username",
            type=str,
            default=DEFAULT_AUTHOR,
            help="Username for the curated studies author",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse metadata only (no AI calls, no DB writes)",
        )
        parser.add_argument(
            "--filter",
            type=str,
            default="v3_*",
            help="Glob pattern to filter study directories (default: v3_*)",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing studies with same validation ID",
        )
        parser.add_argument(
            "--model",
            type=str,
            default="gpt-4o-mini",
            help="OpenAI model to use (default: gpt-4o-mini)",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=1.0,
            help="Delay in seconds between AI calls (rate limiting)",
        )

    def handle(self, *args, **options):
        source_dir = Path(options["source_dir"])
        dry_run = options["dry_run"]
        pattern = options["filter"]
        overwrite = options["overwrite"]
        model = options["model"]
        delay = options["delay"]

        if not source_dir.exists():
            self.stderr.write(self.style.ERROR(f"Source directory not found: {source_dir}"))
            return

        # Get or create author
        if not dry_run:
            author, created = User.objects.get_or_create(
                username=options["author_username"],
                defaults={"is_active": True},
            )
            if created:
                self.stdout.write(f"Created system user: {author.username}")
        else:
            author = None

        # Find all validation directories
        dirs = sorted([
            d for d in source_dir.iterdir()
            if d.is_dir() and fnmatch.fnmatch(d.name, pattern)
        ])

        self.stdout.write(f"Found {len(dirs)} directories matching '{pattern}'")
        if not dry_run:
            self.stdout.write(f"Using model: {model}")

        created_count = 0
        skipped_count = 0
        error_count = 0

        for i, study_dir in enumerate(dirs):
            readme_path = study_dir / "README.md"
            if not readme_path.exists():
                self.stdout.write(self.style.WARNING(f"  SKIP {study_dir.name}: no README.md"))
                skipped_count += 1
                continue

            validation_id = study_dir.name

            # Check if already exists
            if not dry_run and not overwrite:
                if Study.objects.filter(source_validation_id=validation_id).exists():
                    self.stdout.write(f"  EXISTS {validation_id}")
                    skipped_count += 1
                    continue

            if dry_run:
                # Quick metadata extraction without AI
                try:
                    meta = extract_metadata_only(readme_path)
                    self.stdout.write(
                        f"  [{i+1}/{len(dirs)}] {meta['validation_id']}: "
                        f"\"{meta['title']}\" ({meta['study_type']}/{meta['difficulty']})"
                    )
                    created_count += 1
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"  ERROR {validation_id}: {e}"))
                    error_count += 1
                continue

            # AI-powered parsing
            try:
                self.stdout.write(f"  [{i+1}/{len(dirs)}] Processing {validation_id}...")
                result = parse_readme_with_ai(readme_path, model=model)

                title = result.get("title", validation_id)
                blocks = result.get("blocks", [])
                study_type = result.get("study_type", "freeform")
                difficulty = result.get("difficulty", "")
                description = result.get("description", result.get("query", ""))

                # Generate slug
                base_slug = slugify(title)[:180]
                slug = base_slug
                counter = 1
                while Study.objects.filter(slug=slug).exclude(
                    source_validation_id=validation_id
                ).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                # Create or update
                existing = Study.objects.filter(source_validation_id=validation_id).first()
                if existing and overwrite:
                    existing.title = title
                    existing.slug = slug
                    existing.study_type = study_type
                    existing.difficulty = difficulty
                    existing.blocks = blocks
                    existing.visibility = "public"
                    existing.is_published = True
                    existing.tags = [difficulty, study_type] if difficulty else [study_type]
                    existing.description = description
                    existing.save()
                    action = "UPDATE"
                else:
                    Study.objects.create(
                        slug=slug,
                        title=title,
                        author=author,
                        study_type=study_type,
                        difficulty=difficulty,
                        visibility="public",
                        blocks=blocks,
                        is_published=True,
                        source_validation_id=validation_id,
                        tags=[difficulty, study_type] if difficulty else [study_type],
                        description=description,
                        language="pt-BR",
                    )
                    action = "CREATE"

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  {action} {validation_id}: \"{title}\" → {len(blocks)} blocks"
                    )
                )
                created_count += 1

                # Rate limiting
                if delay > 0 and i < len(dirs) - 1:
                    time.sleep(delay)

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  ERROR {validation_id}: {e}"))
                error_count += 1

        # Summary
        self.stdout.write("")
        action = "Parsed" if dry_run else "Processed"
        self.stdout.write(self.style.SUCCESS(f"{action}: {created_count}"))
        if skipped_count:
            self.stdout.write(f"Skipped: {skipped_count}")
        if error_count:
            self.stdout.write(self.style.ERROR(f"Errors: {error_count}"))
