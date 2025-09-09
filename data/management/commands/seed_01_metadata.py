from django.core.management.base import BaseCommand
from django.db import transaction

from bible.models import BookName, CanonicalBook, Language, Testament

# Estrutura de dados central para todos os livros, incluindo nomes em múltiplos idiomas
# Esta é a "fonte da verdade" para os metadados dos livros.
BOOKS_METADATA = [
    # ANTIGO TESTAMENTO
    # Pentateuco
    {
        "order": 1,
        "osis": "Gen",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 50,
        "names": [
            {"lang_code": "pt-BR", "name": "Gênesis", "abbrev": "Gn"},
            {"lang_code": "en-US", "name": "Genesis", "abbrev": "Gen"},
        ],
    },
    {
        "order": 2,
        "osis": "Exod",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 40,
        "names": [
            {"lang_code": "pt-BR", "name": "Êxodo", "abbrev": "Êx"},
            {"lang_code": "en-US", "name": "Exodus", "abbrev": "Exod"},
        ],
    },
    {
        "order": 3,
        "osis": "Lev",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 27,
        "names": [
            {"lang_code": "pt-BR", "name": "Levítico", "abbrev": "Lv"},
            {"lang_code": "en-US", "name": "Leviticus", "abbrev": "Lev"},
        ],
    },
    {
        "order": 4,
        "osis": "Num",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 36,
        "names": [
            {"lang_code": "pt-BR", "name": "Números", "abbrev": "Nm"},
            {"lang_code": "en-US", "name": "Numbers", "abbrev": "Num"},
        ],
    },
    {
        "order": 5,
        "osis": "Deut",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 34,
        "names": [
            {"lang_code": "pt-BR", "name": "Deuteronômio", "abbrev": "Dt"},
            {"lang_code": "en-US", "name": "Deuteronomy", "abbrev": "Deut"},
        ],
    },
    # Históricos
    {
        "order": 6,
        "osis": "Josh",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 24,
        "names": [
            {"lang_code": "pt-BR", "name": "Josué", "abbrev": "Js"},
            {"lang_code": "en-US", "name": "Joshua", "abbrev": "Josh"},
        ],
    },
    {
        "order": 7,
        "osis": "Judg",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 21,
        "names": [
            {"lang_code": "pt-BR", "name": "Juízes", "abbrev": "Jz"},
            {"lang_code": "en-US", "name": "Judges", "abbrev": "Judg"},
        ],
    },
    {
        "order": 8,
        "osis": "Ruth",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 4,
        "names": [
            {"lang_code": "pt-BR", "name": "Rute", "abbrev": "Rt"},
            {"lang_code": "en-US", "name": "Ruth", "abbrev": "Ruth"},
        ],
    },
    {
        "order": 9,
        "osis": "1Sam",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 31,
        "names": [
            {"lang_code": "pt-BR", "name": "1 Samuel", "abbrev": "1Sm"},
            {"lang_code": "en-US", "name": "1 Samuel", "abbrev": "1Sam"},
        ],
    },
    {
        "order": 10,
        "osis": "2Sam",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 24,
        "names": [
            {"lang_code": "pt-BR", "name": "2 Samuel", "abbrev": "2Sm"},
            {"lang_code": "en-US", "name": "2 Samuel", "abbrev": "2Sam"},
        ],
    },
    {
        "order": 11,
        "osis": "1Kgs",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 22,
        "names": [
            {"lang_code": "pt-BR", "name": "1 Reis", "abbrev": "1Rs"},
            {"lang_code": "en-US", "name": "1 Kings", "abbrev": "1Kgs"},
        ],
    },
    {
        "order": 12,
        "osis": "2Kgs",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 25,
        "names": [
            {"lang_code": "pt-BR", "name": "2 Reis", "abbrev": "2Rs"},
            {"lang_code": "en-US", "name": "2 Kings", "abbrev": "2Kgs"},
        ],
    },
    {
        "order": 13,
        "osis": "1Chr",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 29,
        "names": [
            {"lang_code": "pt-BR", "name": "1 Crônicas", "abbrev": "1Cr"},
            {"lang_code": "en-US", "name": "1 Chronicles", "abbrev": "1Chr"},
        ],
    },
    {
        "order": 14,
        "osis": "2Chr",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 36,
        "names": [
            {"lang_code": "pt-BR", "name": "2 Crônicas", "abbrev": "2Cr"},
            {"lang_code": "en-US", "name": "2 Chronicles", "abbrev": "2Chr"},
        ],
    },
    {
        "order": 15,
        "osis": "Ezra",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 10,
        "names": [
            {"lang_code": "pt-BR", "name": "Esdras", "abbrev": "Ed"},
            {"lang_code": "en-US", "name": "Ezra", "abbrev": "Ezra"},
        ],
    },
    {
        "order": 16,
        "osis": "Neh",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 13,
        "names": [
            {"lang_code": "pt-BR", "name": "Neemias", "abbrev": "Ne"},
            {"lang_code": "en-US", "name": "Nehemiah", "abbrev": "Neh"},
        ],
    },
    {
        "order": 17,
        "osis": "Esth",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 10,
        "names": [
            {"lang_code": "pt-BR", "name": "Ester", "abbrev": "Et"},
            {"lang_code": "en-US", "name": "Esther", "abbrev": "Esth"},
        ],
    },
    # Poéticos e Sapienciais
    {
        "order": 18,
        "osis": "Job",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 42,
        "names": [
            {"lang_code": "pt-BR", "name": "Jó", "abbrev": "Jó"},
            {"lang_code": "en-US", "name": "Job", "abbrev": "Job"},
        ],
    },
    {
        "order": 19,
        "osis": "Ps",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 150,
        "names": [
            {"lang_code": "pt-BR", "name": "Salmos", "abbrev": "Sl"},
            {"lang_code": "en-US", "name": "Psalms", "abbrev": "Ps"},
        ],
    },
    {
        "order": 20,
        "osis": "Prov",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 31,
        "names": [
            {"lang_code": "pt-BR", "name": "Provérbios", "abbrev": "Pv"},
            {"lang_code": "en-US", "name": "Proverbs", "abbrev": "Prov"},
        ],
    },
    {
        "order": 21,
        "osis": "Eccl",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 12,
        "names": [
            {"lang_code": "pt-BR", "name": "Eclesiastes", "abbrev": "Ec"},
            {"lang_code": "en-US", "name": "Ecclesiastes", "abbrev": "Eccl"},
        ],
    },
    {
        "order": 22,
        "osis": "Song",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 8,
        "names": [
            {"lang_code": "pt-BR", "name": "Cantares", "abbrev": "Ct"},
            {"lang_code": "en-US", "name": "Song of Songs", "abbrev": "Song"},
        ],
    },
    # Profetas Maiores
    {
        "order": 23,
        "osis": "Isa",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 66,
        "names": [
            {"lang_code": "pt-BR", "name": "Isaías", "abbrev": "Is"},
            {"lang_code": "en-US", "name": "Isaiah", "abbrev": "Isa"},
        ],
    },
    {
        "order": 24,
        "osis": "Jer",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 52,
        "names": [
            {"lang_code": "pt-BR", "name": "Jeremias", "abbrev": "Jr"},
            {"lang_code": "en-US", "name": "Jeremiah", "abbrev": "Jer"},
        ],
    },
    {
        "order": 25,
        "osis": "Lam",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 5,
        "names": [
            {"lang_code": "pt-BR", "name": "Lamentações", "abbrev": "Lm"},
            {"lang_code": "en-US", "name": "Lamentations", "abbrev": "Lam"},
        ],
    },
    {
        "order": 26,
        "osis": "Ezek",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 48,
        "names": [
            {"lang_code": "pt-BR", "name": "Ezequiel", "abbrev": "Ez"},
            {"lang_code": "en-US", "name": "Ezekiel", "abbrev": "Ezek"},
        ],
    },
    {
        "order": 27,
        "osis": "Dan",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 12,
        "names": [
            {"lang_code": "pt-BR", "name": "Daniel", "abbrev": "Dn"},
            {"lang_code": "en-US", "name": "Daniel", "abbrev": "Dan"},
        ],
    },
    # Profetas Menores
    {
        "order": 28,
        "osis": "Hos",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 14,
        "names": [
            {"lang_code": "pt-BR", "name": "Oséias", "abbrev": "Os"},
            {"lang_code": "en-US", "name": "Hosea", "abbrev": "Hos"},
        ],
    },
    {
        "order": 29,
        "osis": "Joel",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 3,
        "names": [
            {"lang_code": "pt-BR", "name": "Joel", "abbrev": "Jl"},
            {"lang_code": "en-US", "name": "Joel", "abbrev": "Joel"},
        ],
    },
    {
        "order": 30,
        "osis": "Amos",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 9,
        "names": [
            {"lang_code": "pt-BR", "name": "Amós", "abbrev": "Am"},
            {"lang_code": "en-US", "name": "Amos", "abbrev": "Amos"},
        ],
    },
    {
        "order": 31,
        "osis": "Obad",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 1,
        "names": [
            {"lang_code": "pt-BR", "name": "Obadias", "abbrev": "Ob"},
            {"lang_code": "en-US", "name": "Obadiah", "abbrev": "Obad"},
        ],
    },
    {
        "order": 32,
        "osis": "Jonah",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 4,
        "names": [
            {"lang_code": "pt-BR", "name": "Jonas", "abbrev": "Jn"},
            {"lang_code": "en-US", "name": "Jonah", "abbrev": "Jonah"},
        ],
    },
    {
        "order": 33,
        "osis": "Mic",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 7,
        "names": [
            {"lang_code": "pt-BR", "name": "Miquéias", "abbrev": "Mq"},
            {"lang_code": "en-US", "name": "Micah", "abbrev": "Mic"},
        ],
    },
    {
        "order": 34,
        "osis": "Nah",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 3,
        "names": [
            {"lang_code": "pt-BR", "name": "Naum", "abbrev": "Na"},
            {"lang_code": "en-US", "name": "Nahum", "abbrev": "Nah"},
        ],
    },
    {
        "order": 35,
        "osis": "Hab",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 3,
        "names": [
            {"lang_code": "pt-BR", "name": "Habacuque", "abbrev": "Hc"},
            {"lang_code": "en-US", "name": "Habakkuk", "abbrev": "Hab"},
        ],
    },
    {
        "order": 36,
        "osis": "Zeph",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 3,
        "names": [
            {"lang_code": "pt-BR", "name": "Sofonias", "abbrev": "Sf"},
            {"lang_code": "en-US", "name": "Zephaniah", "abbrev": "Zeph"},
        ],
    },
    {
        "order": 37,
        "osis": "Hag",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 2,
        "names": [
            {"lang_code": "pt-BR", "name": "Ageu", "abbrev": "Ag"},
            {"lang_code": "en-US", "name": "Haggai", "abbrev": "Hag"},
        ],
    },
    {
        "order": 38,
        "osis": "Zech",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 14,
        "names": [
            {"lang_code": "pt-BR", "name": "Zacarias", "abbrev": "Zc"},
            {"lang_code": "en-US", "name": "Zechariah", "abbrev": "Zech"},
        ],
    },
    {
        "order": 39,
        "osis": "Mal",
        "testament_code": "OLD",
        "is_deuterocanonical": False,
        "chapter_count": 4,
        "names": [
            {"lang_code": "pt-BR", "name": "Malaquias", "abbrev": "Ml"},
            {"lang_code": "en-US", "name": "Malachi", "abbrev": "Mal"},
        ],
    },
    # NOVO TESTAMENTO
    # Evangelhos
    {
        "order": 40,
        "osis": "Matt",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 28,
        "names": [
            {"lang_code": "pt-BR", "name": "Mateus", "abbrev": "Mt"},
            {"lang_code": "en-US", "name": "Matthew", "abbrev": "Matt"},
        ],
    },
    {
        "order": 41,
        "osis": "Mark",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 16,
        "names": [
            {"lang_code": "pt-BR", "name": "Marcos", "abbrev": "Mc"},
            {"lang_code": "en-US", "name": "Mark", "abbrev": "Mark"},
        ],
    },
    {
        "order": 42,
        "osis": "Luke",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 24,
        "names": [
            {"lang_code": "pt-BR", "name": "Lucas", "abbrev": "Lc"},
            {"lang_code": "en-US", "name": "Luke", "abbrev": "Luke"},
        ],
    },
    {
        "order": 43,
        "osis": "John",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 21,
        "names": [
            {"lang_code": "pt-BR", "name": "João", "abbrev": "Jo"},
            {"lang_code": "en-US", "name": "John", "abbrev": "John"},
        ],
    },
    # Histórico
    {
        "order": 44,
        "osis": "Acts",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 28,
        "names": [
            {"lang_code": "pt-BR", "name": "Atos", "abbrev": "At"},
            {"lang_code": "en-US", "name": "Acts", "abbrev": "Acts"},
        ],
    },
    # Cartas Paulinas
    {
        "order": 45,
        "osis": "Rom",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 16,
        "names": [
            {"lang_code": "pt-BR", "name": "Romanos", "abbrev": "Rm"},
            {"lang_code": "en-US", "name": "Romans", "abbrev": "Rom"},
        ],
    },
    {
        "order": 46,
        "osis": "1Cor",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 16,
        "names": [
            {"lang_code": "pt-BR", "name": "1 Coríntios", "abbrev": "1Co"},
            {"lang_code": "en-US", "name": "1 Corinthians", "abbrev": "1Cor"},
        ],
    },
    {
        "order": 47,
        "osis": "2Cor",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 13,
        "names": [
            {"lang_code": "pt-BR", "name": "2 Coríntios", "abbrev": "2Co"},
            {"lang_code": "en-US", "name": "2 Corinthians", "abbrev": "2Cor"},
        ],
    },
    {
        "order": 48,
        "osis": "Gal",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 6,
        "names": [
            {"lang_code": "pt-BR", "name": "Gálatas", "abbrev": "Gl"},
            {"lang_code": "en-US", "name": "Galatians", "abbrev": "Gal"},
        ],
    },
    {
        "order": 49,
        "osis": "Eph",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 6,
        "names": [
            {"lang_code": "pt-BR", "name": "Efésios", "abbrev": "Ef"},
            {"lang_code": "en-US", "name": "Ephesians", "abbrev": "Eph"},
        ],
    },
    {
        "order": 50,
        "osis": "Phil",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 4,
        "names": [
            {"lang_code": "pt-BR", "name": "Filipenses", "abbrev": "Fp"},
            {"lang_code": "en-US", "name": "Philippians", "abbrev": "Phil"},
        ],
    },
    {
        "order": 51,
        "osis": "Col",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 4,
        "names": [
            {"lang_code": "pt-BR", "name": "Colossenses", "abbrev": "Cl"},
            {"lang_code": "en-US", "name": "Colossians", "abbrev": "Col"},
        ],
    },
    {
        "order": 52,
        "osis": "1Thess",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 5,
        "names": [
            {"lang_code": "pt-BR", "name": "1 Tessalonicenses", "abbrev": "1Ts"},
            {"lang_code": "en-US", "name": "1 Thessalonians", "abbrev": "1Thess"},
        ],
    },
    {
        "order": 53,
        "osis": "2Thess",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 3,
        "names": [
            {"lang_code": "pt-BR", "name": "2 Tessalonicenses", "abbrev": "2Ts"},
            {"lang_code": "en-US", "name": "2 Thessalonians", "abbrev": "2Thess"},
        ],
    },
    {
        "order": 54,
        "osis": "1Tim",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 6,
        "names": [
            {"lang_code": "pt-BR", "name": "1 Timóteo", "abbrev": "1Tm"},
            {"lang_code": "en-US", "name": "1 Timothy", "abbrev": "1Tim"},
        ],
    },
    {
        "order": 55,
        "osis": "2Tim",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 4,
        "names": [
            {"lang_code": "pt-BR", "name": "2 Timóteo", "abbrev": "2Tm"},
            {"lang_code": "en-US", "name": "2 Timothy", "abbrev": "2Tim"},
        ],
    },
    {
        "order": 56,
        "osis": "Titus",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 3,
        "names": [
            {"lang_code": "pt-BR", "name": "Tito", "abbrev": "Tt"},
            {"lang_code": "en-US", "name": "Titus", "abbrev": "Titus"},
        ],
    },
    {
        "order": 57,
        "osis": "Phlm",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 1,
        "names": [
            {"lang_code": "pt-BR", "name": "Filemom", "abbrev": "Fm"},
            {"lang_code": "en-US", "name": "Philemon", "abbrev": "Phlm"},
        ],
    },
    # Cartas Gerais
    {
        "order": 58,
        "osis": "Heb",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 13,
        "names": [
            {"lang_code": "pt-BR", "name": "Hebreus", "abbrev": "Hb"},
            {"lang_code": "en-US", "name": "Hebrews", "abbrev": "Heb"},
        ],
    },
    {
        "order": 59,
        "osis": "Jas",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 5,
        "names": [
            {"lang_code": "pt-BR", "name": "Tiago", "abbrev": "Tg"},
            {"lang_code": "en-US", "name": "James", "abbrev": "Jas"},
        ],
    },
    {
        "order": 60,
        "osis": "1Pet",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 5,
        "names": [
            {"lang_code": "pt-BR", "name": "1 Pedro", "abbrev": "1Pe"},
            {"lang_code": "en-US", "name": "1 Peter", "abbrev": "1Pet"},
        ],
    },
    {
        "order": 61,
        "osis": "2Pet",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 3,
        "names": [
            {"lang_code": "pt-BR", "name": "2 Pedro", "abbrev": "2Pe"},
            {"lang_code": "en-US", "name": "2 Peter", "abbrev": "2Pet"},
        ],
    },
    {
        "order": 62,
        "osis": "1John",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 5,
        "names": [
            {"lang_code": "pt-BR", "name": "1 João", "abbrev": "1Jo"},
            {"lang_code": "en-US", "name": "1 John", "abbrev": "1John"},
        ],
    },
    {
        "order": 63,
        "osis": "2John",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 1,
        "names": [
            {"lang_code": "pt-BR", "name": "2 João", "abbrev": "2Jo"},
            {"lang_code": "en-US", "name": "2 John", "abbrev": "2John"},
        ],
    },
    {
        "order": 64,
        "osis": "3John",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 1,
        "names": [
            {"lang_code": "pt-BR", "name": "3 João", "abbrev": "3Jo"},
            {"lang_code": "en-US", "name": "3 John", "abbrev": "3John"},
        ],
    },
    {
        "order": 65,
        "osis": "Jude",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 1,
        "names": [
            {"lang_code": "pt-BR", "name": "Judas", "abbrev": "Jd"},
            {"lang_code": "en-US", "name": "Jude", "abbrev": "Jude"},
        ],
    },
    {
        "order": 66,
        "osis": "Rev",
        "testament_code": "NEW",
        "is_deuterocanonical": False,
        "chapter_count": 22,
        "names": [
            {"lang_code": "pt-BR", "name": "Apocalipse", "abbrev": "Ap"},
            {"lang_code": "en-US", "name": "Revelation", "abbrev": "Rev"},
        ],
    },
    # DEUTEROCANÔNICOS/APÓCRIFOS
    {
        "order": 67,
        "osis": "Tob",
        "testament_code": "APO",
        "is_deuterocanonical": True,
        "chapter_count": 14,
        "names": [{"lang_code": "en-US", "name": "Tobit", "abbrev": "Tob"}],
    },
    {
        "order": 68,
        "osis": "Jdt",
        "testament_code": "APO",
        "is_deuterocanonical": True,
        "chapter_count": 16,
        "names": [{"lang_code": "en-US", "name": "Judith", "abbrev": "Jdt"}],
    },
    {
        "order": 69,
        "osis": "Wis",
        "testament_code": "APO",
        "is_deuterocanonical": True,
        "chapter_count": 19,
        "names": [{"lang_code": "en-US", "name": "Wisdom", "abbrev": "Wis"}],
    },
    {
        "order": 70,
        "osis": "Sir",
        "testament_code": "APO",
        "is_deuterocanonical": True,
        "chapter_count": 51,
        "names": [{"lang_code": "en-US", "name": "Sirach", "abbrev": "Sir"}],
    },
    {
        "order": 71,
        "osis": "Bar",
        "testament_code": "APO",
        "is_deuterocanonical": True,
        "chapter_count": 6,
        "names": [{"lang_code": "en-US", "name": "Baruch", "abbrev": "Bar"}],
    },
    {
        "order": 72,
        "osis": "1Macc",
        "testament_code": "APO",
        "is_deuterocanonical": True,
        "chapter_count": 16,
        "names": [{"lang_code": "en-US", "name": "1 Maccabees", "abbrev": "1Macc"}],
    },
    {
        "order": 73,
        "osis": "2Macc",
        "testament_code": "APO",
        "is_deuterocanonical": True,
        "chapter_count": 15,
        "names": [{"lang_code": "en-US", "name": "2 Maccabees", "abbrev": "2Macc"}],
    },
]

