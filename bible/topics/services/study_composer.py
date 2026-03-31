"""
Study Composer Service — Composes a rich study payload from multiple data sources.

Takes a Topic slug and assembles:
- Topic metadata (title, type, reference)
- Gold references (anchor verses with relevance scores)
- Cross-reference connections grouped by role (prophecy, narrative, fulfillment)
- Commentary voices from patristic and historical authors
- Related themes with progression data
- Entities and symbols mentioned in the topic's verses
"""

from __future__ import annotations

import logging
from typing import Any

from django.db.models import Prefetch, Q

from bible.commentaries import Author, CommentaryEntry
from bible.entities.models import CanonicalEntity, VerseMention as EntityVerseMention
from bible.models import (
    Topic,
    TopicAspect,
    TopicCrossReference,
    TopicDefinition,
    TopicThemeLink,
)
from bible.symbols.models import BiblicalSymbol, SymbolOccurrence

logger = logging.getLogger(__name__)


class StudyComposer:
    """Composes a unified study payload for a given topic."""

    def __init__(self, topic: Topic, lang_code: str = "pt"):
        self.topic = topic
        self.lang_code = lang_code

    def compose(self) -> dict[str, Any]:
        """Build the full study payload."""
        return {
            "meta": self._build_meta(),
            "gold_references": self._build_gold_references(),
            "connections": self._build_connections(),
            "commentaries": self._build_commentaries(),
            "aspects": self._build_aspects(),
            "themes": self._build_themes(),
            "entities": self._build_entities(),
            "symbols": self._build_symbols(),
            "related_topics": self._build_related(),
        }

    def _build_meta(self) -> dict:
        """Topic metadata."""
        topic = self.topic
        display_name = topic.get_display_name(self.lang_code)

        # Get content/outline if available
        content = topic.contents.filter(
            language__code__startswith=self.lang_code[:2]
        ).first()
        outline = content.outline if content else ""

        return {
            "slug": topic.slug,
            "title": display_name,
            "canonical_name": topic.canonical_name,
            "type": topic.topic_type,
            "total_verses": topic.total_verses,
            "ot_refs": topic.ot_refs,
            "nt_refs": topic.nt_refs,
            "books_count": topic.books_count,
            "sources": topic.available_sources,
            "ai_enriched": topic.ai_enriched,
            "outline": outline,
        }

    def _build_gold_references(self) -> list[dict]:
        """
        Anchor verses from themes, ordered by relevance.
        These are the 'gold references' — the most important verses for this topic.
        """
        anchor_verses = []
        seen_refs = set()

        for link in self.topic.theme_links.all().order_by("-relevance_score"):
            label = (
                link.label_original
                if self.lang_code.startswith("pt")
                else link.label_en
            ) or link.label_normalized

            for verse_ref in link.anchor_verses:
                if verse_ref not in seen_refs:
                    seen_refs.add(verse_ref)
                    anchor_verses.append({
                        "reference": verse_ref,
                        "theme_label": label,
                        "relevance_score": link.relevance_score,
                    })

        return anchor_verses

    def _build_connections(self) -> dict:
        """
        Cross-references grouped by testament direction.
        Groups: ot_to_nt (prophecy→fulfillment), within_ot, within_nt, nt_to_ot.
        """
        cross_refs = (
            TopicCrossReference.objects.filter(topic=self.topic)
            .select_related(
                "cross_reference",
                "cross_reference__from_book",
                "cross_reference__to_book",
            )
            .order_by("-relevance_score")[:100]
        )

        groups = {
            "ot_to_nt": [],
            "within_ot": [],
            "within_nt": [],
            "nt_to_ot": [],
        }

        for tcr in cross_refs:
            xref = tcr.cross_reference
            if not xref:
                continue

            from_book = xref.from_book
            to_book = xref.to_book
            if not from_book or not to_book:
                continue

            entry = {
                "from_ref": f"{from_book.name} {xref.from_chapter}:{xref.from_verse}",
                "to_ref": f"{to_book.name} {xref.to_chapter}:{xref.to_verse}",
                "from_book_osis": from_book.osis_code,
                "to_book_osis": to_book.osis_code,
                "votes": xref.votes,
                "confidence": xref.confidence,
                "strength": xref.strength,
                "relevance_score": tcr.relevance_score,
                "sources": xref.sources if hasattr(xref, "sources") else [],
            }

            from_ot = from_book.testament == "OT"
            to_ot = to_book.testament == "OT"

            if from_ot and not to_ot:
                groups["ot_to_nt"].append(entry)
            elif from_ot and to_ot:
                groups["within_ot"].append(entry)
            elif not from_ot and not to_ot:
                groups["within_nt"].append(entry)
            else:
                groups["nt_to_ot"].append(entry)

        return {
            "total": sum(len(v) for v in groups.values()),
            "groups": groups,
        }

    def _build_commentaries(self) -> list[dict]:
        """
        Commentary entries from patristic and historical authors.
        Fetches commentaries for verses referenced by this topic.
        """
        # Get book OSIS codes and chapters from cross-references
        verse_filters = self._get_topic_verse_filters()
        if not verse_filters:
            return []

        entries = (
            CommentaryEntry.objects.filter(verse_filters)
            .select_related("author", "source", "book")
            .order_by("author__birth_year", "book__order", "chapter", "verse_start")[:50]
        )

        result = []
        for entry in entries:
            author = entry.author
            result.append({
                "author_name": author.name if author else "Unknown",
                "author_short": author.short_name if author else "",
                "author_type": author.author_type if author else "",
                "tradition": author.tradition if author else "",
                "century": self._year_to_century(author.birth_year) if author and author.birth_year else "",
                "is_saint": author.is_saint if author else False,
                "verse_ref": f"{entry.book.name} {entry.chapter}:{entry.verse_start}" if entry.book else "",
                "book_osis": entry.book.osis_code if entry.book else "",
                "content": entry.content[:500] if entry.content else "",
                "content_full": entry.content or "",
                "source": entry.source.name if entry.source else "",
            })

        return result

    def _build_aspects(self) -> list[dict]:
        """Topic aspects/subdivisions with verse references."""
        aspects = (
            TopicAspect.objects.filter(topic=self.topic)
            .prefetch_related("labels", "labels__language")
            .order_by("order")
        )

        result = []
        for aspect in aspects:
            label = None
            for lbl in aspect.labels.all():
                if lbl.language.code.startswith(self.lang_code[:2]):
                    label = lbl.label
                    break
            if not label:
                label = aspect.labels.first()
                label = label.label if label else aspect.aspect_key

            result.append({
                "key": aspect.aspect_key,
                "label": label,
                "order": aspect.order,
                "verse_count": aspect.verse_count,
                "verse_refs": aspect.verse_refs[:20] if aspect.verse_refs else [],
            })

        return result

    def _build_themes(self) -> list[dict]:
        """Themes linked to this topic with anchor verses and relevance."""
        links = (
            self.topic.theme_links.all()
            .select_related("theme")
            .order_by("-relevance_score")[:20]
        )

        result = []
        for link in links:
            theme = link.theme
            label = (
                link.label_original
                if self.lang_code.startswith("pt")
                else link.label_en
            ) or link.label_normalized

            result.append({
                "theme_id": theme.id if theme else None,
                "label": label,
                "relevance_score": link.relevance_score,
                "anchor_verses": link.anchor_verses[:10] if link.anchor_verses else [],
                "grade": link.grade,
            })

        return result

    def _build_entities(self) -> list[dict]:
        """Entities mentioned in the topic's key verses."""
        # Get OSIS codes from the topic's cross-references
        books = self._get_topic_books()
        if not books:
            return []

        entities = (
            CanonicalEntity.objects.filter(
                verse_mentions__book_osis__in=books
            )
            .distinct()[:30]
        )

        return [
            {
                "canonical_id": e.canonical_id,
                "name": e.name,
                "namespace": e.namespace,
                "description": (e.description or "")[:200],
            }
            for e in entities
        ]

    def _build_symbols(self) -> list[dict]:
        """Symbols found in the topic's key verses."""
        books = self._get_topic_books()
        if not books:
            return []

        symbols = (
            BiblicalSymbol.objects.filter(
                occurrences__book_osis__in=books
            )
            .distinct()[:20]
        )

        return [
            {
                "canonical_id": s.canonical_id,
                "name": s.name,
                "name_pt": s.name_pt or s.name,
                "literal_meaning": s.literal_meaning or "",
                "namespace": s.namespace,
            }
            for s in symbols
        ]

    def _build_related(self) -> list[dict]:
        """Related topics for further exploration."""
        relations = (
            self.topic.outgoing_relations.all()
            .select_related("target")
            .prefetch_related("target__names", "target__names__language")[:10]
        )

        return [
            {
                "slug": rel.target.slug,
                "name": rel.target.get_display_name(self.lang_code),
                "type": rel.target.topic_type,
                "relation": rel.relation_type,
            }
            for rel in relations
        ]

    # === Helpers ===

    def _get_topic_books(self) -> list[str]:
        """Get distinct OSIS book codes from topic's cross-references."""
        xrefs = TopicCrossReference.objects.filter(
            topic=self.topic
        ).select_related("cross_reference__from_book")[:50]

        books = set()
        for tcr in xrefs:
            if tcr.cross_reference and tcr.cross_reference.from_book:
                books.add(tcr.cross_reference.from_book.osis_code)
            if tcr.cross_reference and tcr.cross_reference.to_book:
                books.add(tcr.cross_reference.to_book.osis_code)
        return list(books)

    def _get_topic_verse_filters(self) -> Q | None:
        """Build Q filter for commentary lookup based on topic's verse references."""
        xrefs = TopicCrossReference.objects.filter(
            topic=self.topic
        ).select_related(
            "cross_reference__from_book", "cross_reference__to_book"
        )[:30]

        filters = Q()
        seen = set()
        for tcr in xrefs:
            xref = tcr.cross_reference
            if not xref:
                continue

            # From verse
            if xref.from_book:
                key = (xref.from_book.osis_code, xref.from_chapter, xref.from_verse)
                if key not in seen:
                    seen.add(key)
                    filters |= Q(
                        book__osis_code=xref.from_book.osis_code,
                        chapter=xref.from_chapter,
                        verse_start=xref.from_verse,
                    )

            # To verse
            if xref.to_book:
                key = (xref.to_book.osis_code, xref.to_chapter, xref.to_verse)
                if key not in seen:
                    seen.add(key)
                    filters |= Q(
                        book__osis_code=xref.to_book.osis_code,
                        chapter=xref.to_chapter,
                        verse_start=xref.to_verse,
                    )

        return filters if seen else None

    @staticmethod
    def _year_to_century(year: int) -> str:
        """Convert birth year to century string (e.g., 354 → 'IV')."""
        if not year:
            return ""
        century = (abs(year) - 1) // 100 + 1
        roman = {
            1: "I", 2: "II", 3: "III", 4: "IV", 5: "V",
            6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X",
            11: "XI", 12: "XII", 13: "XIII", 14: "XIV", 15: "XV",
            16: "XVI", 17: "XVII", 18: "XVIII", 19: "XIX", 20: "XX",
        }
        suffix = " a.C." if year < 0 else ""
        return f"{roman.get(century, str(century))}{suffix}"
