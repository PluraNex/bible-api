"""
Claude Chapter Analyzer — Theological AI analysis with scholarly context.

Uses Claude (Anthropic SDK) with:
- Patristic commentaries from Catena Bible DB
- CCEL paragraphs (2.2M scholarly texts)
- Cross-references for intertextual context
- Symbol meanings for active_meaning selection
- Extended thinking for complex chapters

Tiers: haiku (fast/$0.001), sonnet (standard/$0.02), opus (deep/$0.36)
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field

from django.db import transaction

from bible.ai.models import ChapterAnalysis
from bible.ai.services.ccel_search import CCELSearch
from bible.entities.models import CanonicalEntity, EntityAlias, EntityVerseLink
from bible.models import CanonicalBook, Verse, Version
from bible.symbols.models import BiblicalSymbol, SymbolMeaning, SymbolOccurrence

logger = logging.getLogger(__name__)

MODEL_MAP = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6-20250514",
    "opus": "claude-opus-4-6-20250514",
}

SYSTEM_PROMPT = """Você é um teólogo erudito, ecumênico, com profundo conhecimento das Escrituras Hebraicas, Novo Testamento, patrística, e hermenêutica bíblica.

Sua tarefa: analisar um capítulo bíblico verso a verso, identificando:
1. ENTIDADES mencionadas (pessoas, lugares, conceitos, objetos, eventos)
2. SÍMBOLOS presentes (literal ou figurativamente)
3. Match words — as PALAVRAS EXATAS do texto que referenciam cada entidade/símbolo
4. Active meaning — qual significado do símbolo se aplica NESTE verso específico

REGRAS CRÍTICAS:

Para ENTIDADES existentes:
- Use APENAS canonical_ids da lista fornecida
- mention_type: "explicit" (nomeado), "implicit" (referido indiretamente), "typological" (tipo/sombra)
- match_words devem ser EXATAMENTE como aparecem no texto (mesmo caso, mesmos acentos)
- match_words são as palavras que NOMEIAM a entidade, NÃO adjetivos ou estados
  ERRADO: Entity "Eva" com match_words: ["nu"] — "nu" é condição, não nome
  CERTO: Entity "Eva" com match_words: ["mulher"] — "mulher" refere-se a Eva
  CERTO: Symbol "Nudez" com match_words: ["nus", "nu"] — representam nudez

Para SÍMBOLOS existentes:
- Escolha active_meaning da lista de meanings fornecida
- Se NENHUM meaning existente se encaixa, crie um novo com "new_meaning": true
- active_meaning deve ser o significado que se aplica NESTE contexto específico

Para NOVAS entidades/símbolos (create_entities / create_symbols):
- Crie apenas para conceitos TEOLOGICAMENTE SIGNIFICATIVOS não catalogados
- Exemplos: "Fruto Proibido", "Árvore do Conhecimento", "Proto-evangelho"
- NÃO crie para palavras comuns se já existe um símbolo equivalente

Use os COMENTÁRIOS PATRÍSTICOS fornecidos como respaldo acadêmico para suas decisões.

PRIMEIRO: Escreva uma breve análise teológica do capítulo (2-3 frases).
DEPOIS: Produza o JSON de anotações.

Responda em JSON válido. Todos os textos em Português Brasileiro."""

USER_PROMPT_TEMPLATE = """Analise este capítulo:

Livro: {book_name} (OSIS: {book_osis})
Capítulo: {chapter}

VERSÍCULOS:
{verses_text}

ENTIDADES CONHECIDAS (use APENAS estes canonical_ids):
{entities_json}

SÍMBOLOS CONHECIDOS (com meanings disponíveis):
{symbols_json}

LINKS EXISTENTES PARA AUDITAR:
{existing_links_json}

{commentaries_section}

{ccel_section}