LANGUAGES_DATA = [
    {"code": "pt-BR", "name": "Português (Brasil)"},
    {"code": "en-US", "name": "English (United States)"},
    {"code": "la", "name": "Latin"},
]

TESTAMENTS_DATA = [
    {"id": 1, "name": "Antigo Testamento", "code": "OLD"},
    {"id": 2, "name": "Novo Testamento", "code": "NEW"},
    {"id": 3, "name": "Apócrifo/Deuterocanônico", "code": "APO"},
]


class Command(BaseCommand):
    help = "Populates the database with foundational metadata: Languages, Testaments, Canonical Books, and Book Names."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting metadata seeding..."))

        self._seed_languages()
        self._seed_testaments()
        self._seed_books_and_names()

        self.stdout.write(self.style.SUCCESS("Metadata seeding completed successfully!"))

    def _seed_languages(self):
        self.stdout.write("Seeding languages...")
        for lang_data in LANGUAGES_DATA:
            Language.objects.get_or_create(code=lang_data["code"], defaults={"name": lang_data["name"]})
        self.stdout.write(self.style.SUCCESS("Languages seeded."))

    def _seed_testaments(self):
        self.stdout.write("Seeding testaments...")
        for testament_data in TESTAMENTS_DATA:
            Testament.objects.get_or_create(id=testament_data["id"], defaults={"name": testament_data["name"]})
        self.stdout.write(self.style.SUCCESS("Testaments seeded."))

    def _seed_books_and_names(self):
        self.stdout.write("Seeding canonical books and book names...")

        # Cache testaments and languages to avoid repeated DB queries
        testament_codes = {
            "OLD": Testament.objects.get(id=1),  # Antigo Testamento
            "NEW": Testament.objects.get(id=2),  # Novo Testamento
            "APO": Testament.objects.get(id=3),  # Apócrifo/Deuterocanônico
        }
        languages = {lang.code: lang for lang in Language.objects.all()}

        for book_meta in BOOKS_METADATA:
            testament_obj = testament_codes.get(book_meta["testament_code"])
            if not testament_obj:
                self.stdout.write(
                    self.style.WARNING(
                        f"Testament code '{book_meta['testament_code']}' not found. Skipping book '{book_meta['osis']}'"
                    )
                )
                continue

            # Create the canonical book
            canonical_book, created = CanonicalBook.objects.get_or_create(
                osis_code=book_meta["osis"],
                defaults={
                    "canonical_order": book_meta["order"],
                    "testament": testament_obj,
                    "is_deuterocanonical": book_meta["is_deuterocanonical"],
                    "chapter_count": book_meta["chapter_count"],
                },
            )

            # Create names for the book in different languages
            for name_data in book_meta.get("names", []):
                lang_obj = languages.get(name_data["lang_code"])
                if not lang_obj:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Language code '{name_data['lang_code']}' not found. Skipping name '{name_data['name']}'"
                        )
                    )
                    continue

                BookName.objects.get_or_create(
                    canonical_book=canonical_book,
                    language=lang_obj,
                    defaults={"name": name_data["name"], "abbreviation": name_data["abbrev"]},
                )

        self.stdout.write(self.style.SUCCESS("Canonical books and names seeded."))
