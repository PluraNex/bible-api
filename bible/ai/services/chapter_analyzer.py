"""
AI Chapter Analyzer — On-demand entity/symbol context analysis.

Reads all verses in a chapter, matches against known entities/symbols,
and creates/audits verse links using GPT-4o-mini structured output.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field

from django.db import transaction

from bible.ai.models import ChapterAnalysis
from bible.entities.models import CanonicalEntity, EntityAlias, EntityVerseLink
from bible.models import CanonicalBook, Verse, Version
from bible.symbols.models import BiblicalSymbol, SymbolOccurrence

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a biblical scholar analyzing a chapter to identify entities and symbols mentioned in each verse.

You will receive:
1. The full text of a Bible chapter (all verses)
2. A list of known biblical entities (people, places, concepts, etc.) with their canonical_ids
3. A list of known biblical symbols with their canonical_ids
4. Existing verse links that may need auditing

Your task for EACH verse:
- Identify which entities from the provided list are MENTIONED or REFERENCED in that verse
- Identify which symbols from the provided list are PRESENT (literally or figuratively)
- For each match, provide: canonical_id, relevance (0.0-1.0), mention_type, and a brief context note in Portuguese
- If you find an important biblical concept, person, place, object, or symbol that is NOT in the provided lists, SUGGEST a new entry to create

Rules for EXISTING entities/symbols:
- Use canonical_ids from the provided lists
- An entity is "mentioned" if it appears by name, title, pronoun, or is clearly the subject
- A symbol is "present" if the word appears literally OR the concept is figuratively invoked
- Be conservative: relevance < 0.5 means weak connection, skip those
- mention_type: "explicit" (named directly), "implicit" (referred to indirectly), "typological" (foreshadowing/type)
- Context notes should be 1 short sentence in Portuguese
- CRITICAL: For each match, include "match_words" — the EXACT words from the verse text that reference it (for inline highlighting).
  Examples:
  - Entity "Eva" in "E disse a mulher à serpente" → match_words: ["mulher"]
  - Entity "Deus" in "o SENHOR Deus tinha feito" → match_words: ["SENHOR", "Deus"]
  - Symbol "Nudez" in "conheceram que estavam nus" → match_words: ["nus"]
  - Symbol "Árvore do Conhecimento" in "daquela árvore" → match_words: ["árvore"]
  match_words must be EXACTLY as they appear in the verse text (same case, same accents).
  IMPORTANT: match_words should be the word that NAMES or REPRESENTS the entity/symbol, not adjectives or states.
  - WRONG: Entity "Eva" with match_words: ["nu"] — "nu" is a condition, not Eva's name
  - RIGHT: Entity "Eva" with match_words: ["mulher"] — "mulher" refers to Eva
  - RIGHT: Symbol "Nudez" with match_words: ["nus", "nu"] — these words represent nudity
  - WRONG: Entity "Deus" with match_words: ["bom"] — "bom" is an attribute, not Deus's name
- For symbols that have multiple meanings, include "active_meaning" — the meaning text that applies in THIS verse context.
  Choose from the provided meanings list. If NONE of the existing meanings fits the verse context, create a NEW meaning by setting "new_meaning": true.
  Example: Symbol "Figueira" has meanings: "Abundância e prosperidade", "Juízo sobre a esterilidade"
  In Gen 3:7 (folhas de figueira para cobrir nudez) → none fits → active_meaning: "Cobertura e vergonha", "new_meaning": true
  In Mt 21:19 (Jesus amaldiçoa a figueira) → active_meaning: "Juízo sobre a esterilidade"
  In Mq 4:4 (cada um debaixo da sua figueira) → active_meaning: "Abundância e prosperidade"

Rules for NEW entries (create_entities / create_symbols):
- Only suggest entries that are THEOLOGICALLY or NARRATIVELY significant
- Do NOT create entries for common words (water, land) if a symbol already exists
- Each new entry needs: name (Portuguese), namespace, description (Portuguese, 1-2 sentences)
- For entities, namespace must be: PERSON, DEITY, ANGEL, PLACE, CONCEPT, OBJECT, EVENT, GROUP, CREATURE, PLANT, RITUAL, LITERARY_WORK
- For symbols, namespace must be: NATURAL, OBJECT, ACTION, NUMBER, COLOR, PERSON_TYPE, PLANT
- Generate a canonical_id using the prefix:slug pattern (e.g., OBJ:fruto-proibido, PLN:arvore-do-conhecimento)

Respond with valid JSON only."""

