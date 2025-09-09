"""
Django management command to populate deuterocanonical/apocryphal bible books.
Part of T-205 - Phase 2: Deuterocanonical Books Population

This script processes deuterocanonical books from data/datasets/deuterocanonical/ directory,
focusing on the traditional 7 deuterocanonical books accepted by Catholic Church:
Tobit, Judith, Wisdom, Sirach, Baruch, 1 Maccabees, 2 Maccabees

Usage:
    python manage.py populate_deuterocanon
    python manage.py populate_deuterocanon --book tobit
    python manage.py populate_deuterocanon --dry-run
"""
import json
import os

from django.core.management.base import BaseCommand
from django.db import transaction

from bible.models import BookName, CanonicalBook, Language, License, Testament, Verse, Version


class Command(BaseCommand):
    help = "Populate deuterocanonical/apocryphal bible books"

    def add_arguments(self, parser):
        parser.add_argument(
            "--book",
            type=str,
            help="Specific book to populate (e.g., tobit, judith, wisdom, sirach, baruch, 1maccabees, 2maccabees)",
        )
        parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")

    # Map directory names to OSIS codes and metadata for traditional deuterocanonical books
    DEUTEROCANONICAL_BOOKS = {
        "book-of-tobit": {
            "osis": "Tob",
            "name_en": "Tobit",
            "name_pt": "Tobias",
            "order": 67,  # After canonical 66 books
            "testament_id": 3,  # APO testament
        },
        "book-of-judith": {
            "osis": "Jdt",
            "name_en": "Judith",
            "name_pt": "Judite",
            "order": 68,
            "testament_id": 3,
        },
        "wisdom-of-solomon": {
            "osis": "Wis",
            "name_en": "Wisdom of Solomon",
            "name_pt": "Sabedoria",
            "order": 69,
            "testament_id": 3,
        },
        "book-of-sirach": {
            "osis": "Sir",
            "name_en": "Sirach",
            "name_pt": "Eclesiástico",
            "order": 70,
            "testament_id": 3,
        },
        "1-baruch": {
            "osis": "Bar",
            "name_en": "Baruch",
            "name_pt": "Baruc",
            "order": 71,
            "testament_id": 3,
        },
        "1-maccabees": {
            "osis": "1Macc",
            "name_en": "1 Maccabees",
            "name_pt": "1 Macabeus",
            "order": 72,
            "testament_id": 3,
        },
        "2-maccabees": {
            "osis": "2Macc",
            "name_en": "2 Maccabees",
            "name_pt": "2 Macabeus",
            "order": 73,
            "testament_id": 3,
        },
    }

    def handle(self, *args, **options):
        self.dry_run = options.get("dry_run", False)
        book_filter = options.get("book")

        data_dir = "data/datasets/deuterocanonical/sources/en"
        if not os.path.exists(data_dir):
            self.stdout.write(self.style.ERROR(f"Data directory not found: {data_dir}"))
            return

        if self.dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))

        # Filter books to process
        books_to_process = self.DEUTEROCANONICAL_BOOKS.copy()
        if book_filter:
            # Find matching book
            book_key = None
            for key, book_info in books_to_process.items():
                if (
                    book_filter.lower() in key.lower()
                    or book_filter.lower() in book_info["name_en"].lower()
                    or book_filter.lower().replace("maccabees", "macc") in book_info["osis"].lower()
                ):
                    book_key = key
                    break

            if not book_key:
                self.stdout.write(
                    self.style.ERROR(
                        f"Book {book_filter} not found. Available: {list(self.DEUTEROCANONICAL_BOOKS.keys())}"
                    )
                )
                return
            books_to_process = {book_key: books_to_process[book_key]}

        # Ensure APO testament exists
        if not self.dry_run:
            try:
                apo_testament = Testament.objects.get(id=3)
            except Testament.DoesNotExist:
                self.stdout.write(self.style.ERROR("APO Testament (id=3) not found. Run seed_01_metadata first."))
                return

        # Create deuterocanonical version if it doesn't exist
        if not self.dry_run:
            en_language, _ = Language.objects.get_or_create(code="en-US", defaults={"name": "English (United States)"})

            license_obj, _ = License.objects.get_or_create(code="PD", defaults={"name": "Public Domain", "url": None})

            deutero_version, created = Version.objects.get_or_create(
                code="EN_APOCRYPHA",
                defaults={
                    "name": "English Apocrypha/Deuterocanonical",
                    "language": en_language,
                    "license": license_obj,
                    "description": "English translation of deuterocanonical books accepted by Catholic and Orthodox traditions.",
                },
            )
            if created:
                self.stdout.write(f"✓ Created deuterocanonical version: {deutero_version.abbreviation}")

            # Check if this version already has any deuterocanonical verses
            existing_verses = Verse.objects.filter(version=deutero_version, book__is_deuterocanonical=True).count()
            if existing_verses > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"Version {deutero_version.code} already has {existing_verses} deuterocanonical verses. Skipping to avoid duplicates."
                    )
                )
                return

        total_books = len(books_to_process)
        for idx, (dir_name, book_info) in enumerate(books_to_process.items(), 1):
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n[{idx}/{total_books}] Processing {book_info["name_en"]} ({book_info["osis"]})...'
                )
            )
            self.process_book(data_dir, dir_name, book_info, deutero_version if not self.dry_run else None)

        self.stdout.write(self.style.SUCCESS(f"\n✓ Completed processing {total_books} deuterocanonical books!"))

    @transaction.atomic
    def process_book(self, data_dir, dir_name, book_info, deutero_version):
        """Process a single deuterocanonical book."""
        book_dir = os.path.join(data_dir, dir_name)
        json_file = os.path.join(book_dir, f"{dir_name}.json")

        if not os.path.exists(json_file):
            self.stdout.write(self.style.WARNING(f"  ⚠ File not found: {json_file}"))
            return

        # Create or get CanonicalBook for deuterocanonical
        if not self.dry_run:
            canonical_book, created = CanonicalBook.objects.get_or_create(
                osis_code=book_info["osis"],
                defaults={
                    "canonical_order": book_info["order"],
                    "testament_id": book_info["testament_id"],
                    "is_deuterocanonical": True,
                    "chapter_count": 0,  # Will be updated after processing
                },
            )
            if created:
                self.stdout.write(f'  ✓ Created CanonicalBook: {book_info["osis"]}')

                # Create BookName entries for multiple languages
                pt_language, _ = Language.objects.get_or_create(code="pt-BR", defaults={"name": "Portuguese (Brazil)"})
                en_language, _ = Language.objects.get_or_create(
                    code="en-US", defaults={"name": "English (United States)"}
                )

                # Portuguese name
                BookName.objects.create(
                    canonical_book=canonical_book,
                    language=pt_language,
                    name=book_info["name_pt"],
                    abbreviation=book_info["osis"],
                )

                # English name
                BookName.objects.create(
                    canonical_book=canonical_book,
                    language=en_language,
                    name=book_info["name_en"],
                    abbreviation=book_info["osis"],
                )

                self.stdout.write(f'  ✓ Created BookName entries for {book_info["osis"]}')
            else:
                self.stdout.write(f'  ℹ CanonicalBook already exists: {book_info["osis"]}')

        # Load and process verses
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ Error loading {json_file}: {e}"))
            return

        books_data = data.get("books", [])
        if not books_data:
            self.stdout.write(self.style.WARNING(f"  ⚠ No books data found in {json_file}"))
            return

        verses_to_create = []
        max_chapter = 0
        processed_verses = set()  # Track processed verses to avoid duplicates

        for book_data in books_data:
            chapters = book_data.get("chapters", [])

            for chapter_data in chapters:
                chapter_num = chapter_data.get("chapter", 0)
                max_chapter = max(max_chapter, chapter_num)
                verses = chapter_data.get("verses", [])

                for verse_data in verses:
                    verse_num = verse_data.get("verse", 0)
                    text = verse_data.get("text", "").strip()

                    # Create unique key for this verse
                    verse_key = (chapter_num, verse_num)

                    if text and not self.dry_run and verse_key not in processed_verses:
                        processed_verses.add(verse_key)
                        verses_to_create.append(
                            Verse(
                                book=canonical_book,
                                version=deutero_version,
                                chapter=chapter_num,
                                number=verse_num,
                                text=text,
                            )
                        )

        if self.dry_run:
            self.stdout.write(f"  [DRY RUN] Would create ~{len(verses_to_create)} verses from {max_chapter} chapters")
            return

        # Check if verses already exist for this book and version
        if verses_to_create:
            existing_count = Verse.objects.filter(book=canonical_book, version=deutero_version).count()
            if existing_count > 0:
                self.stdout.write(
                    f'  ⚠ Book {book_info["osis"]} already has {existing_count} verses in version {deutero_version.code}. Skipping.'
                )
                return

            # Bulk create verses
            Verse.objects.bulk_create(verses_to_create, batch_size=1000)

            # Update chapter count
            canonical_book.chapter_count = max_chapter
            canonical_book.save(update_fields=["chapter_count"])

            self.stdout.write(f"  ✓ Created {len(verses_to_create):,} verses from {max_chapter} chapters")
        else:
            self.stdout.write(f'  ⚠ No verses to create for {book_info["name_en"]}')
