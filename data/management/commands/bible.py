"""
Bible Data Management - Simplified CLI

Replaces all complex data management commands with one simple, powerful tool.
Usage:
    python manage.py bible migrate [--source-dir DIR]
    python manage.py bible populate [--languages pt-BR,en-US] [--dry-run]
    python manage.py bible status
    python manage.py bible crossrefs [--file PATH]
"""
import time
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from common.data_core import BibleDataEngine


class Command(BaseCommand):
    help = "Unified Bible data management tool"

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest="subcommand", help="Available commands")

        # migrate - reorganize raw files
        migrate_parser = subparsers.add_parser("migrate", help="Migrate raw Bible files to organized structure")
        migrate_parser.add_argument("--source-dir", help="Source directory containing raw JSON files")
        migrate_parser.add_argument(
            "--min-confidence", type=float, default=0.6, help="Minimum language detection confidence"
        )
        migrate_parser.add_argument(
            "--dry-run", action="store_true", help="Show what would be done without making changes"
        )

        # populate - fill database
        populate_parser = subparsers.add_parser("populate", help="Populate database from processed Bible files")
        populate_parser.add_argument("--languages", help="Comma-separated language codes (e.g., pt-BR,en-US)")
        populate_parser.add_argument("--versions", help="Comma-separated version codes (e.g., NVI,KJV)")
        populate_parser.add_argument("--dry-run", action="store_true", help="Show what would be populated")
        populate_parser.add_argument("--clear-existing", action="store_true", help="Clear existing data first")

        # status - show current state
        status_parser = subparsers.add_parser("status", help="Show data pipeline status")
        status_parser.add_argument("--detailed", action="store_true", help="Show detailed information")

        # crossrefs - populate cross references
        crossrefs_parser = subparsers.add_parser("crossrefs", help="Populate cross references")
        crossrefs_parser.add_argument(
            "--file", default="data/external/cross-references.txt", help="Cross reference file path"
        )
        crossrefs_parser.add_argument(
            "--clear-existing", action="store_true", help="Clear existing cross references first"
        )

        # commentaries - populate commentary data
        commentaries_parser = subparsers.add_parser("commentaries", help="Populate commentary and author data")
        commentaries_parser.add_argument(
            "--languages", help="Languages to populate (comma-separated, default: pt-BR,en-US)"
        )
        commentaries_parser.add_argument(
            "--clear-existing", action="store_true", help="Clear existing commentaries first"
        )

        # cleanup - remove old/unused data
        cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old or unused data")
        cleanup_parser.add_argument("--languages", action="store_true", help="Remove unused languages")
        cleanup_parser.add_argument("--versions", help="Remove specific versions (comma-separated)")
        cleanup_parser.add_argument("--dry-run", action="store_true", help="Show what would be cleaned")

    def handle(self, *args, **options):
        subcommand = options.get("subcommand")

        if not subcommand:
            self.print_help("manage.py", "bible")
            return

        engine = BibleDataEngine()

        try:
            if subcommand == "migrate":
                self.handle_migrate(engine, options)
            elif subcommand == "populate":
                self.handle_populate(engine, options)
            elif subcommand == "status":
                self.handle_status(engine, options)
            elif subcommand == "crossrefs":
                self.handle_crossrefs(engine, options)
            elif subcommand == "commentaries":
                self.handle_commentaries(engine, options)
            elif subcommand == "cleanup":
                self.handle_cleanup(engine, options)
            else:
                raise CommandError(f"Unknown subcommand: {subcommand}")
        except Exception as e:
            raise CommandError(f"Command failed: {e}") from e

    def handle_migrate(self, engine: BibleDataEngine, options):
        """Handle file migration."""
        source_dir = options.get("source_dir")
        min_confidence = options["min_confidence"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No files will be moved"))

        self.stdout.write("Starting Bible file migration...")

        if not dry_run:
            result = engine.migrate_raw_files(source_dir, min_confidence)

            if result.success:
                count = result.items_processed
                self.stdout.write(self.style.SUCCESS(f"✓ Successfully migrated {count} Bible files"))
                self.stdout.write("Files organized in: data/processed/bibles/canonical/")
            else:
                self.stdout.write(self.style.ERROR(f"✗ Migration failed: {result.error_message}"))
        else:
            # Show what would be migrated
            external_dir = Path(source_dir) if source_dir else Path("data/external/multilingual-collection/raw")
            if external_dir.exists():
                json_files = list(external_dir.glob("*.json"))
                self.stdout.write(f"Would migrate {len(json_files)} JSON files:")
                for file_path in json_files[:10]:  # Show first 10
                    lang = engine.detect_language(file_path.name)
                    self.stdout.write(f"  {file_path.name} → {lang}")
                if len(json_files) > 10:
                    self.stdout.write(f"  ... and {len(json_files) - 10} more files")

    def handle_populate(self, engine: BibleDataEngine, options):
        """Handle database population."""
        languages = self._parse_comma_list(options.get("languages"))
        versions = self._parse_comma_list(options.get("versions"))
        dry_run = options["dry_run"]
        clear_existing = options["clear_existing"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No database changes will be made"))

        if clear_existing and not dry_run:
            self.stdout.write("Clearing existing Bible data...")
            from bible.models import Verse, Version

            with transaction.atomic():
                Verse.objects.all().delete()
                if not languages:  # Only clear versions if not filtering by language
                    Version.objects.all().delete()

        self.stdout.write("Starting Bible data population...")
        start_time = time.time()

        if not dry_run:
            result = engine.populate_all(languages)

            processing_time = time.time() - start_time

            if result.success:
                details = result.details
                self.stdout.write("\n" + "=" * 50)
                self.stdout.write("POPULATION COMPLETED SUCCESSFULLY")
                self.stdout.write("=" * 50)
                self.stdout.write(f'Versions processed: {details["total_versions"]}')
                self.stdout.write(f'Verses imported: {details["total_verses"]:,}')
                self.stdout.write(f"Processing time: {processing_time:.1f} seconds")

                if details["failed_versions"]:
                    self.stdout.write(f'\nFailed versions: {len(details["failed_versions"])}')
                    for version, error in details["failed_versions"]:
                        self.stdout.write(f"  ✗ {version}: {error}")
            else:
                self.stdout.write(self.style.ERROR(f"✗ Population failed: {result.error_message}"))
        else:
            # Show what would be populated
            processed_dir = Path("data/processed/bibles/canonical")
            if processed_dir.exists():
                version_count = 0
                versions_found = []

                for lang_dir in processed_dir.iterdir():
                    if not lang_dir.is_dir():
                        continue

                    # Apply language mapping like the engine does
                    lang_code = lang_dir.name
                    mapped_lang = self._map_language_code(lang_code)

                    if languages and mapped_lang not in languages:
                        continue

                    for version_dir in lang_dir.iterdir():
                        if not version_dir.is_dir():
                            continue

                        version_code = version_dir.name
                        if versions and version_code.upper() not in [v.upper() for v in versions]:
                            continue

                        # Check if JSON file exists
                        version_file = version_dir / f"{version_code}.json"
                        if version_file.exists():
                            version_count += 1
                            versions_found.append(f"{version_code} ({mapped_lang})")

                self.stdout.write(f"Would populate {version_count} Bible versions")
                if languages:
                    self.stdout.write(f'Language filter: {", ".join(languages)}')
                if versions:
                    self.stdout.write(f'Version filter: {", ".join(versions)}')
                if versions_found:
                    self.stdout.write("Versions found:")
                    for version in versions_found[:10]:  # Show first 10
                        self.stdout.write(f"  - {version}")
                    if len(versions_found) > 10:
                        self.stdout.write(f"  ... and {len(versions_found) - 10} more")

    def handle_status(self, engine: BibleDataEngine, options):
        """Handle status display."""
        detailed = options["detailed"]

        self.stdout.write("Bible Data Pipeline Status")
        self.stdout.write("=" * 40)

        status = engine.get_status()

        # Directories
        self.stdout.write("\nDirectories:")
        for name, info in status["directories"].items():
            icon = "✓" if info["exists"] else "✗"
            style = self.style.SUCCESS if info["exists"] else self.style.ERROR
            self.stdout.write(style(f'  {icon} {name}: {info["files"]} files'))

        # Database
        self.stdout.write("\nDatabase:")
        db = status["database"]
        self.stdout.write(f'  Languages: {db["languages"]}')
        self.stdout.write(f'  Versions: {db["versions"]}')
        self.stdout.write(f'  Verses: {db["verses"]:,}')
        self.stdout.write(f'  Cross References: {db["cross_references"]:,}')

        if detailed:
            # Show versions by language
            from bible.models import Language, Version

            self.stdout.write("\nVersions by Language:")
            for lang in Language.objects.all():
                versions = Version.objects.filter(language=lang)
                self.stdout.write(f"  {lang.code}: {versions.count()} versions")
                if versions.exists():
                    version_codes = [v.code for v in versions[:5]]
                    self.stdout.write(f'    {", ".join(version_codes)}{"..." if versions.count() > 5 else ""}')

    def handle_crossrefs(self, engine: BibleDataEngine, options):
        """Handle cross reference population."""
        crossref_file = options["file"]
        clear_existing = options["clear_existing"]

        if clear_existing:
            self.stdout.write("Clearing existing cross references...")
            from bible.models import CrossReference

            CrossReference.objects.all().delete()

        self.stdout.write(f"Populating cross references from: {crossref_file}")

        result = engine.populate_cross_references(crossref_file)

        if result.success:
            count = result.items_processed
            self.stdout.write(self.style.SUCCESS(f"✓ Successfully imported {count:,} cross references"))
        else:
            self.stdout.write(self.style.ERROR(f"✗ Cross reference import failed: {result.error_message}"))

    def handle_commentaries(self, engine: BibleDataEngine, options):
        """Handle commentary population."""
        languages = self._parse_comma_list(options.get("languages")) or ["pt-BR", "en-US"]
        clear_existing = options["clear_existing"]

        if clear_existing:
            self.stdout.write("Clearing existing commentaries and authors...")
            from bible.models import Author, CommentaryEntry, CommentarySource

            CommentaryEntry.objects.all().delete()
            CommentarySource.objects.all().delete()
            Author.objects.all().delete()

        self.stdout.write(f'Populating commentaries for languages: {", ".join(languages)}')

        result = engine.populate_commentaries(languages)

        if result.success:
            details = result.details
            entries = details.get("commentary_entries", 0)
            authors = details.get("authors", 0)

            self.stdout.write(self.style.SUCCESS(f"✓ Successfully imported {entries:,} commentary entries"))
            self.stdout.write(self.style.SUCCESS(f"✓ Successfully created {authors:,} authors"))
        else:
            self.stdout.write(self.style.ERROR(f"✗ Commentary import failed: {result.error_message}"))

    def handle_cleanup(self, engine: BibleDataEngine, options):
        """Handle data cleanup."""
        languages = options["languages"]
        versions = self._parse_comma_list(options.get("versions"))
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No data will be deleted"))

        cleanup_count = 0

        if languages:
            from bible.models import Language

            unused_languages = Language.objects.filter(versions__isnull=True)
            cleanup_count += unused_languages.count()

            if unused_languages.exists():
                self.stdout.write(f"Found {unused_languages.count()} unused languages:")
                for lang in unused_languages:
                    self.stdout.write(f"  - {lang.code}: {lang.name}")

                if not dry_run:
                    unused_languages.delete()
                    self.stdout.write(self.style.SUCCESS("✓ Removed unused languages"))

        if versions:
            from bible.models import Version

            versions_to_remove = Version.objects.filter(code__in=[v.upper() for v in versions])
            cleanup_count += versions_to_remove.count()

            if versions_to_remove.exists():
                self.stdout.write(f"Found {versions_to_remove.count()} versions to remove:")
                for version in versions_to_remove:
                    verse_count = version.verses.count()
                    self.stdout.write(f"  - {version.code}: {verse_count:,} verses")

                if not dry_run:
                    versions_to_remove.delete()
                    self.stdout.write(self.style.SUCCESS("✓ Removed specified versions"))

        if cleanup_count == 0:
            self.stdout.write("No cleanup needed")

    def _parse_comma_list(self, value: str | None) -> list[str] | None:
        """Parse comma-separated list."""
        if not value:
            return None
        return [item.strip() for item in value.split(",") if item.strip()]

    def _map_language_code(self, lang_code: str) -> str:
        """Map generic language codes to specific ones (same as engine)."""
        mapping = {
            "pt": "pt-BR",
            "en": "en-US",
            "de": "de-DE",
            "fr": "fr-FR",
            "es": "es-ES",
            "it": "it-IT",
            "nl": "nl-NL",
        }
        return mapping.get(lang_code, lang_code)
