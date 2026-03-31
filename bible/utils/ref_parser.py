"""
Bible Reference Parser — normalizes any ref format to (osis_code, chapter, verse_start, verse_end).

Handles 340+ book name formats: EN full, EN abbreviated, PT full, PT abbreviated, codes.
Examples:
    "Genesis 3:1-15"       → ("Gen", 3, 1, 15)
    "Gn 3:1"              → ("Gen", 3, 1, 1)
    "1 Chronicles 11:29"  → ("1Chr", 11, 29, 29)
    "1 Chr. 11:29"        → ("1Chr", 11, 29, 29)
    "1Cr 11:29"           → ("1Chr", 11, 29, 29)
    "Êxodo 3:2"           → ("Exod", 3, 2, 2)
    "Ap 12:9"             → ("Rev", 12, 9, 9)
    "Mt 5:3-12"           → ("Matt", 5, 3, 12)
    "João 3:16"           → ("John", 3, 16, 16)
    "Isaías 7:18"         → ("Isa", 7, 18, 18)
"""

from __future__ import annotations

import re

# Comprehensive book name → OSIS code mapping
# Covers: English full, English abbreviated, Portuguese full, Portuguese abbreviated, common codes
BOOK_TO_OSIS: dict[str, str] = {
    # Genesis
    "genesis": "Gen", "gen": "Gen", "gen.": "Gen", "ge": "Gen", "gn": "Gen",
    "gênesis": "Gen",
    # Exodus
    "exodus": "Exod", "exod": "Exod", "ex": "Exod", "ex.": "Exod",
    "êxodo": "Exod", "êx": "Exod",
    # Leviticus
    "leviticus": "Lev", "lev": "Lev", "lev.": "Lev", "le": "Lev", "lv": "Lev",
    "levítico": "Lev",
    # Numbers
    "numbers": "Num", "num": "Num", "num.": "Num", "numb": "Num", "nu": "Num",
    "nu.": "Num", "nm": "Num", "números": "Num",
    # Deuteronomy
    "deuteronomy": "Deut", "deut": "Deut", "deut.": "Deut", "de": "Deut", "dt": "Deut",
    "deuteronômio": "Deut",
    # Joshua
    "joshua": "Josh", "josh": "Josh", "josh.": "Josh", "jos": "Josh", "js": "Josh",
    "josué": "Josh",
    # Judges
    "judges": "Judg", "judg": "Judg", "judg.": "Judg", "jud": "Judg", "jz": "Judg",
    "juízes": "Judg",
    # Ruth
    "ruth": "Ruth", "ru": "Ruth", "rt": "Ruth", "rute": "Ruth",
    # 1 Samuel
    "1 samuel": "1Sam", "1 sam.": "1Sam", "1sam": "1Sam", "1sam.": "1Sam",
    "1sa": "1Sam", "1sm": "1Sam", "1 sm": "1Sam",
    # 2 Samuel
    "2 samuel": "2Sam", "2 sam.": "2Sam", "2sam": "2Sam", "2sa": "2Sam", "2sm": "2Sam",
    "2 sm": "2Sam",
    # 1 Kings
    "1 kings": "1Kgs", "1ki": "1Kgs", "1kin": "1Kgs", "1 reis": "1Kgs", "1rs": "1Kgs",
    "1 rs": "1Kgs",
    # 2 Kings
    "2 kings": "2Kgs", "2ki": "2Kgs", "2kin": "2Kgs", "2 reis": "2Kgs", "2rs": "2Kgs",
    # 1 Chronicles
    "1 chronicles": "1Chr", "1 chr.": "1Chr", "1 chr": "1Chr", "1chr": "1Chr",
    "1ch": "1Chr", "1 crônicas": "1Chr", "1cr": "1Chr", "1 cr": "1Chr",
    # 2 Chronicles
    "2 chronicles": "2Chr", "2 chr.": "2Chr", "2 chr": "2Chr", "2chr": "2Chr",
    "2ch": "2Chr", "2 crônicas": "2Chr", "2cr": "2Chr", "2 cr": "2Chr",
    # Ezra
    "ezra": "Ezra", "ezra.": "Ezra", "ezr": "Ezra", "esdras": "Ezra",
    "1 esd.": "Ezra", "1 esdr.": "Ezra", "1esd": "Ezra", "esd": "Ezra", "ed": "Ezra",
    # Nehemiah
    "nehemiah": "Neh", "neh": "Neh", "neh.": "Neh", "ne": "Neh", "neemias": "Neh",
    # Esther
    "esther": "Esth", "esth": "Esth", "es": "Esth", "et": "Esth", "ester": "Esth",
    # Job
    "job": "Job", "job.": "Job", "jó": "Job",
    # Psalms
    "psalms": "Ps", "psalm": "Ps", "psal": "Ps", "ps": "Ps", "ps.": "Ps",
    "salmos": "Ps", "salmo": "Ps", "sl": "Ps",
    # Proverbs
    "proverbs": "Prov", "prov": "Prov", "prov.": "Prov", "pr": "Prov", "pv": "Prov",
    "provérbios": "Prov",
    # Ecclesiastes
    "ecclesiastes": "Eccl", "eccl": "Eccl", "eccl.": "Eccl", "ec": "Eccl",
    "eclesiastes": "Eccl",
    # Song of Solomon
    "song": "Song", "song of solomon": "Song", "cant.": "Song", "ct": "Song",
    "cantares de salomão": "Song", "cântico dos cânticos": "Song", "cantares": "Song",
    "so": "Song",
    # Isaiah
    "isaiah": "Isa", "isa": "Isa", "isa.": "Isa", "isai": "Isa", "is": "Isa",
    "isaías": "Isa",
    # Jeremiah
    "jeremiah": "Jer", "jer": "Jer", "jer.": "Jer", "jere": "Jer", "jr": "Jer",
    "jeremias": "Jer",
    # Lamentations
    "lamentations": "Lam", "lam.": "Lam", "lam": "Lam", "lm": "Lam",
    "lamentações": "Lam",
    # Ezekiel
    "ezekiel": "Ezek", "ezek": "Ezek", "ezek.": "Ezek", "eze": "Ezek", "ez": "Ezek",
    "ezequiel": "Ezek",
    # Daniel
    "daniel": "Dan", "dan": "Dan", "dan.": "Dan", "da": "Dan", "dn": "Dan",
    # Hosea
    "hosea": "Hos", "hos": "Hos", "hos.": "Hos", "ho": "Hos", "os": "Hos",
    "oséias": "Hos", "oseias": "Hos",
    # Joel
    "joel": "Joel", "jl": "Joel",
    # Amos
    "amos": "Amos", "am": "Amos", "amós": "Amos",
    # Obadiah
    "obadiah": "Obad", "ob": "Obad", "obadias": "Obad",
    # Jonah
    "jonah": "Jonah", "jon": "Jonah", "jonas": "Jonah", "jn": "Jonah",
    # Micah
    "micah": "Mic", "mic": "Mic", "mq": "Mic", "miquéias": "Mic",
    # Nahum
    "nahum": "Nah", "nah.": "Nah", "nah": "Nah", "na": "Nah", "naum": "Nah",
    # Habakkuk
    "habakkuk": "Hab", "hab": "Hab", "hab.": "Hab", "hc": "Hab", "habacuque": "Hab",
    # Zephaniah
    "zephaniah": "Zeph", "zeph.": "Zeph", "zep": "Zeph", "sf": "Zeph", "sofonias": "Zeph",
    # Haggai
    "haggai": "Hag", "hag.": "Hag", "hag": "Hag", "ag": "Hag", "ageu": "Hag",
    # Zechariah
    "zechariah": "Zech", "zech": "Zech", "zech.": "Zech", "zec": "Zech", "zc": "Zech",
    "zacarias": "Zech",
    # Malachi
    "malachi": "Mal", "mal": "Mal", "mal.": "Mal", "ml": "Mal", "malaquias": "Mal",
    # Matthew
    "matthew": "Matt", "matt": "Matt", "matt.": "Matt", "mt": "Matt",
    "mateus": "Matt",
    # Mark
    "mark": "Mark", "mr": "Mark", "mc": "Mark", "marcos": "Mark",
    # Luke
    "luke": "Luke", "lu": "Luke", "lc": "Luke", "lucas": "Luke",
    # John
    "john": "John", "john.": "John", "joh": "John", "jo": "John", "joão": "John",
    # Acts
    "acts": "Acts", "acts.": "Acts", "act": "Acts", "ac": "Acts", "at": "Acts",
    "atos": "Acts",
    # Romans
    "romans": "Rom", "rom": "Rom", "rom.": "Rom", "ro": "Rom", "rm": "Rom",
    "romanos": "Rom",
    # 1 Corinthians
    "1 corinthians": "1Cor", "1 cor.": "1Cor", "1co": "1Cor",
    "1 coríntios": "1Cor",
    # 2 Corinthians
    "2 corinthians": "2Cor", "2 cor.": "2Cor", "2co": "2Cor",
    "2 coríntios": "2Cor",
    # Galatians
    "galatians": "Gal", "gal.": "Gal", "gal": "Gal", "gl": "Gal", "gálatas": "Gal",
    # Ephesians
    "ephesians": "Eph", "eph.": "Eph", "eph": "Eph", "ef": "Eph", "efésios": "Eph",
    # Philippians
    "philippians": "Phil", "phil.": "Phil", "phil": "Phil", "php": "Phil",
    "fp": "Phil", "filipenses": "Phil",
    # Colossians
    "colossians": "Col", "col.": "Col", "col": "Col", "cl": "Col", "colossenses": "Col",
    # 1 Thessalonians
    "1 thessalonians": "1Thess", "1 thess.": "1Thess", "1thess.": "1Thess", "1ts": "1Thess",
    "1 tessalonicenses": "1Thess",
    # 2 Thessalonians
    "2 thessalonians": "2Thess", "2 thess.": "2Thess", "2ts": "2Thess",
    # 1 Timothy
    "1 timothy": "1Tim", "1 tim.": "1Tim", "1tm": "1Tim",
    # 2 Timothy
    "2 timothy": "2Tim", "2 tim.": "2Tim", "2tim": "2Tim", "2tm": "2Tim",
    # Titus
    "titus": "Titus", "tit": "Titus", "tt": "Titus",
    # Philemon
    "philemon": "Phlm", "phlm": "Phlm", "fm": "Phlm", "filemon": "Phlm",
    # Hebrews
    "hebrews": "Heb", "heb": "Heb", "heb.": "Heb", "hb": "Heb", "hebreus": "Heb",
    # James
    "james": "Jas", "jas": "Jas", "tg": "Jas", "tiago": "Jas",
    # 1 Peter
    "1 peter": "1Pet", "1 pet.": "1Pet", "1pet": "1Pet", "1pe": "1Pet",
    "1 pedro": "1Pet",
    # 2 Peter
    "2 peter": "2Pet", "2pe": "2Pet", "2 pedro": "2Pet",
    # 1 John
    "1 john": "1John", "1jo": "1John", "1 joão": "1John",
    # 2 John
    "2 john": "2John", "2jo": "2John",
    # 3 John
    "3 john": "3John", "3jo": "3John", "3joh": "3John",
    # Jude
    "jude": "Jude", "jd": "Jude", "judas": "Jude",
    # Revelation
    "revelation": "Rev", "rev": "Rev", "rev.": "Rev", "re": "Rev", "ap": "Rev",
    "apocalipse": "Rev",
    # Deuterocanonical (mapped to closest)
    "tobias": "Tob", "tob": "Tob", "tob.": "Tob", "tb": "Tob",
    "judith": "Jdt", "jt": "Jdt",
    "1 maccabees": "1Macc", "1 macc.": "1Macc", "1macc": "1Macc", "1ma": "1Macc", "1mc": "1Macc",
    "2 maccabees": "2Macc", "2 macc.": "2Macc", "2macc": "2Macc", "2macc.": "2Macc", "2mc": "2Macc",
    "2 macabeus": "2Macc",
    "wisdom": "Wis", "wisd.": "Wis", "sb": "Wis", "sabedoria": "Wis",
    "baruch": "Bar", "bar.": "Bar", "br": "Bar",
    "sirach": "Sir", "sir": "Sir", "eclesiástico": "Sir",
    "ecclus": "Sir", "ecclus.": "Sir", "eclo": "Sir",
    "eccles.": "Eccl",
    "2 esdras": "2Esd", "2 esd.": "2Esd",
    "1 enoque": "1En",
    "3 ma": "3Macc",
}


