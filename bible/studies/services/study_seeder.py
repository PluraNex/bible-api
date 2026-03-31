"""
Study seeder — uses AI to transform validation README.md files into rich
narrative study documents.

Instead of mechanical regex parsing, the AI reads the full README as a
theologian would and composes a proper study article with the correct block
types from our schema.
"""

import json
import logging
import os
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

# Block types reference for the AI prompt
BLOCK_TYPES_SCHEMA = """
You must return a JSON object with these fields:
- title: string (study title in Portuguese)
- study_type: one of "event", "typology", "doctrine", "mystical", "character", "thematic", "devotional", "freeform"
- difficulty: one of "base", "medium", "medium_hard", "hard", "extreme"
- description: string (1-2 sentence summary for listings)
- blocks: array of block objects

Each block has: {"id": "<uuid>", "type": "<type>", "data": {<type-specific>}, "meta": {}}

BLOCK TYPES:

1. "heading" — Section title
   data: {"text": "...", "level": 1|2|3}

2. "paragraph" — Narrative text (author's voice, transitions, analysis)
   data: {"html": "<p>...</p>"}
   USE HTML tags: <p>, <strong>, <em>, <ul>, <li>

3. "verse_cite" — Biblical verse citation (blockquote style)
   data: {"ref": "Rm 11:17", "version": "ARA", "text": "full verse text...", "book_osis": "ROM", "score": 3}

4. "commentary_cite" — Quote from a commentator
   data: {"author_name": "Agostinho", "tradition": "Pai da Igreja", "century": "V", "is_saint": true, "verse_ref": "Jo 9:1", "content": "quote text...", "source": "catena"}

5. "crossref_network" — Network of cross-references for a key verse
   data: {"verse": "ROM.11.17", "connections": [{"to_ref": "JER.11.16", "votes": 5, "note": "..."}], "layout": "table"}

6. "entity_card" — Biblical entity (person, place, etc.)
   data: {"canonical_id": "PER:adao", "name": "Adao", "namespace": "PERSON", "description": "..."}

7. "symbol_card" — Biblical symbol with meanings
   data: {"canonical_id": "NAT:oliveira", "name": "Oliveira", "meanings": ["Israel como povo de Deus", "..."], "progressions": []}

8. "connection_map" — Visual diagram of verse relationships
   data: {"content": "ASCII art or mermaid diagram...", "format": "ascii"|"mermaid"}

9. "comparison_table" — Side-by-side comparison
   data: {"headers": ["Col1", "Col2"], "rows": [["cell", "cell"]], "caption": "..."}

10. "callout" — Highlighted insight or observation
    data: {"style": "insight"|"warning"|"question"|"patristic", "html": "<p>...</p>"}

11. "divider" — Section separator
    data: {"style": "line"|"ornament"|"space"}

12. "reference_table" — Table of key verses with scores
    data: {"refs": [{"ref": "Rm 11:17", "text": "...", "score": 3, "justification": "..."}]}
"""

SYSTEM_PROMPT = """You are a biblical scholar and editor who transforms raw validation data
into beautifully composed study articles in Portuguese (pt-BR).

Your task: Read the validation README and compose a NARRATIVE STUDY ARTICLE.
This is NOT a mechanical conversion — you are writing an article that a theology
student would want to read. The data from the README (verses, commentaries,
cross-references, connection maps) becomes part of your narrative.

CRITICAL RULES — DO NOT SKIP ANY DATA:
1. EVERY gold reference verse MUST appear as a "verse_cite" block with FULL text
2. EVERY patristic commentary (Catena) MUST appear as a "commentary_cite" block with FULL quote
3. EVERY CCEL commentary MUST appear as a "commentary_cite" block with FULL quote
4. ALL cross-reference tables MUST appear as "crossref_network" blocks with ALL connections
5. ASCII connection maps MUST be preserved VERBATIM as "connection_map" blocks
6. Comparison tables MUST be preserved as "comparison_table" blocks
7. Entities and symbols from gazetteers MUST appear as "entity_card" or "symbol_card" blocks

NARRATIVE GUIDELINES:
- Write in Portuguese (pt-BR), scholarly but accessible tone
- Start with an engaging introduction using the Contexto Teologico section
- Between data blocks, add paragraph blocks with YOUR narrative voice:
  transitions, analysis, connections between the data points
- Commentary quotes should be introduced with context ("Agostinho observa que...")
- Use headings (level 2) to organize into 4-6 sections
- End with a synthesis/conclusion
- Aim for 30-50 blocks total — this is a SUBSTANTIAL article

The study should feel like reading an article in a theological journal,
not like browsing a database. But ALL the scholarly evidence must be present.
"""