Responda com JSON:
{{
  "theological_analysis": "Breve análise teológica do capítulo (2-3 frases em PT-BR)",
  "verse_annotations": [
    {{
      "verse": 1,
      "entities": [
        {{"canonical_id": "...", "relevance": 0.9, "mention_type": "explicit", "context": "...", "match_words": ["palavra1", "palavra2"]}}
      ],
      "symbols": [
        {{"canonical_id": "...", "relevance": 0.8, "usage_type": "symbolic", "context": "...", "match_words": ["palavra1"], "active_meaning": "significado que se aplica aqui", "new_meaning": false}}
      ]
    }}
  ],
  "create_entities": [
    {{"canonical_id": "NAMESPACE:slug", "name": "Nome em PT", "namespace": "NAMESPACE", "description": "Descrição em PT", "verses": [3, 6]}}
  ],
  "create_symbols": [
    {{"canonical_id": "NAMESPACE:slug", "name": "Nome em PT", "namespace": "NAMESPACE", "description": "Descrição em PT", "literal_meaning": "...", "symbolic_meanings": ["Significado 1", "Significado 2"], "verses": [3, 6]}}
  ],
  "remove_links": [
    {{"verse": 1, "canonical_id": "...", "reason": "..."}}
  ]
}}

Inclua apenas versos que tenham pelo menos uma entidade ou símbolo. Pule versos vazios.
Crie novas entidades/símbolos apenas para conceitos TEOLOGICAMENTE SIGNIFICATIVOS."""


@dataclass
class AnalysisStats:
    links_created: int = 0
    links_removed: int = 0
    symbols_created: int = 0
    entities_found: int = 0
    symbols_found: int = 0
    new_entities_created: int = 0
    new_symbols_created: int = 0
    new_meanings_created: int = 0
    ccel_paragraphs_used: int = 0
    commentaries_used: int = 0
    errors: list = field(default_factory=list)
    duration_seconds: float = 0.0


class ClaudeChapterAnalyzer:
    """AI chapter analysis using Claude with scholarly context."""

    def __init__(self, tier: str = "sonnet", version_code: str = "ACF"):
        self.tier = tier
        self.model = MODEL_MAP.get(tier, MODEL_MAP["sonnet"])
        self.version_code = version_code
        self.ccel_search = CCELSearch()

    def analyze_chapter(self, book_osis: str, chapter: int) -> AnalysisStats:
        start = time.time()
        stats = AnalysisStats()

        try:
            book = CanonicalBook.objects.get(osis_code__iexact=book_osis)
        except CanonicalBook.DoesNotExist:
            stats.errors.append(f"Book {book_osis} not found")
            return stats

        existing = ChapterAnalysis.objects.filter(book=book, chapter=chapter).first()
        if existing:
            logger.info(f"Chapter {book_osis} {chapter} already analyzed")
            return stats

        logger.info(f"Analyzing {book_osis} {chapter} with Claude ({self.tier})...")

        # 1. Gather context
        verses = self._get_verses(book, chapter)
        if not verses:
            stats.errors.append(f"No verses for {book_osis} {chapter}")
            return stats

        entities = self._get_candidate_entities(book, chapter)
        symbols = self._get_symbols_with_meanings()
        existing_links = self._get_existing_links(book, chapter)
        commentaries = self._get_commentaries(book, chapter)
        ccel = self._get_ccel_context(book_osis, chapter)

        stats.commentaries_used = len(commentaries)
        stats.ccel_paragraphs_used = len(ccel)

        # 2. Build prompt
        prompt = self._build_prompt(book, chapter, verses, entities, symbols, existing_links, commentaries, ccel)

        # 3. Call Claude
        result = self._call_claude(prompt)
        if not result:
            stats.errors.append("Claude call failed")
            return stats

        # Log theological analysis
        theological = result.get("theological_analysis", "")
        if theological:
            logger.info(f"  Theological: {theological[:150]}")

        # 4. Apply to DB (reuses patterns from chapter_analyzer.py)
        self._create_new_entries(result, stats)
        self._apply_annotations(book, chapter, verses, result, stats)
        self._apply_removals(book, chapter, result, stats)

        # 5. Track
        ChapterAnalysis.objects.update_or_create(
            book=book, chapter=chapter,
            defaults={
                "model_used": f"claude-{self.tier}",
                "entities_found": stats.entities_found,
                "symbols_found": stats.symbols_found,
                "links_created": stats.links_created,
                "links_removed": stats.links_removed,
            },
        )

        stats.duration_seconds = time.time() - start
        logger.info(
            f"Analysis complete: +{stats.links_created} links, -{stats.links_removed} removed, "
            f"{stats.entities_found} entities, {stats.symbols_found} symbols, "
            f"+{stats.new_entities_created} new entities, +{stats.new_symbols_created} new symbols, "
            f"+{stats.new_meanings_created} new meanings, "
            f"{stats.ccel_paragraphs_used} CCEL, {stats.commentaries_used} commentaries "
            f"({stats.duration_seconds:.1f}s)"
        )
        return stats

    def is_analyzed(self, book_osis: str, chapter: int) -> bool:
        return ChapterAnalysis.objects.filter(
            book__osis_code__iexact=book_osis, chapter=chapter
        ).exists()

    # ── Data gathering ────────────────────────────────

    def _get_verses(self, book, chapter):
        version = Version.objects.filter(code=self.version_code).first()
        if not version:
            return []
        return list(
            Verse.objects.filter(book=book, version=version, chapter=chapter)
            .order_by("number").values("id", "number", "text")
        )

    def _get_candidate_entities(self, book, chapter):
        linked_ids = (
            EntityVerseLink.objects.filter(verse__book=book)
            .values_list("entity_id", flat=True).distinct()[:200]
        )
        top_ids = (
            CanonicalEntity.objects.order_by("-boost")
            .values_list("id", flat=True)[:300]
        )
        all_ids = set(linked_ids) | set(top_ids)

        entities = CanonicalEntity.objects.filter(id__in=all_ids).exclude(
            description__startswith="["
        ).values("canonical_id", "primary_name", "namespace")

        result = []
        for e in entities:
            aliases = list(
                EntityAlias.objects.filter(entity__canonical_id=e["canonical_id"])
                .values_list("name", flat=True)[:5]
            )
            result.append({**e, "aliases": aliases})
        return result

    def _get_symbols_with_meanings(self):
        symbols = list(BiblicalSymbol.objects.all().values("canonical_id", "primary_name", "namespace"))
        meaning_map = {}
        for m in SymbolMeaning.objects.all().values("symbol__canonical_id", "meaning"):
            cid = m["symbol__canonical_id"]
            if cid not in meaning_map:
                meaning_map[cid] = []
            meaning_map[cid].append(m["meaning"])
        for s in symbols:
            s["meanings"] = meaning_map.get(s["canonical_id"], [])[:7]
        return symbols

    def _get_existing_links(self, book, chapter):
        return [
            {"verse": l["verse__number"], "entity": l["entity__canonical_id"], "relevance": l["relevance"]}
            for l in EntityVerseLink.objects.filter(
                verse__book=book, verse__chapter=chapter
            ).select_related("entity").values("verse__number", "entity__canonical_id", "relevance")
        ]

    def _get_commentaries(self, book, chapter):
        from bible.commentaries.models import CommentaryEntry
        entries = (
            CommentaryEntry.objects.filter(book=book, chapter=chapter)
            .select_related("author").order_by("verse_start")[:30]
        )
        result = []
        for entry in entries:
            result.append({
                "verse": entry.verse_start,
                "author": entry.author.short_name if entry.author else "Unknown",
                "text": entry.body_text[:300],
            })
        return result

    def _get_ccel_context(self, book_osis, chapter):
        return self.ccel_search.search_by_chapter(book_osis, chapter, max_results=10)

    # ── Prompt building ───────────────────────────────

    def _build_prompt(self, book, chapter, verses, entities, symbols, existing_links, commentaries, ccel):
        verses_text = "\n".join(f"v{v['number']}: {v['text']}" for v in verses)

        entities_compact = []
        for e in entities[:150]:
            entry = f"{e['canonical_id']} | {e['primary_name']} ({e['namespace']})"
            if e.get("aliases"):
                entry += f" | aliases: {', '.join(e['aliases'][:3])}"
            entities_compact.append(entry)

        symbols_compact = []
        for s in symbols[:100]:
            entry = f"{s['canonical_id']} | {s['primary_name']} ({s['namespace']})"
            if s.get("meanings"):
                entry += f" | meanings: {', '.join(s['meanings'][:5])}"
            symbols_compact.append(entry)

        existing_compact = [
            f"v{l['verse']}: {l['entity']} (rel={l['relevance']})"
            for l in existing_links[:50]
        ]

        # Commentaries section
        commentaries_section = ""
        if commentaries:
            lines = [f"v{c['verse']} ({c['author']}): {c['text'][:200]}" for c in commentaries[:15]]
            commentaries_section = "COMENTÁRIOS PATRÍSTICOS (Catena Bible):\n" + "\n".join(lines)

        # CCEL section
        ccel_section = ""
        if ccel:
            lines = [f"({c['author']}, {c['title']}): {c['text'][:250]}" for c in ccel[:8]]
            ccel_section = "FONTES ACADÊMICAS (CCEL - Christian Classics Ethereal Library):\n" + "\n".join(lines)

        return USER_PROMPT_TEMPLATE.format(
            book_name=book.osis_code,
            book_osis=book.osis_code,
            chapter=chapter,
            verses_text=verses_text,
            entities_json="\n".join(entities_compact),
            symbols_json="\n".join(symbols_compact),
            existing_links_json="\n".join(existing_compact) or "Nenhum",
            commentaries_section=commentaries_section,
            ccel_section=ccel_section,
        )

    # ── Claude API call ───────────────────────────────

    def _call_claude(self, user_prompt: str) -> dict | None:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

            kwargs = {
                "model": self.model,
                "max_tokens": 8000,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_prompt}],
            }

            # Extended thinking for opus tier
            if self.tier == "opus":
                kwargs["thinking"] = {"type": "enabled", "budget_tokens": 4000}

            response = client.messages.create(**kwargs)

            # Extract text content
            content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content = block.text
                    break

            # Extract JSON from response (may have reasoning before JSON)
            json_start = content.find("{")
            if json_start == -1:
                logger.error("No JSON found in Claude response")
                return None

            json_text = content[json_start:]
            # Find matching closing brace
            depth = 0
            for i, c in enumerate(json_text):
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        json_text = json_text[: i + 1]
                        break

            return json.loads(json_text)

        except Exception as e:
            logger.error(f"Claude call failed: {e}")
            return None

    # ── Apply results (reused from chapter_analyzer.py) ──

    @transaction.atomic
    def _create_new_entries(self, result, stats):
        from bible.entities.models import EntityStatus
        from bible.symbols.models import SymbolStatus

        for entry in result.get("create_entities", []):
            cid = entry.get("canonical_id", "")
            if not cid or CanonicalEntity.objects.filter(canonical_id=cid).exists():
                continue
            CanonicalEntity.objects.create(
                canonical_id=cid,
                namespace=entry.get("namespace", "CONCEPT"),
                primary_name=entry.get("name", ""),
                description=entry.get("description", ""),
                description_pt=entry.get("description", ""),
                status=EntityStatus.APPROVED,
                source_gazetteer="ai_claude_analyzer",
                ai_enriched=True,
            )
            stats.new_entities_created += 1
            logger.info(f"  Created entity: {cid} ({entry.get('name', '')})")

        for entry in result.get("create_symbols", []):
            cid = entry.get("canonical_id", "")
            if not cid or BiblicalSymbol.objects.filter(canonical_id=cid).exists():
                continue
            ns_map = {"NATURAL": "NATURAL", "OBJECT": "OBJECT", "ACTION": "ACTION",
                      "NUMBER": "NUMBER", "COLOR": "COLOR", "PERSON_TYPE": "PERSON_TYPE", "PLANT": "PLANT"}
            symbol = BiblicalSymbol.objects.create(
                canonical_id=cid,
                namespace=ns_map.get(entry.get("namespace", "OBJECT"), "OBJECT"),
                primary_name=entry.get("name", ""),
                primary_name_pt=entry.get("name", ""),
                literal_meaning=entry.get("literal_meaning", ""),
                description=entry.get("description", ""),
                description_pt=entry.get("description", ""),
                status=SymbolStatus.APPROVED,
                source_gazetteer="ai_claude_analyzer",
            )
            for idx, meaning in enumerate(entry.get("symbolic_meanings", [])):
                SymbolMeaning.objects.create(
                    symbol=symbol, meaning=meaning, meaning_pt=meaning,
                    is_primary_meaning=(idx == 0), frequency=1,
                )
            stats.new_symbols_created += 1
            logger.info(f"  Created symbol: {cid} ({entry.get('name', '')})")

    @transaction.atomic
    def _apply_annotations(self, book, chapter, verses, result, stats):
        version = Version.objects.filter(code=self.version_code).first()
        if not version:
            return

        verse_objs = {
            v.number: v for v in Verse.objects.filter(book=book, version=version, chapter=chapter)
        }

        # Caches
        entity_cids = set()
        symbol_cids = set()
        for va in result.get("verse_annotations", []):
            for ann in va.get("entities", []):
                entity_cids.add(ann.get("canonical_id", ""))
            for ann in va.get("symbols", []):
                symbol_cids.add(ann.get("canonical_id", ""))

        entity_cache = {e.canonical_id: e for e in CanonicalEntity.objects.filter(canonical_id__in=entity_cids)}
        symbol_cache = {s.canonical_id: s for s in BiblicalSymbol.objects.filter(canonical_id__in=symbol_cids)}

        entity_ids_seen = set()
        symbol_ids_seen = set()

        for va in result.get("verse_annotations", []):
            verse_obj = verse_objs.get(va.get("verse"))
            if not verse_obj:
                continue

            for ann in va.get("entities", []):
                entity = entity_cache.get(ann.get("canonical_id", ""))
                if not entity or ann.get("relevance", 0) < 0.5:
                    continue
                entity_ids_seen.add(entity.canonical_id)
                EntityVerseLink.objects.update_or_create(
                    entity=entity, verse=verse_obj,
                    defaults={
                        "mention_type": ann.get("mention_type", "explicit"),
                        "relevance": ann.get("relevance", 0.5),
                        "is_primary_subject": ann.get("relevance", 0) >= 0.8,
                        "context_note": ann.get("context", ""),
                        "match_words": ann.get("match_words", []),
                    },
                )
                stats.links_created += 1

            for ann in va.get("symbols", []):
                symbol = symbol_cache.get(ann.get("canonical_id", ""))
                if not symbol or ann.get("relevance", 0) < 0.5:
                    continue
                symbol_ids_seen.add(symbol.canonical_id)

                # Find or create active meaning
                active_meaning_text = ann.get("active_meaning", "")
                is_new = ann.get("new_meaning", False)
                meaning_obj = None
                if active_meaning_text:
                    if not is_new:
                        meaning_obj = SymbolMeaning.objects.filter(
                            symbol=symbol, meaning__icontains=active_meaning_text[:50]
                        ).first()
                    if not meaning_obj:
                        meaning_obj = SymbolMeaning.objects.create(
                            symbol=symbol, meaning=active_meaning_text,
                            meaning_pt=active_meaning_text, is_primary_meaning=False, frequency=1,
                        )
                        stats.new_meanings_created += 1
                        logger.info(f"  New meaning for {symbol.primary_name}: \"{active_meaning_text}\"")

                SymbolOccurrence.objects.update_or_create(
                    symbol=symbol, verse=verse_obj,
                    defaults={
                        "usage_type": ann.get("usage_type", "symbolic"),
                        "context_note": ann.get("context", ""),
                        "match_words": ann.get("match_words", []),
                        "meaning": meaning_obj,
                    },
                )
                stats.symbols_created += 1

        stats.entities_found = len(entity_ids_seen)
        stats.symbols_found = len(symbol_ids_seen)

        # Link new entries to verses
        for entry in result.get("create_entities", []):
            entity = CanonicalEntity.objects.filter(canonical_id=entry.get("canonical_id", "")).first()
            if not entity:
                continue
            for v_num in entry.get("verses", []):
                verse_obj = verse_objs.get(v_num)
                if verse_obj:
                    EntityVerseLink.objects.update_or_create(
                        entity=entity, verse=verse_obj,
                        defaults={"mention_type": "explicit", "relevance": 0.9, "context_note": entry.get("description", "")[:200]},
                    )
                    stats.links_created += 1

        for entry in result.get("create_symbols", []):
            symbol = BiblicalSymbol.objects.filter(canonical_id=entry.get("canonical_id", "")).first()
            if not symbol:
                continue
            for v_num in entry.get("verses", []):
                verse_obj = verse_objs.get(v_num)
                if verse_obj:
                    SymbolOccurrence.objects.update_or_create(
                        symbol=symbol, verse=verse_obj,
                        defaults={"usage_type": "symbolic", "context_note": entry.get("description", "")[:200]},
                    )
                    stats.symbols_created += 1

    @transaction.atomic
    def _apply_removals(self, book, chapter, result, stats):
        version = Version.objects.filter(code=self.version_code).first()
        if not version:
            return
        for removal in result.get("remove_links", []):
            deleted = EntityVerseLink.objects.filter(
                entity__canonical_id=removal.get("canonical_id", ""),
                verse__book=book, verse__chapter=chapter,
                verse__number=removal.get("verse"),
                verse__version=version,
            ).delete()[0]
            if deleted:
                stats.links_removed += deleted
