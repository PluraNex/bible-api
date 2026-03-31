"""
Seed Portuguese and English book names into BookName table.

Usage:
    python manage.py seed_book_names
    python manage.py seed_book_names --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from bible.models import CanonicalBook, Language
from bible.models.books import BookName


BOOK_NAMES = {
    # OSIS: (Portuguese, Abbreviation PT, English, Abbreviation EN)
    "Gen": ("Gênesis", "Gn", "Genesis", "Gen"),
    "Exod": ("Êxodo", "Êx", "Exodus", "Exod"),
    "Lev": ("Levítico", "Lv", "Leviticus", "Lev"),
    "Num": ("Números", "Nm", "Numbers", "Num"),
    "Deut": ("Deuteronômio", "Dt", "Deuteronomy", "Deut"),
    "Josh": ("Josué", "Js", "Joshua", "Josh"),
    "Judg": ("Juízes", "Jz", "Judges", "Judg"),
    "Ruth": ("Rute", "Rt", "Ruth", "Ruth"),
    "1Sam": ("1 Samuel", "1Sm", "1 Samuel", "1Sam"),
    "2Sam": ("2 Samuel", "2Sm", "2 Samuel", "2Sam"),
    "1Kgs": ("1 Reis", "1Rs", "1 Kings", "1Kgs"),
    "2Kgs": ("2 Reis", "2Rs", "2 Kings", "2Kgs"),
    "1Chr": ("1 Crônicas", "1Cr", "1 Chronicles", "1Chr"),
    "2Chr": ("2 Crônicas", "2Cr", "2 Chronicles", "2Chr"),
    "Ezra": ("Esdras", "Ed", "Ezra", "Ezra"),
    "Neh": ("Neemias", "Ne", "Nehemiah", "Neh"),
    "Esth": ("Ester", "Et", "Esther", "Esth"),
    "Job": ("Jó", "Jó", "Job", "Job"),
    "Ps": ("Salmos", "Sl", "Psalms", "Ps"),
    "Prov": ("Provérbios", "Pv", "Proverbs", "Prov"),
    "Eccl": ("Eclesiastes", "Ec", "Ecclesiastes", "Eccl"),
    "Song": ("Cânticos", "Ct", "Song of Solomon", "Song"),
    "Isa": ("Isaías", "Is", "Isaiah", "Isa"),
    "Jer": ("Jeremias", "Jr", "Jeremiah", "Jer"),
    "Lam": ("Lamentações", "Lm", "Lamentations", "Lam"),
    "Ezek": ("Ezequiel", "Ez", "Ezekiel", "Ezek"),
    "Dan": ("Daniel", "Dn", "Daniel", "Dan"),
    "Hos": ("Oséias", "Os", "Hosea", "Hos"),
    "Joel": ("Joel", "Jl", "Joel", "Joel"),
    "Amos": ("Amós", "Am", "Amos", "Amos"),
    "Obad": ("Obadias", "Ob", "Obadiah", "Obad"),
    "Jonah": ("Jonas", "Jn", "Jonah", "Jonah"),
    "Mic": ("Miquéias", "Mq", "Micah", "Mic"),
    "Nah": ("Naum", "Na", "Nahum", "Nah"),
    "Hab": ("Habacuque", "Hc", "Habakkuk", "Hab"),
    "Zeph": ("Sofonias", "Sf", "Zephaniah", "Zeph"),
    "Hag": ("Ageu", "Ag", "Haggai", "Hag"),
    "Zech": ("Zacarias", "Zc", "Zechariah", "Zech"),
    "Mal": ("Malaquias", "Ml", "Malachi", "Mal"),
    "Matt": ("Mateus", "Mt", "Matthew", "Matt"),
    "Mark": ("Marcos", "Mc", "Mark", "Mark"),
    "Luke": ("Lucas", "Lc", "Luke", "Luke"),
    "John": ("João", "Jo", "John", "John"),
    "Acts": ("Atos", "At", "Acts", "Acts"),
    "Rom": ("Romanos", "Rm", "Romans", "Rom"),
    "1Cor": ("1 Coríntios", "1Co", "1 Corinthians", "1Cor"),
    "2Cor": ("2 Coríntios", "2Co", "2 Corinthians", "2Cor"),
    "Gal": ("Gálatas", "Gl", "Galatians", "Gal"),
    "Eph": ("Efésios", "Ef", "Ephesians", "Eph"),
    "Phil": ("Filipenses", "Fp", "Philippians", "Phil"),
    "Col": ("Colossenses", "Cl", "Colossians", "Col"),
    "1Thess": ("1 Tessalonicenses", "1Ts", "1 Thessalonians", "1Thess"),
    "2Thess": ("2 Tessalonicenses", "2Ts", "2 Thessalonians", "2Thess"),
    "1Tim": ("1 Timóteo", "1Tm", "1 Timothy", "1Tim"),
    "2Tim": ("2 Timóteo", "2Tm", "2 Timothy", "2Tim"),
    "Titus": ("Tito", "Tt", "Titus", "Titus"),
    "Phlm": ("Filemom", "Fm", "Philemon", "Phlm"),
    "Heb": ("Hebreus", "Hb", "Hebrews", "Heb"),
    "Jas": ("Tiago", "Tg", "James", "Jas"),
    "1Pet": ("1 Pedro", "1Pe", "1 Peter", "1Pet"),
    "2Pet": ("2 Pedro", "2Pe", "2 Peter", "2Pet"),
    "1John": ("1 João", "1Jo", "1 John", "1John"),
    "2John": ("2 João", "2Jo", "2 John", "2John"),
    "3John": ("3 João", "3Jo", "3 John", "3John"),
    "Jude": ("Judas", "Jd", "Jude", "Jude"),
    "Rev": ("Apocalipse", "Ap", "Revelation", "Rev"),
}


class Command(BaseCommand):
    help = "Seed Portuguese and English book names into BookName table"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Show what would be done")

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Ensure languages exist
        pt_lang, _ = Language.objects.get_or_create(code="pt", defaults={"name": "Portuguese"})
        en_lang, _ = Language.objects.get_or_create(code="en", defaults={"name": "English"})

        created_count = 0
        skipped_count = 0

        for osis_code, (pt_name, pt_abbr, en_name, en_abbr) in BOOK_NAMES.items():
            try:
                book = CanonicalBook.objects.get(osis_code=osis_code)
            except CanonicalBook.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  Book {osis_code} not found, skipping"))
                continue

            # Portuguese name
            _, created = BookName.objects.get_or_create(
                canonical_book=book,
                language=pt_lang,
                version=None,
                defaults={"name": pt_name, "abbreviation": pt_abbr},
            )
            if created:
                created_count += 1
                if not dry_run:
                    self.stdout.write(f"  + {osis_code} → {pt_name} (pt)")
            else:
                skipped_count += 1

            # English name
            _, created = BookName.objects.get_or_create(
                canonical_book=book,
                language=en_lang,
                version=None,
                defaults={"name": en_name, "abbreviation": en_abbr},
            )
            if created:
                created_count += 1
                if not dry_run:
                    self.stdout.write(f"  + {osis_code} → {en_name} (en)")
            else:
                skipped_count += 1

        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{prefix}Done: {created_count} names created, {skipped_count} already existed"
            )
        )
