"""
Django management command to populate cross-references from OpenBible.info data.
Part of T-206 - Phase 3: Cross-References Population (Final Phase)

This script processes cross-references from data/datasets/bibles-2024/cross_references.txt,
creating canonical connections between verses that are version-agnostic.

Usage:
    python manage.py populate_cross_references
    python manage.py populate_cross_references --min-votes 5
    python manage.py populate_cross_references --dry-run
"""
import re

from django.core.management.base import BaseCommand
from django.db import transaction

from bible.models import CanonicalBook, CrossReference


class Command(BaseCommand):
    help = "Populate cross-references from OpenBible.info data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--min-votes",
            type=int,
            default=1,
            help="Minimum votes required for a cross-reference to be included (default: 1)",
        )
        parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")

    # Map standard abbreviations to OSIS codes for cross-reference parsing
    BOOK_ABBREVIATION_TO_OSIS = {
        # Old Testament
        "Gen": "Gen",
        "Exod": "Exod",
        "Lev": "Lev",
        "Num": "Num",
        "Deut": "Deut",
        "Josh": "Josh",
        "Judg": "Judg",
        "Ruth": "Ruth",
        "1Sam": "1Sam",
        "2Sam": "2Sam",
        "1Kgs": "1Kgs",
        "2Kgs": "2Kgs",
        "1Chr": "1Chr",
        "2Chr": "2Chr",
        "Ezra": "Ezra",
        "Neh": "Neh",
        "Esth": "Esth",
        "Job": "Job",
        "Ps": "Ps",
        "Prov": "Prov",
        "Eccl": "Eccl",
        "Song": "Song",
        "Isa": "Isa",
        "Jer": "Jer",
        "Lam": "Lam",
        "Ezek": "Ezek",
        "Dan": "Dan",
        "Hos": "Hos",
        "Joel": "Joel",
        "Amos": "Amos",
        "Obad": "Obad",
        "Jonah": "Jonah",
        "Mic": "Mic",
        "Nah": "Nah",
        "Hab": "Hab",
        "Zeph": "Zeph",
        "Hag": "Hag",
        "Zech": "Zech",
        "Mal": "Mal",
        # New Testament
        "Matt": "Matt",
        "Mark": "Mark",
        "Luke": "Luke",
        "John": "John",
        "Acts": "Acts",
        "Rom": "Rom",
        "1Cor": "1Cor",
        "2Cor": "2Cor",
        "Gal": "Gal",
        "Eph": "Eph",
        "Phil": "Phil",
        "Col": "Col",
        "1Thess": "1Thess",
        "2Thess": "2Thess",
        "1Tim": "1Tim",
        "2Tim": "2Tim",
        "Titus": "Titus",
        "Phlm": "Phlm",
        "Heb": "Heb",
        "Jas": "Jas",
        "1Pet": "1Pet",
        "2Pet": "2Pet",
        "1John": "1John",
        "2John": "2John",
        "3John": "3John",
        "Jude": "Jude",
        "Rev": "Rev",
        # Deuterocanonical (if they exist in system)
        "Tob": "Tob",
        "Jdt": "Jdt",
        "Wis": "Wis",
        "Sir": "Sir",
        "Bar": "Bar",
        "1Macc": "1Macc",
        "2Macc": "2Macc",
    }

    def handle(self, *args, **options):
        self.dry_run = options.get("dry_run", False)
        min_votes = options.get("min_votes", 1)

        file_path = "data/datasets/bibles-2024/cross_references.txt"
        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Cross-references file not found: {file_path}"))
            return

        if self.dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))

        # Skip header line
        data_lines = lines[1:] if lines and lines[0].startswith("From Verse") else lines

        self.stdout.write(
            self.style.SUCCESS(f"Processing {len(data_lines):,} cross-references (min_votes: {min_votes})...")
        )

        # Cache canonical books for performance
        if not self.dry_run:
            self.canonical_books = {book.osis_code: book for book in CanonicalBook.objects.all()}
        else:
            self.canonical_books = {}

        cross_refs_to_create = []
        processed_count = 0
        skipped_count = 0
        error_count = 0

        for line_num, line in enumerate(data_lines, 2):  # Start from line 2
            line = line.strip()
            if not line:
                continue

            try:
                parts = line.split("\t")
                if len(parts) != 3:
                    continue

                from_verse, to_verse, votes_str = parts
                votes = int(votes_str)

                if votes < min_votes:
                    skipped_count += 1
                    continue

                # Parse verse references
                from_ref = self.parse_verse_reference(from_verse)
                to_ref = self.parse_verse_reference(to_verse)

                if not from_ref or not to_ref:
                    error_count += 1
                    continue

                # Handle ranges properly
                if from_ref["is_range"]:
                    from_ref = from_ref["start_verse"]  # Only use start verse for FROM

                # For TO references, handle ranges correctly
                if to_ref["is_range"]:
                    to_start_ref = to_ref["start_verse"]
                    to_end_ref = to_ref["end_verse"]

                    # Ensure both verses are from the same book/chapter
                    if to_start_ref["book"] != to_end_ref["book"] or to_start_ref["chapter"] != to_end_ref["chapter"]:
                        # If range spans books/chapters, just use start verse
                        to_ref = to_start_ref
                        to_verse_start = to_start_ref["verse"]
                        to_verse_end = to_start_ref["verse"]
                    else:
                        to_ref = to_start_ref  # Use start for book/chapter info
                        to_verse_start = to_start_ref["verse"]
                        to_verse_end = to_end_ref["verse"]
                else:
                    to_verse_start = to_ref["verse"]
                    to_verse_end = to_ref["verse"]

                if not self.dry_run:
                    # Get canonical books
                    from_book = self.canonical_books.get(from_ref["book"])
                    to_book = self.canonical_books.get(to_ref["book"])

                    if not from_book or not to_book:
                        error_count += 1
                        continue

                    cross_refs_to_create.append(
                        CrossReference(
                            from_book=from_book,
                            from_chapter=from_ref["chapter"],
                            from_verse=from_ref["verse"],
                            to_book=to_book,
                            to_chapter=to_ref["chapter"],
                            to_verse_start=to_verse_start,
                            to_verse_end=to_verse_end,
                            votes=votes,
                        )
                    )

                processed_count += 1

                # Bulk create in batches
                if not self.dry_run and len(cross_refs_to_create) >= 1000:
                    self.bulk_create_cross_references(cross_refs_to_create)
                    cross_refs_to_create = []

                # Progress update
                if processed_count % 10000 == 0:
                    self.stdout.write(f"  Processed {processed_count:,} references...")

            except Exception as e:
                error_count += 1
                if error_count <= 10:  # Only show first 10 errors
                    self.stdout.write(self.style.WARNING(f"  Line {line_num}: {str(e)[:100]}"))

        # Create remaining cross-references
        if not self.dry_run and cross_refs_to_create:
            self.bulk_create_cross_references(cross_refs_to_create)

        # Summary
        self.stdout.write(self.style.SUCCESS("\n✓ Cross-references processing complete!"))
        self.stdout.write(f"  📊 Processed: {processed_count:,}")
        self.stdout.write(f"  ⏭ Skipped (low votes): {skipped_count:,}")
        self.stdout.write(f"  ⚠ Errors: {error_count:,}")

    def parse_verse_reference(self, ref_str):
        """
        Parse verse reference like 'Gen.1.1' or 'Prov.8.22-Prov.8.30'
        Returns dict with book, chapter, verse info
        """
        try:
            # Check for range (has dash)
            if "-" in ref_str:
                start_ref, end_ref = ref_str.split("-", 1)
                start_parsed = self.parse_single_verse(start_ref)
                end_parsed = self.parse_single_verse(end_ref)

                if start_parsed and end_parsed:
                    return {"is_range": True, "start_verse": start_parsed, "end_verse": end_parsed}
                return None
            else:
                parsed = self.parse_single_verse(ref_str)
                if parsed:
                    return {"is_range": False, **parsed}
                return None

        except Exception:
            return None

    def parse_single_verse(self, verse_str):
        """Parse single verse reference like 'Gen.1.1'"""
        try:
            # Pattern: Book.Chapter.Verse
            pattern = r"^([A-Za-z0-9]+)\.(\d+)\.(\d+)$"
            match = re.match(pattern, verse_str)

            if not match:
                return None

            book_abbrev, chapter_str, verse_str = match.groups()

            # Map abbreviation to OSIS code
            osis_code = self.BOOK_ABBREVIATION_TO_OSIS.get(book_abbrev)
            if not osis_code:
                return None

            return {"book": osis_code, "chapter": int(chapter_str), "verse": int(verse_str)}

        except Exception:
            return None

    @transaction.atomic
    def bulk_create_cross_references(self, cross_refs):
        """Create cross-references in bulk, handling duplicates"""
        try:
            if self.dry_run:
                return

            # Use bulk_create with ignore_conflicts to handle duplicates gracefully
            created_count = len(CrossReference.objects.bulk_create(cross_refs, batch_size=1000, ignore_conflicts=True))

            if created_count < len(cross_refs):
                self.stdout.write(
                    f"  ℹ Created {created_count}/{len(cross_refs)} cross-references (duplicates skipped)"
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ Error creating cross-references: {e}"))
