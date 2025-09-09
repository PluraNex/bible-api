"""
Django management command to populate bible data from JSON files.

Usage:
    python manage.py populate_bible_data
"""
import json
import os

from django.core.management.base import BaseCommand
from django.db import transaction

from bible.models import BookName, CanonicalBook, Language, License, Testament, Verse, Version


class Command(BaseCommand):
    help = "Populate bible data from JSON files"

    # Map JSON abbreviations to OSIS codes and canonical order
    BOOK_MAPPING = {
        "Gn": {"osis": "Gen", "order": 1, "testament": "OLD", "name_pt": "Gênesis", "chapters": 50},
        "Êx": {"osis": "Exod", "order": 2, "testament": "OLD", "name_pt": "Êxodo", "chapters": 40},
        "Lv": {"osis": "Lev", "order": 3, "testament": "OLD", "name_pt": "Levítico", "chapters": 27},
        "Nm": {"osis": "Num", "order": 4, "testament": "OLD", "name_pt": "Números", "chapters": 36},
        "Dt": {"osis": "Deut", "order": 5, "testament": "OLD", "name_pt": "Deuteronômio", "chapters": 34},
        "Js": {"osis": "Josh", "order": 6, "testament": "OLD", "name_pt": "Josué", "chapters": 24},
        "Jz": {"osis": "Judg", "order": 7, "testament": "OLD", "name_pt": "Juízes", "chapters": 21},
        "Rt": {"osis": "Ruth", "order": 8, "testament": "OLD", "name_pt": "Rute", "chapters": 4},
        "1Sm": {"osis": "1Sam", "order": 9, "testament": "OLD", "name_pt": "1 Samuel", "chapters": 31},
        "2Sm": {"osis": "2Sam", "order": 10, "testament": "OLD", "name_pt": "2 Samuel", "chapters": 24},
        "1Rs": {"osis": "1Kgs", "order": 11, "testament": "OLD", "name_pt": "1 Reis", "chapters": 22},
        "2Rs": {"osis": "2Kgs", "order": 12, "testament": "OLD", "name_pt": "2 Reis", "chapters": 25},
        "1Cr": {"osis": "1Chr", "order": 13, "testament": "OLD", "name_pt": "1 Crônicas", "chapters": 29},
        "2Cr": {"osis": "2Chr", "order": 14, "testament": "OLD", "name_pt": "2 Crônicas", "chapters": 36},
        "Ed": {"osis": "Ezra", "order": 15, "testament": "OLD", "name_pt": "Esdras", "chapters": 10},
        "Ne": {"osis": "Neh", "order": 16, "testament": "OLD", "name_pt": "Neemias", "chapters": 13},
        "Et": {"osis": "Esth", "order": 17, "testament": "OLD", "name_pt": "Ester", "chapters": 10},
        "Jó": {"osis": "Job", "order": 18, "testament": "OLD", "name_pt": "Jó", "chapters": 42},
        "Sl": {"osis": "Ps", "order": 19, "testament": "OLD", "name_pt": "Salmos", "chapters": 150},
        "Pv": {"osis": "Prov", "order": 20, "testament": "OLD", "name_pt": "Provérbios", "chapters": 31},
        "Ec": {"osis": "Eccl", "order": 21, "testament": "OLD", "name_pt": "Eclesiastes", "chapters": 12},
        "Ct": {"osis": "Song", "order": 22, "testament": "OLD", "name_pt": "Cantares", "chapters": 8},
        "Is": {"osis": "Isa", "order": 23, "testament": "OLD", "name_pt": "Isaías", "chapters": 66},
        "Jr": {"osis": "Jer", "order": 24, "testament": "OLD", "name_pt": "Jeremias", "chapters": 52},
        "Lm": {"osis": "Lam", "order": 25, "testament": "OLD", "name_pt": "Lamentações", "chapters": 5},
        "Ez": {"osis": "Ezek", "order": 26, "testament": "OLD", "name_pt": "Ezequiel", "chapters": 48},
        "Dn": {"osis": "Dan", "order": 27, "testament": "OLD", "name_pt": "Daniel", "chapters": 12},
        "Os": {"osis": "Hos", "order": 28, "testament": "OLD", "name_pt": "Oséias", "chapters": 14},
        "Jl": {"osis": "Joel", "order": 29, "testament": "OLD", "name_pt": "Joel", "chapters": 3},
        "Am": {"osis": "Amos", "order": 30, "testament": "OLD", "name_pt": "Amós", "chapters": 9},
        "Ob": {"osis": "Obad", "order": 31, "testament": "OLD", "name_pt": "Obadias", "chapters": 1},
        "Jn": {"osis": "Jonah", "order": 32, "testament": "OLD", "name_pt": "Jonas", "chapters": 4},
        "Mq": {"osis": "Mic", "order": 33, "testament": "OLD", "name_pt": "Miquéias", "chapters": 7},
        "Na": {"osis": "Nah", "order": 34, "testament": "OLD", "name_pt": "Naum", "chapters": 3},
        "Hc": {"osis": "Hab", "order": 35, "testament": "OLD", "name_pt": "Habacuque", "chapters": 3},
        "Sf": {"osis": "Zeph", "order": 36, "testament": "OLD", "name_pt": "Sofonias", "chapters": 3},
        "Ag": {"osis": "Hag", "order": 37, "testament": "OLD", "name_pt": "Ageu", "chapters": 2},
        "Zc": {"osis": "Zech", "order": 38, "testament": "OLD", "name_pt": "Zacarias", "chapters": 14},
        "Ml": {"osis": "Mal", "order": 39, "testament": "OLD", "name_pt": "Malaquias", "chapters": 4},
        # New Testament
        "Mt": {"osis": "Matt", "order": 40, "testament": "NEW", "name_pt": "Mateus", "chapters": 28},
        "Mc": {"osis": "Mark", "order": 41, "testament": "NEW", "name_pt": "Marcos", "chapters": 16},
        "Lc": {"osis": "Luke", "order": 42, "testament": "NEW", "name_pt": "Lucas", "chapters": 24},
        "Jo": {"osis": "John", "order": 43, "testament": "NEW", "name_pt": "João", "chapters": 21},
        "At": {"osis": "Acts", "order": 44, "testament": "NEW", "name_pt": "Atos", "chapters": 28},
        "Rm": {"osis": "Rom", "order": 45, "testament": "NEW", "name_pt": "Romanos", "chapters": 16},
        "1Co": {"osis": "1Cor", "order": 46, "testament": "NEW", "name_pt": "1 Coríntios", "chapters": 16},
        "2Co": {"osis": "2Cor", "order": 47, "testament": "NEW", "name_pt": "2 Coríntios", "chapters": 13},
        "Gl": {"osis": "Gal", "order": 48, "testament": "NEW", "name_pt": "Gálatas", "chapters": 6},
        "Ef": {"osis": "Eph", "order": 49, "testament": "NEW", "name_pt": "Efésios", "chapters": 6},
        "Fp": {"osis": "Phil", "order": 50, "testament": "NEW", "name_pt": "Filipenses", "chapters": 4},
        "Cl": {"osis": "Col", "order": 51, "testament": "NEW", "name_pt": "Colossenses", "chapters": 4},
        "1Ts": {"osis": "1Thess", "order": 52, "testament": "NEW", "name_pt": "1 Tessalonicenses", "chapters": 5},
        "2Ts": {"osis": "2Thess", "order": 53, "testament": "NEW", "name_pt": "2 Tessalonicenses", "chapters": 3},
        "1Tm": {"osis": "1Tim", "order": 54, "testament": "NEW", "name_pt": "1 Timóteo", "chapters": 6},
        "2Tm": {"osis": "2Tim", "order": 55, "testament": "NEW", "name_pt": "2 Timóteo", "chapters": 4},
        "Tt": {"osis": "Titus", "order": 56, "testament": "NEW", "name_pt": "Tito", "chapters": 3},
        "Fm": {"osis": "Phlm", "order": 57, "testament": "NEW", "name_pt": "Filemom", "chapters": 1},
        "Hb": {"osis": "Heb", "order": 58, "testament": "NEW", "name_pt": "Hebreus", "chapters": 13},
        "Tg": {"osis": "Jas", "order": 59, "testament": "NEW", "name_pt": "Tiago", "chapters": 5},
        "1Pe": {"osis": "1Pet", "order": 60, "testament": "NEW", "name_pt": "1 Pedro", "chapters": 5},
        "2Pe": {"osis": "2Pet", "order": 61, "testament": "NEW", "name_pt": "2 Pedro", "chapters": 3},
        "1Jo": {"osis": "1John", "order": 62, "testament": "NEW", "name_pt": "1 João", "chapters": 5},
        "2Jo": {"osis": "2John", "order": 63, "testament": "NEW", "name_pt": "2 João", "chapters": 1},
        "3Jo": {"osis": "3John", "order": 64, "testament": "NEW", "name_pt": "3 João", "chapters": 1},
        "Jd": {"osis": "Jude", "order": 65, "testament": "NEW", "name_pt": "Judas", "chapters": 1},
        "Ap": {"osis": "Rev", "order": 66, "testament": "NEW", "name_pt": "Apocalipse", "chapters": 22},
    }

    VERSION_MAPPING = {
        "ARA": {"name": "Almeida Revista e Atualizada", "code": "PT_ARA"},
        "ACF": {"name": "Almeida Corrigida e Revisada Fiel", "code": "PT_ACF"},
        "ARC": {"name": "Almeida Revista e Corrigida", "code": "PT_ARC"},
        "NVI": {"name": "Nova Versão Internacional", "code": "PT_NVI"},
        "NTLH": {"name": "Nova Tradução na Linguagem de Hoje", "code": "PT_NTLH"},
        "NVT": {"name": "Nova Versão Transformadora", "code": "PT_NVT"},
        "NBV": {"name": "Nova Bíblia Viva", "code": "PT_NBV"},
        "KJA": {"name": "King James Atualizada", "code": "PT_KJA"},
        "NAA": {"name": "Nova Almeida Atualizada", "code": "PT_NAA"},
        "AS21": {"name": "Almeida Século 21", "code": "PT_AS21"},
        "JFAA": {"name": "João Ferreira de Almeida Atualizada", "code": "PT_JFAA"},
        "KJF": {"name": "King James Fiel", "code": "PT_KJF"},
        "TB": {"name": "Tradução Brasileira", "code": "PT_TB"},
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--bible-version",
            type=str,
            help="Specific Bible version to populate (e.g., ARA, NVI)",
        )
        parser.add_argument(
            "--data-dir",
            type=str,
            default="data/datasets/inst/json",
            help="Directory containing JSON files",
        )

    def handle(self, *args, **options):
        data_dir = options["data_dir"]
        version_filter = options.get("bible_version")

        if not os.path.exists(data_dir):
            self.stdout.write(self.style.ERROR(f"Data directory {data_dir} not found"))
            return

        with transaction.atomic():
            self._create_base_data()

            json_files = [f for f in os.listdir(data_dir) if f.endswith(".json")]

            for json_file in json_files:
                version_key = json_file.replace(".json", "")

                if version_filter and version_key != version_filter:
                    continue

                if version_key not in self.VERSION_MAPPING:
                    self.stdout.write(self.style.WARNING(f"Unknown version: {version_key}"))
                    continue

                self.stdout.write(f"Processing {version_key}...")
                self._process_version(data_dir, json_file, version_key)

        self.stdout.write(self.style.SUCCESS("Successfully populated bible data"))

    def _create_base_data(self):
        """Create base language, testament, and canonical book structure."""
        # Create Portuguese language
        portuguese, created = Language.objects.get_or_create(code="pt-BR", defaults={"name": "Português (Brasil)"})
        if created:
            self.stdout.write("Created Portuguese language")

        # Create Public Domain license
        license_pd, created = License.objects.get_or_create(
            code="PD", defaults={"name": "Public Domain", "url": "https://creativecommons.org/publicdomain/mark/1.0/"}
        )
        if created:
            self.stdout.write("Created Public Domain license")

        # Create testaments
        old_testament, created = Testament.objects.get_or_create(
            id=1, defaults={"name": "Antigo Testamento", "description": "Livros do Antigo Testamento"}
        )
        if created:
            self.stdout.write("Created Old Testament")

        new_testament, created = Testament.objects.get_or_create(
            id=2, defaults={"name": "Novo Testamento", "description": "Livros do Novo Testamento"}
        )
        if created:
            self.stdout.write("Created New Testament")

        # Create canonical books
        for abbrev, book_data in self.BOOK_MAPPING.items():
            testament = old_testament if book_data["testament"] == "OLD" else new_testament

            canonical_book, created = CanonicalBook.objects.get_or_create(
                osis_code=book_data["osis"],
                defaults={
                    "canonical_order": book_data["order"],
                    "testament": testament,
                    "chapter_count": book_data["chapters"],
                },
            )

            if created:
                # Create Portuguese book name
                BookName.objects.get_or_create(
                    canonical_book=canonical_book,
                    language=portuguese,
                    version=None,  # Generic name, not version-specific
                    defaults={"name": book_data["name_pt"], "abbreviation": abbrev},
                )

        self.stdout.write("Created canonical books and names")

    def _process_version(self, data_dir, json_file, version_key):
        """Process a single Bible version JSON file."""
        file_path = os.path.join(data_dir, json_file)

        with open(file_path, encoding="utf-8") as f:
            books_data = json.load(f)

        # Get Portuguese language and license
        portuguese = Language.objects.get(code="pt-BR")
        license_pd = License.objects.get(code="PD")

        # Create version
        version_info = self.VERSION_MAPPING[version_key]
        version, created = Version.objects.get_or_create(
            code=version_info["code"],
            defaults={
                "name": version_info["name"],
                "language": portuguese,
                "license": license_pd,
                "versification": "PT",
                "copyright": f'© {version_info["name"]}',
            },
        )

        if created:
            self.stdout.write(f"Created version: {version.name}")
        else:
            # Clear existing verses for this version
            Verse.objects.filter(version=version).delete()
            self.stdout.write(f"Cleared existing verses for: {version.name}")

        # Process books with bulk_create for performance
        verses_to_create = []
        for book_data in books_data:
            abbrev = book_data["abbrev"]

            if abbrev not in self.BOOK_MAPPING:
                self.stdout.write(self.style.WARNING(f"  Skipping book: {abbrev} (not in BOOK_MAPPING)"))
                continue

            book_info = self.BOOK_MAPPING[abbrev]
            canonical_book = CanonicalBook.objects.get(osis_code=book_info["osis"])

            # Process chapters
            for chapter_num, verses in enumerate(book_data["chapters"], 1):
                for verse_num, verse_text in enumerate(verses, 1):
                    # Handle cases where verse_text might be a list (data inconsistency)
                    if isinstance(verse_text, list):
                        # Join multiple parts with a space, common in some versions
                        processed_text = " ".join(verse_text).strip()
                        self.stdout.write(
                            self.style.WARNING(f"  Fixed list verse in {abbrev} {chapter_num}:{verse_num}")
                        )
                    elif isinstance(verse_text, str):
                        processed_text = verse_text.strip()
                    else:
                        # Skip non-string, non-list verses (shouldn't happen)
                        self.stdout.write(
                            self.style.ERROR(
                                f"  Skipping invalid verse type in {abbrev} {chapter_num}:{verse_num}: {type(verse_text)}"
                            )
                        )
                        continue

                    verses_to_create.append(
                        Verse(
                            book=canonical_book,
                            version=version,
                            chapter=chapter_num,
                            number=verse_num,
                            text=processed_text,
                        )
                    )

        # Bulk create all verses at once for massive performance improvement
        Verse.objects.bulk_create(verses_to_create, batch_size=1000)
        self.stdout.write(f"  Successfully created {len(verses_to_create)} verses for {version.name}")