def _generate_blocks_with_ai(readme_content, model="gpt-4o-mini"):
    """
    Use AI to read the README and generate study blocks.

    Args:
        readme_content: Full text of the validation README.md
        model: OpenAI model to use

    Returns:
        dict with title, study_type, difficulty, description, blocks
    """
    import openai

    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    user_prompt = f"""Transform this validation README into a narrative biblical study article.

Return a JSON object following the block schema below.

{BLOCK_TYPES_SCHEMA}

IMPORTANT:
- Generate a UUID for each block's "id" field
- The blocks array should contain 15-40 blocks (a substantial article)
- Every verse_cite must have the full verse text preserved
- Every commentary_cite must have the full quote preserved
- Cross-reference data (votes, connections) must be preserved exactly
- ASCII connection maps must be preserved verbatim
- Comparison tables must be preserved

README CONTENT:
---
{readme_content}
---

Return ONLY valid JSON. No markdown, no code fences."""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=16000,
    )

    content = response.choices[0].message.content
    result = json.loads(content)

    # Ensure all blocks have IDs
    for block in result.get("blocks", []):
        if "id" not in block or not block["id"]:
            block["id"] = str(uuid.uuid4())
        if "meta" not in block:
            block["meta"] = {}

    return result


def parse_readme_with_ai(readme_path, model="gpt-4o-mini"):
    """
    Parse a validation README.md using AI to produce study blocks.

    Args:
        readme_path: Path to the README.md file
        model: OpenAI model to use

    Returns:
        dict with keys: title, study_type, difficulty, validation_id,
                        query, description, blocks
    """
    content = Path(readme_path).read_text(encoding="utf-8")

    # Extract validation_id from directory name
    validation_id = Path(readme_path).parent.name

    # Call AI
    result = _generate_blocks_with_ai(content, model=model)

    # Add validation_id
    result["validation_id"] = validation_id

    # Extract query from title if not present
    if "query" not in result:
        result["query"] = result.get("title", "")

    return result


# ---------------------------------------------------------------------------
# Fallback: simple metadata extraction (no AI, for --no-ai mode)
# ---------------------------------------------------------------------------

STUDY_TYPE_MAP = {
    "evento": "event",
    "event": "event",
    "typology": "typology",
    "tipologia": "typology",
    "doctrine": "doctrine",
    "doutrina": "doctrine",
    "mystical": "mystical",
    "character": "character",
    "thematic": "thematic",
    "devotional": "devotional",
    "sanctification": "thematic",
    "spiritual_warfare": "thematic",
    "contemplation": "mystical",
    "pastoral": "thematic",
    "teaching": "doctrine",
}

DIFFICULTY_MAP = {
    "base": "base",
    "baseline": "base",
    "medium": "medium",
    "med": "medium",
    "medium-hard": "medium_hard",
    "medium_hard": "medium_hard",
    "mh": "medium_hard",
    "hard": "hard",
    "extreme": "extreme",
    "ext": "extreme",
}


def extract_metadata_only(readme_path):
    """
    Extract just the metadata (title, type, difficulty) without AI.
    Used for --no-ai dry-run mode.
    """
    import re

    content = Path(readme_path).read_text(encoding="utf-8")
    validation_id = Path(readme_path).parent.name

    # Title from H1
    title_match = re.search(r'^#\s+.*?—\s*"(.+?)"', content, re.MULTILINE)
    title = title_match.group(1) if title_match else validation_id

    # Metadata table
    meta = {}
    for line in content.split("\n"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        parts = [p.strip().strip("*").strip() for p in line.split("|") if p.strip()]
        if len(parts) >= 2:
            key = parts[0].lower()
            val = parts[1].strip()
            if key in ("tipo", "type"):
                meta["type"] = val.lower()
            elif key in ("dificuldade", "difficulty"):
                meta["difficulty"] = val.lower()
            elif key in ("query",):
                meta["query"] = val

    return {
        "title": title,
        "study_type": STUDY_TYPE_MAP.get(meta.get("type", ""), "freeform"),
        "difficulty": DIFFICULTY_MAP.get(meta.get("difficulty", ""), ""),
        "validation_id": validation_id,
        "query": meta.get("query", title),
    }
