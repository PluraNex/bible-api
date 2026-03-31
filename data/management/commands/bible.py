"""
Bible Data Management - Simplified CLI

Replaces all complex data management commands with one simple, powerful tool.
Usage:
    python manage.py bible migrate [--source-dir DIR]
    python manage.py bible populate [--languages pt-BR,en-US] [--dry-run]
    python manage.py bible status
    python manage.py bible crossrefs [--file PATH]
    python manage.py bible topics import [--letter A] [--limit 100] [--update]
    python manage.py bible topics status
    python manage.py bible entities import [--update]
    python manage.py bible entities status
    python manage.py bible symbols import [--update]
    python manage.py bible symbols status
    python manage.py bible themes import [--catalog PATH] [--version PT_NAA] [--update]
    python manage.py bible themes status
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

        # commentaries - manage commentary data
        commentaries_parser = subparsers.add_parser("commentaries", help="Manage commentaries and authors")
        commentaries_subparsers = commentaries_parser.add_subparsers(dest="commentaries_action", help="Commentary actions")

        # commentaries import-authors
        comm_authors = commentaries_subparsers.add_parser("import-authors", help="Import authors from validated_authors.json")
        comm_authors.add_argument("--json", help="Path to validated_authors.json")
        comm_authors.add_argument("--update", action="store_true", help="Update existing authors")

        # commentaries import-entries
        comm_entries = commentaries_subparsers.add_parser("import-entries", help="Import Catena Bible commentary entries")
        comm_entries.add_argument("--catena-path", help="Path to Catena Bible dataset")
        comm_entries.add_argument("--limit", type=int, help="Limit entries to import")
        comm_entries.add_argument("--clear-existing", action="store_true", help="Clear existing entries first")

        # commentaries status
        commentaries_subparsers.add_parser("status", help="Show commentaries data status")

        # cleanup - remove old/unused data
        cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old or unused data")
        cleanup_parser.add_argument("--languages", action="store_true", help="Remove unused languages")
        cleanup_parser.add_argument("--versions", help="Remove specific versions (comma-separated)")
        cleanup_parser.add_argument("--dry-run", action="store_true", help="Show what would be cleaned")

        # topics - manage topical data
        topics_parser = subparsers.add_parser("topics", help="Manage topical Bible data")
        topics_subparsers = topics_parser.add_subparsers(dest="topics_action", help="Topics actions")

        # topics import
        topics_import = topics_subparsers.add_parser("import", help="Import topics from V3 dataset")
        topics_import.add_argument("--letter", help="Import only topics starting with this letter (e.g., A)")
        topics_import.add_argument("--slug", help="Import a single topic by slug (e.g., abraham)")
        topics_import.add_argument("--limit", type=int, help="Limit number of topics to import")
        topics_import.add_argument("--update", action="store_true", help="Update existing topics")

        # topics update (Phase 0 processed data)
        topics_update = topics_subparsers.add_parser("update", help="Update topics with Phase 0 processed data (AI aspects, entities, relationships)")
        topics_update.add_argument("--letter", help="Update only topics starting with this letter (e.g., A)")
        topics_update.add_argument("--limit", type=int, help="Limit number of topics to update")

        # topics status
        topics_subparsers.add_parser("status", help="Show topics data status")

        # entities - manage biblical entities from gazetteer
        entities_parser = subparsers.add_parser("entities", help="Manage biblical entities (people, places, etc.)")
        entities_subparsers = entities_parser.add_subparsers(dest="entities_action", help="Entities actions")

        # entities import
        entities_import = entities_subparsers.add_parser("import", help="Import entities from gazetteer")
        entities_import.add_argument("--update", action="store_true", help="Update existing entities")

        # entities populate-verse-links
        entities_vl = entities_subparsers.add_parser("populate-verse-links", help="Populate EntityVerseLink + SymbolOccurrence from key_refs")
        entities_vl.add_argument("--clear", action="store_true", help="Clear existing links first")
        entities_vl.add_argument("--version", default="ACF", help="Bible version to use (default: ACF)")

        # entities status
        entities_subparsers.add_parser("status", help="Show entities data status")

        # symbols - manage biblical symbols from gazetteer
        symbols_parser = subparsers.add_parser("symbols", help="Manage biblical symbols")
        symbols_subparsers = symbols_parser.add_subparsers(dest="symbols_action", help="Symbols actions")

        # symbols import
        symbols_import = symbols_subparsers.add_parser("import", help="Import symbols from gazetteer")
        symbols_import.add_argument("--update", action="store_true", help="Update existing symbols")

        # symbols status
        symbols_subparsers.add_parser("status", help="Show symbols data status")

        # themes - manage biblical themes from research catalog
        themes_parser = subparsers.add_parser("themes", help="Manage biblical themes from research catalog")
        themes_subparsers = themes_parser.add_subparsers(dest="themes_action", help="Themes actions")

        # themes import
        themes_import = themes_subparsers.add_parser("import", help="Import themes from verse-linking catalog")
        themes_import.add_argument("--catalog", help="Path to catalog.json (default: hybrid-search experiments)")
        themes_import.add_argument("--version", default="PT_NAA", help="Bible version code for verse lookup")
        themes_import.add_argument("--update", action="store_true", help="Update existing themes")

        # themes status
        themes_subparsers.add_parser("status", help="Show themes data status")

        # people - manage unified person hub
        people_parser = subparsers.add_parser("people", help="Manage unified Person identity hub")
        people_subparsers = people_parser.add_subparsers(dest="people_action", help="People actions")

        # people populate
        people_populate = people_subparsers.add_parser("populate", help="Populate Person hub from Authors and Entities")
        people_populate.add_argument("--update", action="store_true", help="Update existing Person records")

        # people status
        people_subparsers.add_parser("status", help="Show Person hub status")

        # images - manage biblical art images
        images_parser = subparsers.add_parser("images", help="Manage biblical art images")
        images_subparsers = images_parser.add_subparsers(dest="images_action", help="Images actions")

        # images import-metadata
        img_meta = images_subparsers.add_parser("import-metadata", help="Import WikiArt metadata (16K images)")
        img_meta.add_argument("--path", help="Path to metadata directory")
        img_meta.add_argument("--limit", type=int, help="Limit images to import")

        # images import-tags
        img_tags = images_subparsers.add_parser("import-tags", help="Import Gemini Vision tags (2K images)")
        img_tags.add_argument("--path", help="Path to tags directory")
        img_tags.add_argument("--limit", type=int, help="Limit tags to import")

        # images status
        images_subparsers.add_parser("status", help="Show images data status")

        # ai - AI enrichment pipeline
        ai_parser = subparsers.add_parser("ai", help="AI analysis and enrichment")
        ai_subparsers = ai_parser.add_subparsers(dest="ai_action", help="AI actions")

        # ai analyze
        ai_analyze = ai_subparsers.add_parser("analyze", help="AI-analyze chapter for entity/symbol context")
        ai_analyze.add_argument("--book", required=True, help="Book OSIS code (e.g., Gen)")
        ai_analyze.add_argument("--chapter", type=int, help="Chapter number (omit for all chapters)")
        ai_analyze.add_argument("--model", default="gpt-4o-mini", help="AI model to use")
        ai_analyze.add_argument("--force", action="store_true", help="Re-analyze even if already done")

        # ai status
        ai_subparsers.add_parser("status", help="Show AI analysis status")

        # integration - cross-domain matching
        int_parser = subparsers.add_parser("integration", help="Cross-domain image↔entity matching")
        int_subparsers = int_parser.add_subparsers(dest="integration_action", help="Integration actions")

        # integration match-images
        int_match = int_subparsers.add_parser("match-images", help="Match image characters to entities")
        int_match.add_argument("--clear", action="store_true", help="Clear existing links before matching")

        # integration status
        int_subparsers.add_parser("status", help="Show matching status")

        # gazetteers - data quality pipeline
        gaz_parser = subparsers.add_parser("gazetteers", help="Gazetteer data quality pipeline")
        gaz_subparsers = gaz_parser.add_subparsers(dest="gazetteers_action", help="Gazetteers actions")

        # gazetteers process
        gaz_process = gaz_subparsers.add_parser("process", help="Clean, merge, and validate gazetteer data")
        gaz_process.add_argument("--source", help="Path to bible-gazetteers-dataset/data/pt/")
        gaz_process.add_argument("--tagger-index", help="Path to gazetteer_index.json from image tagger")
        gaz_process.add_argument("--output", help="Output directory (default: data/processed/gazetteers/)")

        # gazetteers status
        gaz_subparsers.add_parser("status", help="Show processed gazetteer status")

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
                self.handle_commentaries(options)
            elif subcommand == "cleanup":
                self.handle_cleanup(engine, options)
            elif subcommand == "topics":
                self.handle_topics(options)
            elif subcommand == "entities":
                self.handle_entities(options)
            elif subcommand == "symbols":
                self.handle_symbols(options)
            elif subcommand == "themes":
                self.handle_themes(options)
            elif subcommand == "people":
                self.handle_people(options)
            elif subcommand == "images":
                self.handle_images(options)
            elif subcommand == "ai":
                self.handle_ai(options)
            elif subcommand == "integration":
                self.handle_integration(options)
            elif subcommand == "gazetteers":
                self.handle_gazetteers(options)
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

    def handle_commentaries(self, options):
        """Handle commentary management commands."""
        action = options.get("commentaries_action")

        if not action:
            self.stdout.write("Available commentaries actions: import-authors, import-entries, status")
            return

        if action == "import-authors":
            self._handle_commentaries_import_authors(options)
        elif action == "import-entries":
            self._handle_commentaries_import_entries(options)
        elif action == "status":
            self._handle_commentaries_status()
        else:
            raise CommandError(f"Unknown commentaries action: {action}")

    def _handle_commentaries_import_authors(self, options):
        """Import authors from validated_authors.json."""
        from bible.commentaries.services import CatenaImporter

        json_path = options.get("json")
        update = options.get("update", False)

        importer = CatenaImporter(authors_json=json_path)

        self.stdout.write(f"Importing authors from {importer.authors_json}...")
        result = importer.import_authors(update_existing=update)

        self.stdout.write(self.style.SUCCESS(f"\n✓ Authors imported in {result.duration_seconds:.1f}s"))
        self.stdout.write(f"  Created: {result.authors_created:,}")
        self.stdout.write(f"  Updated: {result.authors_updated:,}")
        self.stdout.write(f"  Skipped: {result.authors_skipped:,}")

        if result.errors:
            self.stdout.write(self.style.WARNING(f"\n⚠ {len(result.errors)} errors:"))
            for err in result.errors[:10]:
                self.stdout.write(f"  - {err}")

    def _handle_commentaries_import_entries(self, options):
        """Import commentary entries from Catena Bible dataset."""
        from bible.commentaries.services import CatenaImporter

        catena_path = options.get("catena_path")
        limit = options.get("limit")
        clear = options.get("clear_existing", False)

        if clear:
            from bible.commentaries.models import CommentaryEntry
            count = CommentaryEntry.objects.count()
            CommentaryEntry.objects.all().delete()
            self.stdout.write(f"Cleared {count:,} existing entries")

        importer = CatenaImporter(catena_base=catena_path)

        self.stdout.write(f"Importing entries from {importer.catena_base}...")
        if limit:
            self.stdout.write(f"  Limit: {limit:,}")

        result = importer.import_entries(limit=limit)

        self.stdout.write(self.style.SUCCESS(f"\n✓ Entries imported in {result.duration_seconds:.1f}s"))
        self.stdout.write(f"  Created: {result.entries_created:,}")
        self.stdout.write(f"  Skipped: {result.entries_skipped:,}")
        self.stdout.write(f"  Books not found: {result.books_not_found:,}")

        if result.errors:
            self.stdout.write(self.style.WARNING(f"\n⚠ {len(result.errors)} errors:"))
            for err in result.errors[:10]:
                self.stdout.write(f"  - {err}")

    def _handle_commentaries_status(self):
        """Show commentaries data status."""
        from bible.commentaries.models import Author, CommentaryEntry, CommentarySource

        self.stdout.write("\n📜 Commentaries Data Status")
        self.stdout.write("=" * 50)
        self.stdout.write(f"\n💾 Database:")
        self.stdout.write(f"   Authors: {Author.objects.count():,}")
        self.stdout.write(f"   Sources: {CommentarySource.objects.count():,}")
        self.stdout.write(f"   Entries: {CommentaryEntry.objects.count():,}")

        if Author.objects.exists():
            from django.db.models import Count
            by_type = Author.objects.values("author_type").annotate(count=Count("id")).order_by("-count")
            self.stdout.write(f"\n📊 Authors by type:")
            for entry in by_type:
                self.stdout.write(f"   {entry['author_type']}: {entry['count']:,}")

        for source in CommentarySource.objects.all():
            count = CommentaryEntry.objects.filter(source=source).count()
            self.stdout.write(f"\n📖 {source.name} [{source.short_code}]: {count:,} entries")

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

    def handle_topics(self, options):
        """Handle topics management commands."""
        action = options.get("topics_action")

        if not action:
            self.stdout.write("Available topics actions: import, update, status")
            return

        if action == "import":
            self._handle_topics_import(options)
        elif action == "update":
            self._handle_topics_update(options)
        elif action == "status":
            self._handle_topics_status()
        else:
            raise CommandError(f"Unknown topics action: {action}")

    def _handle_topics_import(self, options):
        """Handle topics import from V3 dataset."""
        from bible.topics.services import TopicImporter

        letter = options.get("letter")
        slug = options.get("slug")
        limit = options.get("limit")
        update_existing = options.get("update", False)

        importer = TopicImporter()

        if slug:
            self.stdout.write(f"Importing single topic: {slug}")
            result = importer.import_single(slug, update_existing=update_existing)
        elif letter:
            self.stdout.write(f"Importing topics for letter: {letter.upper()}")
            result = importer.import_letter(letter.upper(), update_existing=update_existing)
        else:
            self.stdout.write("Importing all topics from V3 dataset...")
            result = importer.import_all(update_existing=update_existing, limit=limit)

        if result.success:
            stats = result.stats
            self.stdout.write(self.style.SUCCESS(
                f"\n✓ Import completed in {result.duration_seconds:.1f}s"
            ))
            self.stdout.write(f"  Topics created: {stats.topics_created:,}")
            self.stdout.write(f"  Topics updated: {stats.topics_updated:,}")
            self.stdout.write(f"  Topics skipped: {stats.topics_skipped:,}")
            self.stdout.write(f"  Aspects created: {stats.aspects_created:,}")
            self.stdout.write(f"  Definitions created: {stats.definitions_created:,}")
            self.stdout.write(f"  Verses linked: {stats.verses_linked:,}")
            self.stdout.write(f"  Themes linked: {stats.themes_linked:,}")
            self.stdout.write(f"  Cross-refs linked: {stats.crossrefs_linked:,}")

            if stats.errors:
                self.stdout.write(self.style.WARNING(
                    f"\n⚠️ {len(stats.errors)} errors during import"
                ))
                for err in stats.errors[:10]:
                    self.stdout.write(f"  - {err}")
                if len(stats.errors) > 10:
                    self.stdout.write(f"  ... and {len(stats.errors) - 10} more errors")
        else:
            self.stdout.write(self.style.ERROR(
                f"✗ Import failed: {result.error_message}"
            ))

    def _handle_topics_update(self, options):
        """Handle topics update from Phase 0 processed data."""
        from bible.topics.services import TopicImporter

        letter = options.get("letter")
        limit = options.get("limit")

        importer = TopicImporter()

        if letter:
            self.stdout.write(f"Updating topics for letter: {letter.upper()} with Phase 0 data...")
        else:
            self.stdout.write("Updating all topics with Phase 0 processed data...")

        result = importer.update_from_processed(limit=limit, letter=letter)

        if result.success:
            stats = result.stats
            self.stdout.write(self.style.SUCCESS(
                f"\n✓ Update completed in {result.duration_seconds:.1f}s"
            ))
            self.stdout.write(f"  Topics updated: {stats.topics_updated:,}")
            self.stdout.write(f"  Topics skipped: {stats.topics_skipped:,}")
            self.stdout.write(f"  AI aspects created: {stats.ai_aspects_created:,}")
            self.stdout.write(f"  Entities linked: {stats.entities_linked:,}")
            self.stdout.write(f"  Relationships created: {stats.relationships_created:,}")

            if stats.errors:
                self.stdout.write(self.style.WARNING(
                    f"\n⚠️ {len(stats.errors)} errors during update"
                ))
                for err in stats.errors[:10]:
                    self.stdout.write(f"  - {err}")
                if len(stats.errors) > 10:
                    self.stdout.write(f"  ... and {len(stats.errors) - 10} more errors")
        else:
            self.stdout.write(self.style.ERROR(
                f"✗ Update failed: {result.error_message}"
            ))

    def _handle_topics_status(self):
        """Show topics data status."""
        from pathlib import Path

        from bible.models import (
            Topic,
            TopicAspect,
            TopicContent,
            TopicCrossReference,
            TopicDefinition,
            TopicName,
            TopicThemeLink,
            TopicVerse,
        )

        self.stdout.write("\n📚 Topics Data Status")
        self.stdout.write("=" * 50)

        # Dataset info
        dataset_path = Path("data/dataset/topics_v3")
        if dataset_path.exists():
            index_file = dataset_path / "_index.json"
            if index_file.exists():
                import json
                with open(index_file) as f:
                    index = json.load(f)
                self.stdout.write(f"\n📁 Dataset (V3):")
                self.stdout.write(f"   Total entries: {index.get('total_entries', 0):,}")
                by_type = index.get("by_type", {})
                self.stdout.write(f"   Dictionary: {by_type.get('dictionary', 0):,}")
                self.stdout.write(f"   Topic: {by_type.get('topic', 0):,}")
                self.stdout.write(f"   Both: {by_type.get('both', 0):,}")
        else:
            self.stdout.write(self.style.WARNING("\n⚠️ Dataset not found at data/dataset/topics_v3"))

        # Database counts
        self.stdout.write(f"\n💾 Database:")
        self.stdout.write(f"   Topics: {Topic.objects.count():,}")
        self.stdout.write(f"   Topic Names: {TopicName.objects.count():,}")
        self.stdout.write(f"   Topic Contents: {TopicContent.objects.count():,}")
        self.stdout.write(f"   Definitions: {TopicDefinition.objects.count():,}")
        self.stdout.write(f"   Aspects: {TopicAspect.objects.count():,}")
        self.stdout.write(f"   Verse Links: {TopicVerse.objects.count():,}")
        self.stdout.write(f"   Theme Links: {TopicThemeLink.objects.count():,}")
        self.stdout.write(f"   Cross-Ref Links: {TopicCrossReference.objects.count():,}")

        # AI enrichment stats
        ai_enriched = Topic.objects.filter(ai_enriched=True).count()
        total = Topic.objects.count()
        if total > 0:
            pct = (ai_enriched / total) * 100
            self.stdout.write(f"\n🤖 AI Enrichment:")
            self.stdout.write(f"   Enriched: {ai_enriched:,} / {total:,} ({pct:.1f}%)")

        # By type
        self.stdout.write(f"\n📊 By Type:")
        for choice in Topic.TopicType.choices:
            count = Topic.objects.filter(topic_type=choice[0]).count()
            if count > 0:
                self.stdout.write(f"   {choice[1]}: {count:,}")

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

    # ==================== ENTITIES ====================

    def handle_entities(self, options):
        """Handle entities management commands."""
        action = options.get("entities_action")

        if not action:
            self.stdout.write("Available entities actions: import, status")
            return

        if action == "import":
            self._handle_entities_import(options)
        elif action == "populate-verse-links":
            self._handle_entities_populate_verse_links(options)
        elif action == "status":
            self._handle_entities_status()
        else:
            raise CommandError(f"Unknown entities action: {action}")

    def _handle_entities_import(self, options):
        """Handle entities import from gazetteer."""
        from bible.entities.services import GazetteerImporter

        update_existing = options.get("update", False)

        importer = GazetteerImporter()

        self.stdout.write("Importing entities from gazetteer...")
        result = importer.import_all(update_existing=update_existing)

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Import completed in {result.duration_seconds:.1f}s"
        ))
        self.stdout.write(f"  Entities created: {result.entities_created:,}")
        self.stdout.write(f"  Entities updated: {result.entities_updated:,}")
        self.stdout.write(f"  Entities skipped: {result.entities_skipped:,}")
        self.stdout.write(f"  Aliases created: {result.aliases_created:,}")
        self.stdout.write(f"  Relationships created: {result.relationships_created:,}")
        self.stdout.write(f"  Relationships skipped: {result.relationships_skipped:,}")

        if result.errors:
            self.stdout.write(self.style.WARNING(
                f"\n⚠️ {len(result.errors)} errors during import"
            ))
            for err in result.errors[:10]:
                self.stdout.write(f"  - {err}")
            if len(result.errors) > 10:
                self.stdout.write(f"  ... and {len(result.errors) - 10} more errors")

    def _handle_entities_populate_verse_links(self, options):
        """Populate EntityVerseLink + SymbolOccurrence from key_refs."""
        from bible.entities.services.verse_link_populator import VerseLinkPopulator

        clear = options.get("clear", False)
        version = options.get("version", "ACF")

        populator = VerseLinkPopulator(version_code=version)

        self.stdout.write(f"Populating verse links (version={version})...")
        stats = populator.populate_all(clear_existing=clear)

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Population completed in {stats.duration_seconds:.1f}s"
        ))
        self.stdout.write(f"  Refs parsed: {stats.refs_parsed:,}")
        self.stdout.write(f"  Refs failed: {stats.refs_failed:,}")
        self.stdout.write(f"  Verses not found: {stats.verses_not_found:,}")
        self.stdout.write(f"  Entity links created: {stats.entity_links_created:,}")
        self.stdout.write(f"  Entity links skipped: {stats.entity_links_skipped:,}")
        self.stdout.write(f"  Symbol occurrences created: {stats.symbol_occurrences_created:,}")
        self.stdout.write(f"  Symbol occurrences skipped: {stats.symbol_occurrences_skipped:,}")

        if stats.errors:
            self.stdout.write(self.style.WARNING(f"\n⚠ {len(stats.errors)} errors"))
            for err in stats.errors[:5]:
                self.stdout.write(f"  - {err}")

    def _handle_entities_status(self):
        """Show entities data status."""
        from bible.entities.services import GazetteerImporter

        importer = GazetteerImporter()
        status = importer.get_status()

        self.stdout.write("\n👤 Entities Data Status")
        self.stdout.write("=" * 50)

        self.stdout.write(f"\n💾 Database:")
        self.stdout.write(f"   Total Entities: {status['total_entities']:,}")
        self.stdout.write(f"   Aliases: {status['aliases']:,}")
        self.stdout.write(f"   Relationships: {status['relationships']:,}")

        if status['by_namespace']:
            self.stdout.write(f"\n📊 By Namespace:")
            for ns, count in sorted(status['by_namespace'].items()):
                self.stdout.write(f"   {ns}: {count:,}")

        if status['by_status']:
            self.stdout.write(f"\n📋 By Status:")
            for st, count in sorted(status['by_status'].items()):
                self.stdout.write(f"   {st}: {count:,}")

    # ==================== SYMBOLS ====================

    def handle_symbols(self, options):
        """Handle symbols management commands."""
        action = options.get("symbols_action")

        if not action:
            self.stdout.write("Available symbols actions: import, status")
            return

        if action == "import":
            self._handle_symbols_import(options)
        elif action == "status":
            self._handle_symbols_status()
        else:
            raise CommandError(f"Unknown symbols action: {action}")

    def _handle_symbols_import(self, options):
        """Handle symbols import from gazetteer."""
        from bible.symbols.services import SymbolsImporter

        update_existing = options.get("update", False)

        importer = SymbolsImporter()

        self.stdout.write("Importing symbols from gazetteer...")
        result = importer.import_all(update_existing=update_existing)

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Import completed in {result.duration_seconds:.1f}s"
        ))
        self.stdout.write(f"  Symbols created: {result.symbols_created:,}")
        self.stdout.write(f"  Symbols updated: {result.symbols_updated:,}")
        self.stdout.write(f"  Symbols skipped: {result.symbols_skipped:,}")
        self.stdout.write(f"  Meanings created: {result.meanings_created:,}")

        if result.errors:
            self.stdout.write(self.style.WARNING(
                f"\n⚠️ {len(result.errors)} errors during import"
            ))
            for err in result.errors[:10]:
                self.stdout.write(f"  - {err}")
            if len(result.errors) > 10:
                self.stdout.write(f"  ... and {len(result.errors) - 10} more errors")

    def _handle_symbols_status(self):
        """Show symbols data status."""
        from bible.symbols.services import SymbolsImporter

        importer = SymbolsImporter()
        status = importer.get_status()

        self.stdout.write("\n🔮 Symbols Data Status")
        self.stdout.write("=" * 50)

        self.stdout.write(f"\n💾 Database:")
        self.stdout.write(f"   Total Symbols: {status['total_symbols']:,}")
        self.stdout.write(f"   Meanings: {status['meanings']:,}")

        if status['by_namespace']:
            self.stdout.write(f"\n📊 By Namespace:")
            for ns, count in sorted(status['by_namespace'].items()):
                self.stdout.write(f"   {ns}: {count:,}")

        if status['by_status']:
            self.stdout.write(f"\n📋 By Status:")
            for st, count in sorted(status['by_status'].items()):
                self.stdout.write(f"   {st}: {count:,}")

    # ──────────────────────────────────────────────────
    # THEMES
    # ──────────────────────────────────────────────────

    def handle_themes(self, options):
        """Handle themes management commands."""
        action = options.get("themes_action")

        if not action:
            self.stdout.write("Available themes actions: import, status")
            return

        if action == "import":
            self._handle_themes_import(options)
        elif action == "status":
            self._handle_themes_status()
        else:
            raise CommandError(f"Unknown themes action: {action}")

    def _handle_themes_import(self, options):
        """Import themes from verse-linking catalog."""
        from bible.themes.services import CatalogImporter

        catalog_path = options.get("catalog")
        version_code = options.get("version", "PT_NAA")
        update_existing = options.get("update", False)

        importer = CatalogImporter(catalog_path=catalog_path, version_code=version_code)

        self.stdout.write(f"Importing themes from {importer.catalog_path}...")
        self.stdout.write(f"  Version: {version_code}")
        self.stdout.write(f"  Update existing: {update_existing}")

        result = importer.import_catalog(update_existing=update_existing)

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Import completed in {result.duration_seconds:.1f}s"
        ))
        self.stdout.write(f"  Themes created: {result.themes_created:,}")
        self.stdout.write(f"  Themes updated: {result.themes_updated:,}")
        self.stdout.write(f"  Themes skipped: {result.themes_skipped:,}")
        self.stdout.write(f"  Verse links created: {result.verse_links_created:,}")
        self.stdout.write(f"  Verse links skipped: {result.verse_links_skipped:,}")
        self.stdout.write(f"  Verses not found: {result.verses_not_found:,}")

        if result.errors:
            self.stdout.write(self.style.WARNING(
                f"\n⚠️ {len(result.errors)} errors during import"
            ))
            for err in result.errors[:10]:
                self.stdout.write(f"  - {err}")
            if len(result.errors) > 10:
                self.stdout.write(f"  ... and {len(result.errors) - 10} more errors")

    def _handle_themes_status(self):
        """Show themes data status."""
        from bible.themes.models import Theme, ThemeVerseLink

        total_themes = Theme.objects.count()
        total_links = ThemeVerseLink.objects.count()

        self.stdout.write("\n📖 Themes Data Status")
        self.stdout.write("=" * 50)
        self.stdout.write(f"\n💾 Database:")
        self.stdout.write(f"   Total Themes: {total_themes:,}")
        self.stdout.write(f"   Total Verse Links: {total_links:,}")

        if total_themes > 0:
            from django.db.models import Avg, Count

            stats = Theme.objects.aggregate(
                avg_score=Avg("evidence_score"),
                avg_verses=Avg("verse_count"),
            )
            self.stdout.write(f"   Avg Evidence Score: {stats['avg_score']:.3f}" if stats['avg_score'] else "")
            self.stdout.write(f"   Avg Verses/Theme: {stats['avg_verses']:.1f}" if stats['avg_verses'] else "")

            by_status = Theme.objects.values("status").annotate(count=Count("id")).order_by("status")
            if by_status:
                self.stdout.write(f"\n📊 By Status:")
                for entry in by_status:
                    self.stdout.write(f"   {entry['status']}: {entry['count']:,}")

            grade_dist = ThemeVerseLink.objects.values("grade").annotate(count=Count("id")).order_by("-grade")
            if grade_dist:
                self.stdout.write(f"\n⭐ Grade Distribution:")
                for entry in grade_dist:
                    self.stdout.write(f"   Grade {entry['grade']}: {entry['count']:,}")

    # ──────────────────────────────────────────────────
    # PEOPLE
    # ──────────────────────────────────────────────────

    def handle_people(self, options):
        """Handle people management commands."""
        action = options.get("people_action")

        if not action:
            self.stdout.write("Available people actions: populate, status")
            return

        if action == "populate":
            self._handle_people_populate(options)
        elif action == "status":
            self._handle_people_status()
        else:
            raise CommandError(f"Unknown people action: {action}")

    def _handle_people_populate(self, options):
        """Populate Person hub from Authors and Entities."""
        from bible.people.services.person_linker import PersonLinker

        update = options.get("update", False)
        linker = PersonLinker()

        # Phase 1: Authors
        self.stdout.write("Populating Person from Authors...")
        result = linker.populate_from_authors(update_existing=update)
        self.stdout.write(self.style.SUCCESS(f"  Authors: {result.persons_created} created, {result.persons_updated} updated, {result.authors_linked} linked ({result.duration_seconds:.1f}s)"))
        if result.errors:
            for err in result.errors[:5]:
                self.stdout.write(self.style.WARNING(f"  - {err}"))

        # Phase 2: Entities (if available)
        self.stdout.write("Populating Person from Entities...")
        result2 = linker.populate_from_entities(update_existing=update)
        self.stdout.write(self.style.SUCCESS(f"  Entities: {result2.persons_created} created, {result2.entities_linked} linked, {result2.mixed_found} mixed ({result2.duration_seconds:.1f}s)"))
        if result2.errors:
            for err in result2.errors[:5]:
                self.stdout.write(self.style.WARNING(f"  - {err}"))

        # Summary
        from bible.people.models import Person
        self.stdout.write(self.style.SUCCESS(f"\n✓ Total Person records: {Person.objects.count():,}"))

    def _handle_people_status(self):
        """Show Person hub status."""
        from bible.people.services.person_linker import PersonLinker

        linker = PersonLinker()
        status = linker.get_status()

        self.stdout.write("\n👤 Person Hub Status")
        self.stdout.write("=" * 50)
        self.stdout.write(f"\n💾 Total Persons: {status['total_persons']:,}")

        if status['by_type']:
            self.stdout.write(f"\n📊 By Type:")
            for ptype, count in status['by_type'].items():
                if count > 0:
                    self.stdout.write(f"   {ptype}: {count:,}")

        self.stdout.write(f"\n🔗 Links:")
        self.stdout.write(f"   Authors linked: {status['authors_linked']:,}")
        self.stdout.write(f"   Authors unlinked: {status['authors_unlinked']:,}")
        self.stdout.write(f"   Entities linked: {status['entities_linked']:,}")
        self.stdout.write(f"   Entities unlinked: {status['entities_unlinked']:,}")

    # ──────────────────────────────────────────────────
    # IMAGES
    # ──────────────────────────────────────────────────

    def handle_images(self, options):
        """Handle images management commands."""
        action = options.get("images_action")

        if not action:
            self.stdout.write("Available images actions: import-metadata, import-tags, status")
            return

        if action == "import-metadata":
            self._handle_images_import_metadata(options)
        elif action == "import-tags":
            self._handle_images_import_tags(options)
        elif action == "status":
            self._handle_images_status()
        else:
            raise CommandError(f"Unknown images action: {action}")

    def _handle_images_import_metadata(self, options):
        from bible.images.services.image_importer import ImageImporter

        path = options.get("path")
        limit = options.get("limit")

        importer = ImageImporter(metadata_path=path)
        self.stdout.write(f"Importing image metadata from {importer.metadata_path}...")
        if limit:
            self.stdout.write(f"  Limit: {limit:,}")

        result = importer.import_metadata(limit=limit)

        self.stdout.write(self.style.SUCCESS(f"\n✓ Metadata imported in {result.duration_seconds:.1f}s"))
        self.stdout.write(f"  Artists created: {result.artists_created:,}")
        self.stdout.write(f"  Images created: {result.images_created:,}")
        self.stdout.write(f"  Images skipped: {result.images_skipped:,}")
        if result.errors:
            self.stdout.write(self.style.WARNING(f"\n⚠ {len(result.errors)} errors"))
            for err in result.errors[:5]:
                self.stdout.write(f"  - {err}")

    def _handle_images_import_tags(self, options):
        from bible.images.services.image_importer import ImageImporter

        path = options.get("path")
        limit = options.get("limit")

        importer = ImageImporter(tags_path=path)
        self.stdout.write(f"Importing image tags from {importer.tags_path}...")
        if limit:
            self.stdout.write(f"  Limit: {limit:,}")

        result = importer.import_tags(limit=limit)

        self.stdout.write(self.style.SUCCESS(f"\n✓ Tags imported in {result.duration_seconds:.1f}s"))
        self.stdout.write(f"  Tags created: {result.tags_created:,}")
        self.stdout.write(f"  Verse links created: {result.verse_links_created:,}")
        self.stdout.write(f"  Verse links skipped: {result.verse_links_skipped:,}")
        if result.errors:
            self.stdout.write(self.style.WARNING(f"\n⚠ {len(result.errors)} errors"))
            for err in result.errors[:5]:
                self.stdout.write(f"  - {err}")

    def _handle_images_status(self):
        from bible.images.services.image_importer import ImageImporter

        importer = ImageImporter()
        status = importer.get_status()

        self.stdout.write("\n🎨 Images Data Status")
        self.stdout.write("=" * 50)
        self.stdout.write(f"  Artists: {status['artists']:,}")
        self.stdout.write(f"  Images: {status['images']:,}")
        self.stdout.write(f"  Tagged: {status['tagged']:,}")
        self.stdout.write(f"  Untagged: {status['untagged']:,}")
        self.stdout.write(f"  Tags: {status['tags']:,}")
        self.stdout.write(f"  Verse Links: {status['verse_links']:,}")

    # ──────────────────────────────────────────────────
    # AI
    # ──────────────────────────────────────────────────

    def handle_ai(self, options):
        action = options.get("ai_action")
        if not action:
            self.stdout.write("Available ai actions: analyze, status")
            return

        if action == "analyze":
            self._handle_ai_analyze(options)
        elif action == "status":
            self._handle_ai_status()
        else:
            raise CommandError(f"Unknown ai action: {action}")

    def _handle_ai_analyze(self, options):
        from bible.ai.services.chapter_analyzer import ChapterAnalyzer
        from bible.models import CanonicalBook

        book_osis = options.get("book")
        chapter = options.get("chapter")
        model = options.get("model", "gpt-4o-mini")
        force = options.get("force", False)

        try:
            book = CanonicalBook.objects.get(osis_code__iexact=book_osis)
        except CanonicalBook.DoesNotExist:
            raise CommandError(f"Book {book_osis} not found")

        analyzer = ChapterAnalyzer(model=model)

        if force:
            from bible.ai.models import ChapterAnalysis
            if chapter:
                ChapterAnalysis.objects.filter(book=book, chapter=chapter).delete()
            else:
                ChapterAnalysis.objects.filter(book=book).delete()

        if chapter:
            chapters = [chapter]
        else:
            chapters = list(range(1, book.chapter_count + 1))

        self.stdout.write(f"Analyzing {book_osis} ({len(chapters)} chapters) with {model}...")

        total_stats = {"links_created": 0, "links_removed": 0, "entities": 0, "symbols": 0}

        for ch in chapters:
            if not force and analyzer.is_analyzed(book_osis, ch):
                self.stdout.write(f"  {book_osis} {ch}: already analyzed, skipping")
                continue

            stats = analyzer.analyze_chapter(book_osis, ch)
            total_stats["links_created"] += stats.links_created
            total_stats["links_removed"] += stats.links_removed
            total_stats["entities"] += stats.entities_found
            total_stats["symbols"] += stats.symbols_found

            self.stdout.write(
                f"  {book_osis} {ch}: +{stats.links_created} links, "
                f"-{stats.links_removed} removed, "
                f"{stats.entities_found} entities, {stats.symbols_found} symbols, "
                f"+{stats.new_entities_created} new entities, +{stats.new_symbols_created} new symbols "
                f"({stats.duration_seconds:.1f}s)"
            )

            if stats.errors:
                for err in stats.errors:
                    self.stdout.write(self.style.WARNING(f"    {err}"))

        self.stdout.write(self.style.SUCCESS(
            f"\nTotal: +{total_stats['links_created']} links, "
            f"-{total_stats['links_removed']} removed"
        ))

    def _handle_ai_status(self):
        from bible.ai.models import ChapterAnalysis
        from bible.models import CanonicalBook

        total_chapters = sum(b.chapter_count for b in CanonicalBook.objects.all())
        analyzed = ChapterAnalysis.objects.count()

        self.stdout.write(f"\nAI Analysis Status")
        self.stdout.write("=" * 40)
        self.stdout.write(f"  Chapters analyzed: {analyzed}/{total_chapters}")

        if analyzed > 0:
            from django.db.models import Sum
            totals = ChapterAnalysis.objects.aggregate(
                total_entities=Sum("entities_found"),
                total_symbols=Sum("symbols_found"),
                total_created=Sum("links_created"),
                total_removed=Sum("links_removed"),
            )
            self.stdout.write(f"  Entities found: {totals['total_entities'] or 0}")
            self.stdout.write(f"  Symbols found: {totals['total_symbols'] or 0}")
            self.stdout.write(f"  Links created: {totals['total_created'] or 0}")
            self.stdout.write(f"  Links removed: {totals['total_removed'] or 0}")

    # ──────────────────────────────────────────────────
    # INTEGRATION
    # ──────────────────────────────────────────────────

    def handle_integration(self, options):
        """Handle cross-domain matching commands."""
        action = options.get("integration_action")

        if not action:
            self.stdout.write("Available integration actions: match-images, status")
            return

        if action == "match-images":
            self._handle_integration_match(options)
        elif action == "status":
            self._handle_integration_status()
        else:
            raise CommandError(f"Unknown integration action: {action}")

    def _handle_integration_match(self, options):
        """Run image↔entity matching pipeline."""
        from bible.integration.services.image_matcher import ImageEntityMatcher

        clear = options.get("clear", False)
        matcher = ImageEntityMatcher()

        self.stdout.write("Running image↔entity matching pipeline...")
        stats = matcher.match_all(clear_existing=clear)

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Matching completed in {stats.duration_seconds:.1f}s"
        ))
        self.stdout.write(f"  Tags processed: {stats.tags_processed:,}")
        self.stdout.write(f"  Characters processed: {stats.characters_processed:,}")
        self.stdout.write(f"  Characters skipped (groups): {stats.characters_skipped:,}")
        self.stdout.write(f"  Links created: {stats.links_created:,}")
        self.stdout.write(f"  Links existing: {stats.links_existing:,}")
        self.stdout.write(f"\n  Exact matches: {stats.exact_matches:,}")
        self.stdout.write(f"  Alias matches: {stats.alias_matches:,}")
        self.stdout.write(f"  Fuzzy matches: {stats.fuzzy_matches:,}")
        self.stdout.write(f"  Person matches: {stats.person_matches:,}")
        self.stdout.write(f"  Unmatched: {stats.unmatched:,}")

        if stats.errors:
            self.stdout.write(self.style.WARNING(f"\n⚠ {len(stats.errors)} errors"))
            for err in stats.errors[:5]:
                self.stdout.write(f"  - {err}")

    def _handle_integration_status(self):
        """Show matching status."""
        from bible.integration.services.image_matcher import ImageEntityMatcher

        status = ImageEntityMatcher.get_status()

        self.stdout.write("\n🔗 Integration Status")
        self.stdout.write("=" * 50)
        self.stdout.write(f"  Total links: {status['total_links']:,}")
        self.stdout.write(f"  With entity: {status['with_entity']:,}")
        self.stdout.write(f"  With person: {status['with_person']:,}")
        self.stdout.write(f"  Unlinked: {status['unlinked']:,}")

        if status['by_method']:
            self.stdout.write(f"\n  By method:")
            for method, count in sorted(status['by_method'].items()):
                self.stdout.write(f"    {method}: {count:,}")

    # ──────────────────────────────────────────────────
    # GAZETTEERS
    # ──────────────────────────────────────────────────

    def handle_gazetteers(self, options):
        """Handle gazetteers data quality pipeline."""
        action = options.get("gazetteers_action")

        if not action:
            self.stdout.write("Available gazetteers actions: process, status")
            return

        if action == "process":
            self._handle_gazetteers_process(options)
        elif action == "status":
            self._handle_gazetteers_status()
        else:
            raise CommandError(f"Unknown gazetteers action: {action}")

    def _handle_gazetteers_process(self, options):
        """Run the gazetteer data quality pipeline."""
        from bible.services.gazetteer_processor import GazetteerProcessor

        source = options.get("source")
        tagger_index = options.get("tagger_index")
        output = options.get("output")

        if not source:
            # Try default paths
            candidates = [
                Path("C:/Users/Iury Coelho/Desktop/bible-gazetteers-dataset/data/pt"),
                Path("E:/bible-gazetteers-dataset/data/pt"),
            ]
            for c in candidates:
                if c.exists():
                    source = str(c)
                    break
            if not source:
                raise CommandError(
                    "Source directory not found. Use --source to specify the path to "
                    "bible-gazetteers-dataset/data/pt/"
                )

        if not tagger_index:
            candidates = [
                Path("C:/Users/Iury Coelho/Desktop/bible-image-tagger/data/lookup/gazetteer_index.json"),
                Path("E:/bible-image-tagger/data/lookup/gazetteer_index.json"),
            ]
            for c in candidates:
                if c.exists():
                    tagger_index = str(c)
                    break

        self.stdout.write("Running Gazetteer Data Quality Pipeline...")
        self.stdout.write(f"  Source: {source}")
        self.stdout.write(f"  Tagger index: {tagger_index or 'not found (skipping alias merge)'}")
        self.stdout.write(f"  Output: {output or 'data/processed/gazetteers/'}")

        processor = GazetteerProcessor(
            source_dir=source,
            tagger_index_path=tagger_index,
            output_dir=output,
        )
        report = processor.process()

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Pipeline completed in {report.duration_seconds:.1f}s"
        ))
        self.stdout.write(f"  Entities: {report.entities_total:,}")
        self.stdout.write(f"  Symbols: {report.symbols_total:,}")
        self.stdout.write(f"  Relationships: {report.relationships_total:,}")
        self.stdout.write(f"  EN aliases added: {report.aliases_en_added:,}")

        if report.prefix_fixes:
            self.stdout.write(f"\n  Prefix fixes: {len(report.prefix_fixes):,}")
        if report.duplicate_merges:
            self.stdout.write(f"  Duplicates merged: {len(report.duplicate_merges):,}")
        if report.canonical_id_fixes:
            self.stdout.write(f"  Canonical ID fixes: {len(report.canonical_id_fixes):,}")

        if report.invalid_refs:
            self.stdout.write(self.style.WARNING(
                f"\n  Invalid refs: {len(report.invalid_refs):,}"
            ))
        if report.duplicate_ids:
            self.stdout.write(self.style.WARNING(
                f"  Duplicate IDs: {len(report.duplicate_ids):,}"
            ))
        if report.alias_conflicts:
            self.stdout.write(self.style.WARNING(
                f"  Alias conflicts: {len(report.alias_conflicts):,}"
            ))
        if report.missing_fields:
            self.stdout.write(self.style.WARNING(
                f"  Missing fields: {len(report.missing_fields):,}"
            ))

        self.stdout.write(f"\n  Full report: data/processed/gazetteers/quality_report.json")

    def _handle_gazetteers_status(self):
        """Show processed gazetteer data status."""
        import json
        from pathlib import Path as P

        output_dir = P("data/processed/gazetteers")

        if not output_dir.exists():
            self.stdout.write(self.style.WARNING(
                "No processed gazetteer data found. Run: python manage.py bible gazetteers process"
            ))
            return

        meta_path = output_dir / "_meta.json"
        if not meta_path.exists():
            self.stdout.write(self.style.WARNING("_meta.json not found in processed directory"))
            return

        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)

        self.stdout.write("\n📊 Processed Gazetteer Status")
        self.stdout.write("=" * 50)
        self.stdout.write(f"  Version: {meta.get('version', '?')}")
        self.stdout.write(f"  Processed at: {meta.get('processed_at', '?')}")
        self.stdout.write(f"  Total entities: {meta.get('total_entities', 0):,}")
        self.stdout.write(f"  Total symbols: {meta.get('total_symbols', 0):,}")
        self.stdout.write(f"  Total relationships: {meta.get('total_relationships', 0):,}")

        self.stdout.write(f"\n📁 Entity namespaces:")
        for ns, info in meta.get("entity_namespaces", {}).items():
            self.stdout.write(f"   {ns}: {info['count']:,}")

        self.stdout.write(f"\n📁 Symbol namespaces:")
        for ns, info in meta.get("symbol_namespaces", {}).items():
            self.stdout.write(f"   {ns}: {info['count']:,}")

        # Show quality report summary if available
        report_path = output_dir / "quality_report.json"
        if report_path.exists():
            with open(report_path, encoding="utf-8") as f:
                report = json.load(f)
            validation = report.get("validation", {})
            fixes = report.get("fixes_applied", {})

            self.stdout.write(f"\n🔧 Fixes applied:")
            self.stdout.write(f"   Prefix fixes: {fixes.get('prefix_fixes', 0)}")
            self.stdout.write(f"   Duplicate merges: {fixes.get('duplicate_merges', 0)}")
            self.stdout.write(f"   Canonical ID fixes: {fixes.get('canonical_id_fixes', 0)}")

            self.stdout.write(f"\n⚠ Validation issues:")
            self.stdout.write(f"   Invalid refs: {validation.get('invalid_refs_count', 0)}")
            self.stdout.write(f"   Duplicate IDs: {validation.get('duplicate_ids_count', 0)}")
            self.stdout.write(f"   Alias conflicts: {validation.get('alias_conflicts_count', 0)}")
            self.stdout.write(f"   Missing fields: {validation.get('missing_fields_count', 0)}")