def parse_ref(ref: str) -> tuple[str | None, int | None, int | None, int | None]:
    """
    Parse a Bible reference string into (osis_code, chapter, verse_start, verse_end).

    Handles:
        "Genesis 3:1-15"      → ("Gen", 3, 1, 15)
        "Gn 3:1"              → ("Gen", 3, 1, 1)
        "1 Chr. 11:29"        → ("1Chr", 11, 29, 29)
        "Êxodo 3:2"           → ("Exod", 3, 2, 2)
        "Ap 12:9"             → ("Rev", 12, 9, 9)
        "Salmo 23"            → ("Ps", 23, None, None)  # chapter only
        "1 Samuel 16:6-10"    → ("1Sam", 16, 6, 10)

    Returns (None, None, None, None) if parsing fails.
    """
    if not ref or not ref.strip():
        return None, None, None, None

    ref = ref.strip()

    # Try multi-word book names first (e.g., "Cantares de Salomão 4:14", "Song of Solomon 2:1")
    multi_match = re.match(
        r'^(\d?\s*[A-Za-zÀ-ÿ.]+(?:\s+(?:de|dos|of|do)\s+[A-Za-zÀ-ÿ.]+)*\.?)\s+(\d+)(?:[:.]\s*(\d+)(?:\s*[-–]\s*(\d+))?)?',
        ref,
    )

    # Fallback: single-word book name
    single_match = re.match(
        r'^(\d?\s*[A-Za-zÀ-ÿ.]+\.?)\s+(\d+)(?:[:.]\s*(\d+)(?:\s*[-–]\s*(\d+))?)?',
        ref,
    )

    # Try multi-word first, then single-word
    match = None
    for m in [multi_match, single_match]:
        if not m:
            continue
        book_raw = m.group(1).strip().rstrip('.')
        book_key = book_raw.lower().rstrip('.')
        if book_key in BOOK_TO_OSIS or (book_key + '.') in BOOK_TO_OSIS:
            match = m
            break

    if not match:
        return None, None, None, None

    book_raw = match.group(1).strip().rstrip('.')
    chapter = int(match.group(2))
    verse_start = int(match.group(3)) if match.group(3) else None
    verse_end = int(match.group(4)) if match.group(4) else verse_start

    # Normalize book name
    book_key = book_raw.lower().rstrip('.')
    osis = BOOK_TO_OSIS.get(book_key)

    if not osis:
        osis = BOOK_TO_OSIS.get(book_key + '.')

    if not osis:
        return None, None, None, None

    return osis, chapter, verse_start, verse_end
