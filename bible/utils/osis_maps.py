"""
Shared OSIS code mappings used by multiple domains.

Maps 3-letter uppercase codes (used in research data, image tagger, cross-refs)
to the CanonicalBook.osis_code format stored in the database.

Usage:
    from bible.utils.osis_maps import CATALOG_TO_OSIS, parse_osis_ref
"""

# 3-letter research/tagger format → DB osis_code
CATALOG_TO_OSIS = {
    # OT
    "GEN": "Gen", "EXO": "Exod", "LEV": "Lev", "NUM": "Num", "DEU": "Deut",
    "JOS": "Josh", "JDG": "Judg", "RUT": "Ruth",
    "1SA": "1Sam", "2SA": "2Sam", "1KI": "1Kgs", "2KI": "2Kgs",
    "1CH": "1Chr", "2CH": "2Chr", "EZR": "Ezra", "NEH": "Neh", "EST": "Esth",
    "JOB": "Job", "PSA": "Ps", "PRO": "Prov", "ECC": "Eccl", "SNG": "Song",
    "ISA": "Isa", "JER": "Jer", "LAM": "Lam",
    "EZE": "Ezek", "EZK": "Ezek",  # both variants
    "DAN": "Dan", "HOS": "Hos",
    "JOL": "Joel", "JOE": "Joel",  # both variants
    "AMO": "Amos", "OBA": "Obad", "JON": "Jonah",
    "MIC": "Mic", "NAM": "Nah", "HAB": "Hab", "ZEP": "Zeph",
    "HAG": "Hag", "ZEC": "Zech", "MAL": "Mal",
    # NT
    "MAT": "Matt", "MRK": "Mark", "LUK": "Luke", "JHN": "John", "ACT": "Acts",
    "ROM": "Rom", "1CO": "1Cor", "2CO": "2Cor", "GAL": "Gal", "EPH": "Eph",
    "PHP": "Phil", "COL": "Col", "1TH": "1Thess", "2TH": "2Thess",
    "1TI": "1Tim", "2TI": "2Tim", "TIT": "Titus", "PHM": "Phlm",
    "HEB": "Heb", "JAS": "Jas", "1PE": "1Pet", "2PE": "2Pet",
    "1JN": "1John", "2JN": "2John", "3JN": "3John", "JUD": "Jude", "REV": "Rev",
}


def parse_osis_ref(ref: str) -> tuple[str | None, int | None, int | None, int | None]:
    """
    Parse an OSIS reference string into (osis_code, chapter, verse_start, verse_end).

    Handles:
        "REV.12.11"      → ("Rev", 12, 11, 11)
        "GEN.7.17-24"    → ("Gen", 7, 17, 24)
        "ACT.7.55-56"    → ("Acts", 7, 55, 56)
        "MAT.4.1"        → ("Matt", 4, 1, 1)

    Returns (None, None, None, None) if parsing fails.
    """
    try:
        parts = ref.strip().split(".")
        if len(parts) < 3:
            return None, None, None, None

        book_code = parts[0].upper()
        chapter = int(parts[1])
        verse_spec = parts[2]

        osis_code = CATALOG_TO_OSIS.get(book_code)
        if not osis_code:
            return None, None, None, None

        if "-" in verse_spec:
            vs_parts = verse_spec.split("-")
            verse_start = int(vs_parts[0])
            verse_end = int(vs_parts[1])
        else:
            verse_start = int(verse_spec)
            verse_end = verse_start

        return osis_code, chapter, verse_start, verse_end

    except (ValueError, IndexError):
        return None, None, None, None
