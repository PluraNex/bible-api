"""
Management command to seed commentaries from JSON files in new_testament/ directory.
Reads pre-enriched commentary data with AI analysis and populates the database.
"""

import json
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from bible.commentaries import Author, CommentaryEntry, CommentarySource
from bible.models import CanonicalBook, Language, License


class Command(BaseCommand):
    help = "Populate commentaries from JSON files with pre-enriched data"

    def add_arguments(self, parser):
        parser.add_argument(
            '--book',
            type=str,
            help='Specific book to seed (e.g., "acts")',
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete existing commentaries before seeding',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without saving',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        # Get or create languages
        en_us, _ = Language.objects.get_or_create(code='en-US', defaults={'name': 'English (US)'})
        pt_br, _ = Language.objects.get_or_create(code='pt-BR', defaults={'name': 'Portuguese (Brazil)'})

        # Get or create license
        public_domain, _ = License.objects.get_or_create(
            code='catena-bible',
            defaults={'name': 'Catena Bible - Patristic Commentaries'}
        )

        if options.get('delete'):
            CommentaryEntry.objects.all().delete()
            Author.objects.all().delete()
            CommentarySource.objects.all().delete()
            self.stdout.write(self.style.WARNING('Deleted existing data'))

        # Create or get Catena Bible source
        catena_source, created = CommentarySource.objects.get_or_create(
            short_code='CATENA',
            defaults={
                'name': 'Catena Bible - Patristic Commentaries',
                'publication_year': 2024,
                'author_type': 'Church Fathers/Medieval',
                'description': 'Collection of patristic and medieval biblical commentaries from Catena Bible API',
                'language': en_us,
                'license': public_domain,
                'is_featured': True,
                'url': 'https://catenabible.com',
            }
        )
        status = "created" if created else "exists"
        self.stdout.write(self.style.SUCCESS(f'Source: {catena_source.name} [{status}]'))

        # Find JSON files
        base_path = Path('new_testament')
        if not base_path.exists():
            self.stdout.write(self.style.ERROR(f'Directory {base_path} not found'))
            return

        book_filter = options.get('book')
        json_files = []

        for json_file in sorted(base_path.glob('*/**/verses/*.json')):
            if book_filter and book_filter not in str(json_file):
                continue
            json_files.append(json_file)

        self.stdout.write(f'Found {len(json_files)} commentary files')

        authors_created = {}
        entries_created = 0
        entries_updated = 0

        # Process each JSON file
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                verse_reference = data.get('verse_reference', '')
                if not verse_reference:
                    continue

                # Parse reference (e.g., "ACTS 1:1" -> book="Acts", chapter=1, verse=1)
                parts = verse_reference.split()
                if len(parts) < 2:
                    continue

                book_name = parts[0].lower()
                verse_parts = parts[1].split(':')
                if len(verse_parts) != 2:
                    continue

                try:
                    chapter = int(verse_parts[0])
                    verse = int(verse_parts[1])
                except ValueError:
                    continue

                # Get canonical book
                try:
                    # Try OSIS code first
                    if book_name == 'acts':
                        book = CanonicalBook.objects.get(osis_code='Acts')
                    else:
                        # Map other books
                        book_map = {
                            'matthew': 'Matt', 'mark': 'Mark', 'luke': 'Luke', 'john': 'John',
                            'romans': 'Rom', 'corinthians': 'Cor', '1corinthians': '1Cor', '2corinthians': '2Cor',
                            'galatians': 'Gal', 'ephesians': 'Eph', 'philippians': 'Phil', 'colossians': 'Col',
                            '1thessalonians': '1Thess', '2thessalonians': '2Thess', '1timothy': '1Tim', '2timothy': '2Tim',
                            'titus': 'Titus', 'philemon': 'Phlm', 'hebrews': 'Heb', 'james': 'Jas',
                            '1peter': '1Pet', '2peter': '2Pet', '1john': '1John', '2john': '2John',
                            '3john': '3John', 'jude': 'Jude', 'revelation': 'Rev',
                        }
                        osis = book_map.get(book_name, book_name.capitalize())
                        book = CanonicalBook.objects.get(osis_code=osis)
                except CanonicalBook.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Book not found: {book_name}'))
                    continue

                # Process commentaries from this verse
                commentaries = data.get('commentaries', [])
                for commentary in commentaries:
                    author_name = commentary.get('author', 'Unknown')
                    period = commentary.get('period', '')

                    # Get or create author
                    if author_name not in authors_created:
                        author, _ = Author.objects.get_or_create(
                            name=author_name,
                            defaults={
                                'author_type': 'church_father' if 'AD' in period else 'modern',
                                'period': period,
                                'century': period,
                            }
                        )
                        authors_created[author_name] = author

                    author = authors_created[author_name]

                    # Prepare enrichment data
                    ai_summary = commentary.get('ai_summary', {})
                    argumentative_structure = commentary.get('argumentative_structure', {})
                    theological_analysis = commentary.get('theological_analysis', {})
                    spiritual_insight = commentary.get('spiritual_insight', {})

                    # Use Portuguese content if available, fallback to English
                    body_text = commentary.get('content_pt') or commentary.get('content_en', '')

                    # Calculate word count
                    word_count = len(body_text.split()) if body_text else 0

                    # Create or update entry
                    entry, created = CommentaryEntry.objects.get_or_create(
                        source=catena_source,
                        author=author,
                        book=book,
                        chapter=chapter,
                        verse_start=verse,
                        verse_end=verse,
                        defaults={
                            'title': commentary.get('title', f'{author_name} on {verse_reference}'),
                            'body_text': body_text,
                            'original_language': 'English',
                            'word_count': word_count,
                            'ai_summary': ai_summary,
                            'argumentative_structure': argumentative_structure,
                            'theological_analysis': theological_analysis,
                            'spiritual_insight': spiritual_insight,
                            'confidence_score': 0.85,
                            'is_complete': True,
                        }
                    )

                    if created:
                        entries_created += 1
                    else:
                        entries_updated += 1

            except json.JSONDecodeError:
                self.stdout.write(self.style.WARNING(f'Invalid JSON: {json_file}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Error processing {json_file}: {str(e)}'))

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Seed complete!\n'
                f'   Authors: {len(authors_created)}\n'
                f'   Commentaries created: {entries_created}\n'
                f'   Commentaries updated: {entries_updated}\n'
                f'   Source: {catena_source.name}'
            )
        )