USER_PROMPT_TEMPLATE = """Analyze this chapter:

Book: {book_name} (OSIS: {book_osis})
Chapter: {chapter}

VERSES:
{verses_text}

KNOWN ENTITIES (use ONLY these canonical_ids):
{entities_json}

KNOWN SYMBOLS (use ONLY these canonical_ids):
{symbols_json}

EXISTING VERSE LINKS TO AUDIT:
{existing_links_json}

Respond with JSON:
{{
  "verse_annotations": [
    {{
      "verse": 1,
      "entities": [
        {{"canonical_id": "...", "relevance": 0.9, "mention_type": "explicit", "context": "...", "match_words": ["word1", "word2"]}}
      ],
      "symbols": [
        {{"canonical_id": "...", "relevance": 0.8, "usage_type": "symbolic", "context": "...", "match_words": ["word1"], "active_meaning": "the meaning text", "new_meaning": false}}
      ]
    }}
  ],
  "create_entities": [
    {{
      "canonical_id": "OBJ:fruto-proibido",
      "name": "Fruto Proibido",
      "namespace": "OBJECT",
      "description": "O fruto da árvore do conhecimento do bem e do mal, proibido por Deus no jardim do Éden.",
      "verses": [3, 6]
    }}
  ],
  "create_symbols": [
    {{
      "canonical_id": "NAT:arvore-do-conhecimento",
      "name": "Árvore do Conhecimento",
      "namespace": "NATURAL",
      "description": "Árvore cujo fruto traria o conhecimento do bem e do mal, símbolo da tentação e da desobediência.",
      "literal_meaning": "Árvore plantada no jardim do Éden",
      "symbolic_meanings": ["Tentação", "Limite divino", "Conhecimento proibido"],
      "verses": [3, 6, 11, 17]
    }}
  ],
  "remove_links": [
    {{"verse": 1, "canonical_id": "...", "reason": "..."}}
  ]
}}

Only include verses that have at least one entity or symbol match. Skip empty verses.

IMPORTANT: Always look for opportunities to create new entries. Examples of what to create:
- Named objects: "fruto proibido", "árvore do conhecimento do bem e do mal", "arca de Noé"
- Named places not in the list: "jardim do Éden", "torre de Babel"
- Theological concepts mentioned: "pecado original", "maldição", "proto-evangelho"
- Important symbols: "nudez" (innocence/shame), "pó da terra" (mortality), "suor do rosto" (labor)
- Named events: "a Queda", "expulsão do Éden"
If the text mentions something thematically important that is NOT in the provided lists, CREATE IT."""


@dataclass
class AnalysisStats:
    links_created: int = 0
    links_removed: int = 0
    symbols_created: int = 0
    entities_found: int = 0
    symbols_found: int = 0
    new_entities_created: int = 0
    new_symbols_created: int = 0
    errors: list = field(default_factory=list)
    duration_seconds: float = 0.0


