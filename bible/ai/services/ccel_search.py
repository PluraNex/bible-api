"""
CCEL Search — Find relevant patristic paragraphs from CCEL parquet files.

Searches 2.2M paragraphs across 20 parquet files using biblical reference matching.
Returns scholarly commentary excerpts for AI context enrichment.
"""

from __future__ import annotations

import logging
import os
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)

CCEL_DATA_DIR = Path("E:/ccel-paragraphs/data")
INDEX_CACHE_PATH = Path("E:/ccel-paragraphs/ref_index.pkl")

# OSIS code → common ref formats used in CCEL
OSIS_TO_CCEL_REFS = {
    "Gen": ["Gen", "Genesis", "Gn"],
    "Exod": ["Ex", "Exod", "Exodus"],
    "Lev": ["Lev", "Leviticus"],
    "Num": ["Num", "Numbers"],
    "Deut": ["Deut", "Deuteronomy", "Dt"],
    "Josh": ["Josh", "Joshua"],
    "Judg": ["Judg", "Judges"],
    "Ruth": ["Ruth"],
    "1Sam": ["1 Sam", "1Sam", "1 Samuel"],
    "2Sam": ["2 Sam", "2Sam", "2 Samuel"],
    "1Kgs": ["1 Kings", "1Kgs", "1 Ki"],
    "2Kgs": ["2 Kings", "2Kgs", "2 Ki"],
    "1Chr": ["1 Chr", "1Chr", "1 Chronicles"],
    "2Chr": ["2 Chr", "2Chr", "2 Chronicles"],
    "Ezra": ["Ezra", "Ezr"],
    "Neh": ["Neh", "Nehemiah"],
    "Esth": ["Esth", "Esther"],
    "Job": ["Job"],
    "Ps": ["Ps", "Psalm", "Psalms"],
    "Prov": ["Prov", "Proverbs"],
    "Eccl": ["Eccl", "Ecclesiastes"],
    "Song": ["Song", "Cant"],
    "Isa": ["Isa", "Isaiah", "Is"],
    "Jer": ["Jer", "Jeremiah"],
    "Lam": ["Lam", "Lamentations"],
    "Ezek": ["Ezek", "Ezekiel", "Ez"],
    "Dan": ["Dan", "Daniel"],
    "Hos": ["Hos", "Hosea"],
    "Joel": ["Joel"],
    "Amos": ["Amos", "Am"],
    "Obad": ["Obad", "Obadiah"],
    "Jonah": ["Jonah", "Jon"],
    "Mic": ["Mic", "Micah"],
    "Nah": ["Nah", "Nahum"],
    "Hab": ["Hab", "Habakkuk"],
    "Zeph": ["Zeph", "Zephaniah"],
    "Hag": ["Hag", "Haggai"],
    "Zech": ["Zech", "Zechariah"],
    "Mal": ["Mal", "Malachi"],
    "Matt": ["Matt", "Matthew", "Mt"],
    "Mark": ["Mark", "Mk"],
    "Luke": ["Luke", "Lk"],
    "John": ["John", "Jn"],
    "Acts": ["Acts", "Ac"],
    "Rom": ["Rom", "Romans"],
    "1Cor": ["1 Cor", "1Cor", "1 Corinthians"],
    "2Cor": ["2 Cor", "2Cor", "2 Corinthians"],
    "Gal": ["Gal", "Galatians"],
    "Eph": ["Eph", "Ephesians"],
    "Phil": ["Phil", "Philippians"],
    "Col": ["Col", "Colossians"],
    "1Thess": ["1 Thess", "1Thess"],
    "2Thess": ["2 Thess", "2Thess"],
    "1Tim": ["1 Tim", "1Tim"],
    "2Tim": ["2 Tim", "2Tim"],
    "Titus": ["Titus", "Tit"],
    "Phlm": ["Phlm", "Philemon"],
    "Heb": ["Heb", "Hebrews"],
    "Jas": ["Jas", "James"],
    "1Pet": ["1 Pet", "1Pet", "1 Peter"],
    "2Pet": ["2 Pet", "2Pet", "2 Peter"],
    "1John": ["1 John", "1John", "1 Jn"],
    "2John": ["2 John", "2John"],
    "3John": ["3 John", "3John"],
    "Jude": ["Jude"],
    "Rev": ["Rev", "Revelation", "Apoc"],
}


class CCELSearch:
    """Search CCEL parquet files for scholarly commentary on Bible chapters."""

    def __init__(self, data_dir: str | Path | None = None):
        self.data_dir = Path(data_dir) if data_dir else CCEL_DATA_DIR

    def search_by_chapter(
        self, book_osis: str, chapter: int, max_results: int = 15
    ) -> list[dict]:
        """Find CCEL paragraphs that reference this chapter."""
        if not self.data_dir.exists():
            logger.warning(f"CCEL data dir not found: {self.data_dir}")
            return []

        ref_patterns = self._build_ref_patterns(book_osis, chapter)
        if not ref_patterns:
            return []

        results = []
        parquet_files = sorted(self.data_dir.glob("*.parquet"))

        for pf in parquet_files:
            try:
                import pyarrow.parquet as pq

                table = pq.read_table(pf, columns=["text", "refs", "author-short-form", "title"])
                df = table.to_pandas()

                # Filter rows where refs contain our chapter reference
                mask = df["refs"].apply(
                    lambda refs: self._refs_match(refs, ref_patterns) if isinstance(refs, list) else False
                )
                matching = df[mask]

                for _, row in matching.iterrows():
                    text = row.get("text", "")
                    if len(text) < 50:  # Skip very short paragraphs
                        continue
                    results.append({
                        "author": row.get("author-short-form", "Unknown"),
                        "title": str(row.get("title", ""))[:100],
                        "text": text[:500],
                    })

            except Exception as e:
                logger.warning(f"Error reading {pf}: {e}")
                continue

        # Sort by text length (longer = more substantive) and deduplicate
        results.sort(key=lambda r: len(r["text"]), reverse=True)

        # Deduplicate by first 100 chars
        seen = set()
        unique = []
        for r in results:
            key = r["text"][:100]
            if key not in seen:
                seen.add(key)
                unique.append(r)

        logger.info(f"CCEL search for {book_osis} {chapter}: {len(unique)} paragraphs found")
        return unique[:max_results]

    def _build_ref_patterns(self, book_osis: str, chapter: int) -> list[str]:
        """Build patterns to match in CCEL refs column."""
        book_names = OSIS_TO_CCEL_REFS.get(book_osis, [book_osis])
        patterns = []
        for name in book_names:
            # Match: "Gen 3:", "Gen 3.", "Gen. 3:", "Genesis 3:" etc.
            patterns.append(f"{name} {chapter}:")
            patterns.append(f"{name} {chapter}.")
            patterns.append(f"{name}. {chapter}:")
            patterns.append(f"{name}. {chapter}.")
            # Also match "[Gen 3:1]" format
            patterns.append(f"[{name} {chapter}:")
            patterns.append(f"[{name}. {chapter}:")
        return patterns

    @staticmethod
    def _refs_match(refs: list, patterns: list[str]) -> bool:
        """Check if any ref in the list matches any pattern."""
        for ref in refs:
            ref_str = str(ref)
            for pattern in patterns:
                if pattern in ref_str:
                    return True
        return False
