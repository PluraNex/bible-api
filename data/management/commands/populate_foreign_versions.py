"""
Django management command to populate foreign (non-Portuguese) bible versions.
Part of T-204 - Phase 2: Foreign Versions Population

This script processes bible versions from data/datasets/bibles-2024/ directory,
focusing on English versions like KJV, ASV, BBE, WEB, YLT.

Usage:
    python manage.py populate_foreign_versions
    python manage.py populate_foreign_versions --bible-version KJV
    python manage.py populate_foreign_versions --dry-run
"""
import json
import os

from django.core.management.base import BaseCommand
from django.db import transaction

from bible.models import CanonicalBook, Language, License, Verse, Version


class Command(BaseCommand):
    help = "Populate foreign bible versions from data/datasets/bibles-2024/ directory"

    def add_arguments(self, parser):
        parser.add_argument(
            "--bible-version", type=str, help="Specific version to populate (e.g., KJV, ASV, BBE, WEB, YLT)"
        )
        parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")

    # Map version file prefixes to metadata
    VERSION_MAPPING = {
        "t_kjv": {
            "abbreviation": "KJV",
            "name": "King James Version",
            "language": "en-US",
            "license": "Public Domain",
            "description": "The King James Version (KJV), completed in 1611, is one of the most important English Bible translations.",
        },
        "t_asv": {
            "abbreviation": "ASV",
            "name": "American Standard Version",
            "language": "en-US",
            "license": "Public Domain",
            "description": "American Standard Version (ASV), completed in 1901, revision of the English Revised Version.",
        },
        "t_bbe": {
            "abbreviation": "BBE",
            "name": "Bible in Basic English",
            "language": "en-US",
            "license": "Public Domain",
            "description": "Bible In Basic English (BBE) uses only 1,000 basic English words for accessibility.",
        },
        "t_web": {
            "abbreviation": "WEB",
            "name": "World English Bible",
            "language": "en-US",
            "license": "Public Domain",
            "description": "World English Bible (WEB) is a free updated revision of the American Standard Version.",
        },
        "t_ylt": {
            "abbreviation": "YLT",
            "name": "Young's Literal Translation",
            "language": "en-US",
            "license": "Public Domain",
            "description": "Young's Literal Translation (YLT) aims for word-for-word accuracy from original texts.",
        },
    }

    # Map book numbers from bible_databases-2024 to OSIS codes
    # Based on key_english.json structure
    BOOK_NUMBER_TO_OSIS = {
        1: "Gen",
        2: "Exod",
        3: "Lev",
        4: "Num",
        5: "Deut",
        6: "Josh",
        7: "Judg",
        8: "Ruth",
        9: "1Sam",
        10: "2Sam",
        11: "1Kgs",
        12: "2Kgs",
        13: "1Chr",
        14: "2Chr",
        15: "Ezra",
        16: "Neh",
        17: "Esth",
        18: "Job",
        19: "Ps",
        20: "Prov",
        21: "Eccl",
        22: "Song",
        23: "Isa",
        24: "Jer",
        25: "Lam",
        26: "Ezek",
        27: "Dan",
        28: "Hos",
        29: "Joel",
        30: "Amos",
        31: "Obad",
        32: "Jonah",
        33: "Mic",
        34: "Nah",
        35: "Hab",
        36: "Zeph",
        37: "Hag",
        38: "Zech",
        39: "Mal",
        # New Testament
        40: "Matt",
        41: "Mark",
        42: "Luke",
        43: "John",
        44: "Acts",
        45: "Rom",
        46: "1Cor",
        47: "2Cor",
        48: "Gal",
        49: "Eph",
        50: "Phil",
        51: "Col",
        52: "1Thess",
        53: "2Thess",
        54: "1Tim",
        55: "2Tim",
        56: "Titus",
        57: "Phlm",
        58: "Heb",
        59: "Jas",
        60: "1Pet",
        61: "2Pet",
        62: "1John",
        63: "2John",
        64: "3John",
        65: "Jude",
        66: "Rev",
    }

    def handle(self, *args, **options):
        self.dry_run = options.get("dry_run", False)
        version_filter = options.get("bible_version")

        data_dir = "data/datasets/bibles-2024/json"
        if not os.path.exists(data_dir):
            self.stdout.write(self.style.ERROR(f"Data directory not found: {data_dir}"))
            return

        if self.dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))

        # Load book metadata
        book_key_path = os.path.join(data_dir, "key_english.json")
        if not os.path.exists(book_key_path):
            self.stdout.write(self.style.ERROR(f"Book key file not found: {book_key_path}"))
            return

        # Filter versions to process
        versions_to_process = self.VERSION_MAPPING.copy()
        if version_filter:
            # Find matching version
            matching_versions = {
                k: v for k, v in versions_to_process.items() if v["abbreviation"].upper() == version_filter.upper()
            }
            if not matching_versions:
                self.stdout.write(
                    self.style.ERROR(
                        f'Version {version_filter} not found. Available: {list(v["abbreviation"] for v in self.VERSION_MAPPING.values())}'
                    )
                )
                return
            versions_to_process = matching_versions

        total_versions = len(versions_to_process)
        for idx, (file_prefix, version_info) in enumerate(versions_to_process.items(), 1):
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n[{idx}/{total_versions}] Processing {version_info["abbreviation"]} ({version_info["name"]})...'
                )
            )
            self.process_version(data_dir, file_prefix, version_info)

        self.stdout.write(self.style.SUCCESS(f"\n✓ Completed processing {total_versions} foreign versions!"))

    @transaction.atomic
    def process_version(self, data_dir, file_prefix, version_info):
        """Process a single version from its JSON file."""
        json_file = os.path.join(data_dir, f"{file_prefix}.json")

        if not os.path.exists(json_file):
            self.stdout.write(self.style.WARNING(f"  ⚠ File not found: {json_file}"))
            return

        # Get or create language
        if not self.dry_run:
            language, created = Language.objects.get_or_create(
                code=version_info["language"], defaults={"name": "English (United States)"}
            )
            if created:
                self.stdout.write(f"  ✓ Created language: {language.code}")

            # Get or create license
            license_obj, created = License.objects.get_or_create(
                code="PD", defaults={"name": version_info["license"], "url": None}
            )
            if created:
                self.stdout.write(f"  ✓ Created license: {license_obj.name}")

            # Create or get version
            version, created = Version.objects.get_or_create(
                code=f"EN_{version_info['abbreviation']}",
                defaults={
                    "name": version_info["name"],
                    "language": language,
                    "license": license_obj,
                    "description": version_info["description"],
                },
            )
            if created:
                self.stdout.write(f"  ✓ Created version: {version.abbreviation}")
            else:
                self.stdout.write(f"  ℹ Version already exists: {version.abbreviation}")
        else:
            self.stdout.write(f'  [DRY RUN] Would process version: {version_info["abbreviation"]}')

        # Load and process verses
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ Error loading {json_file}: {e}"))
            return

        # Parse verse data
        verses_data = data.get("resultset", {}).get("row", [])
        if not verses_data:
            self.stdout.write(self.style.WARNING(f"  ⚠ No verse data found in {json_file}"))
            return

        verses_to_create = []
        processed_books = set()

        for verse_entry in verses_data:
            field = verse_entry.get("field", [])
            if len(field) < 5:
                continue

            verse_id, book_number, chapter, verse_num, text = field[:5]

            # Map book number to OSIS code
            osis_code = self.BOOK_NUMBER_TO_OSIS.get(book_number)
            if not osis_code:
                if book_number not in processed_books:
                    self.stdout.write(self.style.WARNING(f"  ⚠ Unknown book number: {book_number}"))
                continue

            # Get canonical book
            if not self.dry_run:
                try:
                    canonical_book = CanonicalBook.objects.get(osis_code=osis_code)
                except CanonicalBook.DoesNotExist:
                    if book_number not in processed_books:
                        self.stdout.write(self.style.ERROR(f"  ✗ CanonicalBook not found for OSIS: {osis_code}"))
                    continue

                verses_to_create.append(
                    Verse(book=canonical_book, version=version, chapter=chapter, number=verse_num, text=text.strip())
                )

            processed_books.add(book_number)

        if self.dry_run:
            self.stdout.write(
                f"  [DRY RUN] Would create ~{len(verses_to_create)} verses from {len(processed_books)} books"
            )
            return

        # Bulk create verses
        if verses_to_create:
            existing_count = Verse.objects.filter(version=version).count()
            if existing_count > 0:
                self.stdout.write(f"  ⚠ Version {version.abbreviation} already has {existing_count} verses. Skipping.")
                return

            Verse.objects.bulk_create(verses_to_create, batch_size=1000)
            self.stdout.write(f"  ✓ Created {len(verses_to_create):,} verses for {len(processed_books)} books")
        else:
            self.stdout.write(f'  ⚠ No verses to create for {version_info["abbreviation"]}')