class ChapterAnalyzer:
    """On-demand AI analysis of a chapter for entity/symbol context."""

    def __init__(self, model: str = "gpt-4o-mini", version_code: str = "ACF"):
        self.model = model
        self.version_code = version_code

    def analyze_chapter(self, book_osis: str, chapter: int) -> AnalysisStats:
        """Analyze a chapter and create/audit verse links."""
        start = time.time()
        stats = AnalysisStats()

        try:
            book = CanonicalBook.objects.get(osis_code__iexact=book_osis)
        except CanonicalBook.DoesNotExist:
            stats.errors.append(f"Book {book_osis} not found")
            return stats

        # Check if already analyzed
        existing = ChapterAnalysis.objects.filter(book=book, chapter=chapter).first()
        if existing:
            logger.info(f"Chapter {book_osis} {chapter} already analyzed at {existing.analyzed_at}")
            return stats

        logger.info(f"Analyzing {book_osis} chapter {chapter}...")

        # Build context
        verses = self._get_verses(book, chapter)
        if not verses:
            stats.errors.append(f"No verses found for {book_osis} {chapter}")
            return stats

        entities = self._get_candidate_entities(book, chapter)
        symbols = self._get_all_symbols()
        existing_links = self._get_existing_links(book, chapter)
        commentaries = self._get_commentaries(book, chapter)

        # Build prompt
        prompt = self._build_prompt(book, chapter, verses, entities, symbols, existing_links, commentaries)

        # Call AI
        result = self._call_ai(prompt)
        if not result:
            stats.errors.append("AI call failed or returned empty")
            return stats

        # Apply to DB
        self._create_new_entries(result, stats)
        self._apply_annotations(book, chapter, verses, result, stats)
        self._apply_removals(book, chapter, result, stats)

        # Track
        ChapterAnalysis.objects.update_or_create(
            book=book, chapter=chapter,
            defaults={
                "model_used": self.model,
                "entities_found": stats.entities_found,
                "symbols_found": stats.symbols_found,
                "links_created": stats.links_created,
                "links_removed": stats.links_removed,
            },
        )

        stats.duration_seconds = time.time() - start
        logger.info(
            f"Analysis complete for {book_osis} {chapter}: "
            f"+{stats.links_created} links, -{stats.links_removed} removed, "
            f"{stats.entities_found} entities, {stats.symbols_found} symbols "
            f"({stats.duration_seconds:.1f}s)"
        )
        return stats

    def is_analyzed(self, book_osis: str, chapter: int) -> bool:
        return ChapterAnalysis.objects.filter(
            book__osis_code__iexact=book_osis, chapter=chapter
        ).exists()

    # ── Data gathering ────────────────────────────────

    def _get_verses(self, book: CanonicalBook, chapter: int) -> list[dict]:
        version = Version.objects.filter(code=self.version_code).first()
        if not version:
            return []

        verses = (
            Verse.objects
            .filter(book=book, version=version, chapter=chapter)
            .order_by("number")
            .values("id", "number", "text")
        )
        return list(verses)

    def _get_candidate_entities(self, book: CanonicalBook, chapter: int) -> list[dict]:
        """Get entities that are likely relevant to this chapter.

        Strategy: entities that already have verse links in this book,
        plus top entities by boost.
        """
        # Entities linked to this book
        linked_ids = (
            EntityVerseLink.objects
            .filter(verse__book=book)
            .values_list("entity_id", flat=True)
            .distinct()[:200]
        )

        # Top entities by boost (global)
        top_ids = (
            CanonicalEntity.objects
            .order_by("-boost")
            .values_list("id", flat=True)[:300]
        )

        all_ids = set(linked_ids) | set(top_ids)

        entities = (
            CanonicalEntity.objects
            .filter(id__in=all_ids)
            .exclude(description__startswith="[")
            .values("canonical_id", "primary_name", "namespace")
        )

        result = []
        for e in entities:
            aliases = list(
                EntityAlias.objects
                .filter(entity__canonical_id=e["canonical_id"])
                .values_list("name", flat=True)[:5]
            )
            result.append({
                "canonical_id": e["canonical_id"],
                "name": e["primary_name"],
                "namespace": e["namespace"],
                "aliases": aliases,
            })

        return result

    def _get_all_symbols(self) -> list[dict]:
        from bible.symbols.models import SymbolMeaning

        symbols = list(
            BiblicalSymbol.objects.all()
            .values("canonical_id", "primary_name", "namespace")
        )

        # Attach meanings to each symbol for contextual matching
        meaning_map = {}
        for m in SymbolMeaning.objects.all().values("symbol__canonical_id", "meaning"):
            cid = m["symbol__canonical_id"]
            if cid not in meaning_map:
                meaning_map[cid] = []
            meaning_map[cid].append(m["meaning"])

        for s in symbols:
            s["meanings"] = meaning_map.get(s["canonical_id"], [])[:5]

        return symbols

    def _get_existing_links(self, book: CanonicalBook, chapter: int) -> list[dict]:
        links = (
            EntityVerseLink.objects
            .filter(verse__book=book, verse__chapter=chapter)
            .select_related("entity")
            .values("verse__number", "entity__canonical_id", "relevance")
        )
        return [
            {"verse": l["verse__number"], "entity": l["entity__canonical_id"], "relevance": l["relevance"]}
            for l in links
        ]

    def _get_commentaries(self, book: CanonicalBook, chapter: int) -> list[dict]:
        """Get patristic commentaries for this chapter from the Catena/CCEL database."""
        from bible.commentaries.models import CommentaryEntry

        entries = (
            CommentaryEntry.objects
            .filter(book=book, chapter=chapter)
            .select_related("author")
            .order_by("verse_start")[:30]
        )

        result = []
        for entry in entries:
            author_name = entry.author.short_name if entry.author else "Unknown"
            result.append({
                "verse": entry.verse_start,
                "author": author_name,
                "text": entry.body_text[:300],
            })

        if result:
            logger.info(f"  Found {len(result)} commentaries for {book.osis_code} {chapter}")

        return result

    # ── Prompt building ───────────────────────────────

    def _build_prompt(self, book, chapter, verses, entities, symbols, existing_links, commentaries=None) -> str:
        verses_text = "\n".join(
            f"v{v['number']}: {v['text']}" for v in verses
        )

        # Compact entity list (name + aliases)
        entities_compact = []
        for e in entities[:150]:
            entry = f"{e['canonical_id']} | {e['name']} ({e['namespace']})"
            if e.get("aliases"):
                entry += f" | aliases: {', '.join(e['aliases'][:3])}"
            entities_compact.append(entry)

        symbols_compact = []
        for s in symbols[:100]:
            entry = f"{s['canonical_id']} | {s['primary_name']} ({s['namespace']})"
            meanings = s.get("meanings", [])
            if meanings:
                entry += f" | meanings: {', '.join(meanings[:5])}"
            symbols_compact.append(entry)

        existing_compact = [
            f"v{l['verse']}: {l['entity']} (rel={l['relevance']})"
            for l in existing_links[:50]
        ]

        # Patristic commentaries as scholarly context
        commentary_text = ""
        if commentaries:
            commentary_lines = []
            for c in commentaries[:20]:
                commentary_lines.append(f"v{c['verse']} ({c['author']}): {c['text'][:200]}")
            commentary_text = "\n\nSCHOLARLY COMMENTARIES (use as context for entity/symbol identification):\n" + "\n".join(commentary_lines)

        prompt = USER_PROMPT_TEMPLATE.format(
            book_name=book.osis_code,
            book_osis=book.osis_code,
            chapter=chapter,
            verses_text=verses_text,
            entities_json="\n".join(entities_compact),
            symbols_json="\n".join(symbols_compact),
            existing_links_json="\n".join(existing_compact) or "None",
        )

        if commentary_text:
            prompt += commentary_text

        return prompt

    # ── AI call ───────────────────────────────────────

    def _call_ai(self, user_prompt: str) -> dict | None:
        try:
            import openai
            client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=4000,
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            logger.error(f"AI call failed: {e}")
            return None

    # ── Create new entries ──────────────────────────────

    @transaction.atomic
    def _create_new_entries(self, result, stats):
        """Create new entities and symbols suggested by the AI."""
        from bible.entities.models import EntityNamespace, EntityStatus
        from bible.symbols.models import SymbolMeaning, SymbolNamespace, SymbolStatus

        # New entities
        for entry in result.get("create_entities", []):
            cid = entry.get("canonical_id", "")
            if not cid or CanonicalEntity.objects.filter(canonical_id=cid).exists():
                continue

            namespace = entry.get("namespace", "CONCEPT")
            entity = CanonicalEntity.objects.create(
                canonical_id=cid,
                namespace=namespace,
                primary_name=entry.get("name", ""),
                description=entry.get("description", ""),
                description_pt=entry.get("description", ""),
                status=EntityStatus.APPROVED,
                source_gazetteer="ai_chapter_analyzer",
                ai_enriched=True,
            )
            stats.new_entities_created += 1
            logger.info(f"  Created entity: {cid} ({entity.primary_name})")

        # New symbols
        for entry in result.get("create_symbols", []):
            cid = entry.get("canonical_id", "")
            if not cid or BiblicalSymbol.objects.filter(canonical_id=cid).exists():
                continue

            namespace = entry.get("namespace", "OBJECT")
            # Map namespace to model choices
            ns_map = {
                "NATURAL": "NATURAL", "OBJECT": "OBJECT", "ACTION": "ACTION",
                "NUMBER": "NUMBER", "COLOR": "COLOR", "PERSON_TYPE": "PERSON_TYPE",
                "PLANT": "PLANT",
            }
            model_ns = ns_map.get(namespace, "OBJECT")

            symbol = BiblicalSymbol.objects.create(
                canonical_id=cid,
                namespace=model_ns,
                primary_name=entry.get("name", ""),
                primary_name_pt=entry.get("name", ""),
                literal_meaning=entry.get("literal_meaning", ""),
                literal_meaning_pt=entry.get("literal_meaning", ""),
                description=entry.get("description", ""),
                description_pt=entry.get("description", ""),
                status=SymbolStatus.APPROVED,
                source_gazetteer="ai_chapter_analyzer",
            )

            # Create meanings
            for idx, meaning in enumerate(entry.get("symbolic_meanings", [])):
                SymbolMeaning.objects.create(
                    symbol=symbol,
                    meaning=meaning,
                    meaning_pt=meaning,
                    is_primary_meaning=(idx == 0),
                    frequency=1,
                )

            stats.new_symbols_created += 1
            logger.info(f"  Created symbol: {cid} ({symbol.primary_name})")

    # ── Apply results ─────────────────────────────────

    @transaction.atomic
    def _apply_annotations(self, book, chapter, verses, result, stats):
        """Create new EntityVerseLink and SymbolOccurrence from AI analysis."""
        version = Version.objects.filter(code=self.version_code).first()
        if not version:
            return

        # Build verse lookup: number → Verse object
        verse_objs = {
            v.number: v
            for v in Verse.objects.filter(book=book, version=version, chapter=chapter)
        }

        # Entity cache
        entity_cache = {
            e.canonical_id: e
            for e in CanonicalEntity.objects.filter(
                canonical_id__in=[
                    ann.get("canonical_id", "")
                    for va in result.get("verse_annotations", [])
                    for ann in va.get("entities", [])
                ]
            )
        }

        # Symbol cache
        symbol_cache = {
            s.canonical_id: s
            for s in BiblicalSymbol.objects.filter(
                canonical_id__in=[
                    ann.get("canonical_id", "")
                    for va in result.get("verse_annotations", [])
                    for ann in va.get("symbols", [])
                ]
            )
        }

        entity_ids_seen = set()
        symbol_ids_seen = set()

        for va in result.get("verse_annotations", []):
            verse_num = va.get("verse")
            verse_obj = verse_objs.get(verse_num)
            if not verse_obj:
                continue

            # Entities
            for ann in va.get("entities", []):
                cid = ann.get("canonical_id", "")
                entity = entity_cache.get(cid)
                if not entity:
                    continue

                relevance = ann.get("relevance", 0.5)
                if relevance < 0.5:
                    continue

                entity_ids_seen.add(cid)

                # Create or update
                EntityVerseLink.objects.update_or_create(
                    entity=entity,
                    verse=verse_obj,
                    defaults={
                        "mention_type": ann.get("mention_type", "explicit"),
                        "relevance": relevance,
                        "is_primary_subject": relevance >= 0.8,
                        "context_note": ann.get("context", ""),
                        "match_words": ann.get("match_words", []),
                    },
                )
                stats.links_created += 1

            # Symbols
            for ann in va.get("symbols", []):
                cid = ann.get("canonical_id", "")
                symbol = symbol_cache.get(cid)
                if not symbol:
                    continue

                relevance = ann.get("relevance", 0.5)
                if relevance < 0.5:
                    continue

                symbol_ids_seen.add(cid)

                # Find or create active meaning
                active_meaning_text = ann.get("active_meaning", "")
                is_new_meaning = ann.get("new_meaning", False)
                active_meaning_obj = None

                if active_meaning_text:
                    from bible.symbols.models import SymbolMeaning

                    if not is_new_meaning:
                        # Try to find existing meaning
                        active_meaning_obj = (
                            SymbolMeaning.objects
                            .filter(symbol=symbol, meaning__icontains=active_meaning_text[:50])
                            .first()
                        )

                    if not active_meaning_obj and active_meaning_text:
                        # Create new meaning (AI determined none fits this context)
                        active_meaning_obj = SymbolMeaning.objects.create(
                            symbol=symbol,
                            meaning=active_meaning_text,
                            meaning_pt=active_meaning_text,
                            is_primary_meaning=False,
                            frequency=1,
                        )
                        logger.info(f"  Created new meaning for {symbol.primary_name}: \"{active_meaning_text}\"")

                SymbolOccurrence.objects.update_or_create(
                    symbol=symbol,
                    verse=verse_obj,
                    defaults={
                        "usage_type": ann.get("usage_type", "symbolic"),
                        "context_note": ann.get("context", ""),
                        "match_words": ann.get("match_words", []),
                        "meaning": active_meaning_obj,
                    },
                )
                stats.symbols_created += 1

        stats.entities_found = len(entity_ids_seen)
        stats.symbols_found = len(symbol_ids_seen)

        # Link newly created entities to their verses
        for entry in result.get("create_entities", []):
            cid = entry.get("canonical_id", "")
            entity = CanonicalEntity.objects.filter(canonical_id=cid).first()
            if not entity:
                continue
            for v_num in entry.get("verses", []):
                verse_obj = verse_objs.get(v_num)
                if verse_obj:
                    EntityVerseLink.objects.update_or_create(
                        entity=entity, verse=verse_obj,
                        defaults={
                            "mention_type": "explicit",
                            "relevance": 0.9,
                            "is_primary_subject": False,
                            "context_note": entry.get("description", "")[:200],
                        },
                    )
                    stats.links_created += 1

        # Link newly created symbols to their verses
        for entry in result.get("create_symbols", []):
            cid = entry.get("canonical_id", "")
            symbol = BiblicalSymbol.objects.filter(canonical_id=cid).first()
            if not symbol:
                continue
            for v_num in entry.get("verses", []):
                verse_obj = verse_objs.get(v_num)
                if verse_obj:
                    SymbolOccurrence.objects.update_or_create(
                        symbol=symbol, verse=verse_obj,
                        defaults={
                            "usage_type": "symbolic",
                            "context_note": entry.get("description", "")[:200],
                        },
                    )
                    stats.symbols_created += 1

    @transaction.atomic
    def _apply_removals(self, book, chapter, result, stats):
        """Remove irrelevant verse links flagged by AI."""
        version = Version.objects.filter(code=self.version_code).first()
        if not version:
            return

        for removal in result.get("remove_links", []):
            verse_num = removal.get("verse")
            cid = removal.get("canonical_id", "")

            deleted = EntityVerseLink.objects.filter(
                entity__canonical_id=cid,
                verse__book=book,
                verse__chapter=chapter,
                verse__number=verse_num,
                verse__version=version,
            ).delete()[0]

            if deleted:
                stats.links_removed += deleted
                logger.info(f"  Removed link: v{verse_num} ← {cid} ({removal.get('reason', '')})")
