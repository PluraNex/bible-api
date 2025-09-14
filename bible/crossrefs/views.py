"""Views for cross-references domain."""
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.response import Response

from bible.references.services import resolve_book_by_alias
from bible.references.views import _parse_reference_string
from bible.utils import get_canonical_book_by_name
from common.openapi import get_error_responses

from ..models import CrossReference, Verse
from .serializers import CrossReferenceSerializer


class CrossReferencesByVerseView(generics.ListAPIView):
    serializer_class = CrossReferenceSerializer

    def get_queryset(self):
        from_book = None
        from_chapter = None
        from_verse = None

        verse_id = self.kwargs.get("verse_id")
        if verse_id is not None:
            v = Verse.objects.filter(pk=verse_id).select_related("book").first()
            if v:
                from_book = v.book
                from_chapter = v.chapter
                from_verse = v.number
        else:
            ref = self.request.query_params.get("ref", "").strip()
            if ref:
                parsed = _parse_reference_string(ref)
                if parsed["items"]:
                    entry = parsed["items"][0]
                    lang = getattr(self.request, "lang_code", "en")
                    book = resolve_book_by_alias(entry.get("book_raw"), lang) or None
                    if book is None:
                        try:
                            book = get_canonical_book_by_name(entry.get("book_raw"))
                        except Exception:
                            book = None
                    if book and entry.get("chapter") and entry.get("verse_start"):
                        from_book = book
                        from_chapter = entry["chapter"]
                        from_verse = entry["verse_start"]

        base = CrossReference.objects.select_related("from_book", "to_book").order_by(
            "from_book", "from_chapter", "from_verse"
        )
        if from_book and from_chapter and from_verse:
            return base.filter(from_book=from_book, from_chapter=from_chapter, from_verse=from_verse)
        return base

    @extend_schema(
        summary="List cross-references for a verse (by id or textual ref)",
        tags=["cross-references"],
        parameters=[OpenApiParameter(name="ref", description="Text reference (e.g., 'Jo 3:16')", required=False)],
        responses={200: CrossReferenceSerializer(many=True), **get_error_responses()},
        examples=[
            OpenApiExample(
                "For by textual ref",
                value={
                    "results": [
                        {
                            "from_book_code": "John",
                            "from_chapter": 3,
                            "from_verse": 16,
                            "to_book_code": "Isa",
                            "to_chapter": 53,
                            "to_verse_start": 5,
                            "to_verse_end": 5,
                            "source": "TSK",
                            "confidence": 0.9,
                        }
                    ]
                },
                response_only=True,
            )
        ],
    )
    def get(self, request, *args, **kwargs):
        qs = self.get_queryset()
        if not qs.exists():
            ref = request.query_params.get("ref")
            if ref:
                return Response(
                    {"detail": "Reference not found or invalid", "code": "not_found"}, status=status.HTTP_404_NOT_FOUND
                )
        return super().get(request, *args, **kwargs)


class CrossReferencesParallelsView(generics.ListAPIView):
    """Return parallel passages (Gospels) for a textual reference.

    Minimal implementation: filter CrossReference results for to_book within the four Gospels.
    """

    serializer_class = CrossReferenceSerializer

    GOSPELS = {"Matt", "Mark", "Luke", "John"}

    def get_queryset(self):
        ref = self.request.query_params.get("ref", "").strip()
        if not ref:
            return CrossReference.objects.none()

        parsed = _parse_reference_string(ref)
        if not parsed["items"]:
            return CrossReference.objects.none()
        entry = parsed["items"][0]
        lang = getattr(self.request, "lang_code", "en")
        book = resolve_book_by_alias(entry.get("book_raw"), lang) or None
        if book is None:
            try:
                book = get_canonical_book_by_name(entry.get("book_raw"))
            except Exception:
                book = None
        if not book or not entry.get("chapter") or not entry.get("verse_start"):
            return CrossReference.objects.none()

        base = (
            CrossReference.objects.filter(
                from_book=book, from_chapter=entry["chapter"], from_verse=entry["verse_start"]
            )
            .select_related("from_book", "to_book")
            .order_by("to_book__canonical_order", "to_chapter", "to_verse_start")
        )

        # Filter to Gospels by OSIS code; if DB uses different codes, this can be extended to canonical_order range 40-43
        qs = base.filter(to_book__osis_code__in=self.GOSPELS)
        return qs

    @extend_schema(
        summary="List parallel gospel passages for a reference",
        tags=["cross-references"],
        parameters=[OpenApiParameter(name="ref", description="Text reference (e.g., 'Matt 3:16')", required=True)],
        responses={200: CrossReferenceSerializer(many=True), **get_error_responses()},
        examples=[
            OpenApiExample(
                "Parallel passages",
                value={
                    "results": [
                        {
                            "from_book_code": "Matt",
                            "from_chapter": 3,
                            "from_verse": 16,
                            "to_book_code": "Mark",
                            "to_chapter": 1,
                            "to_verse_start": 9,
                            "to_verse_end": 11,
                            "source": "Harmony",
                            "confidence": 0.8,
                        }
                    ]
                },
                response_only=True,
            )
        ],
    )
    def get(self, request, *args, **kwargs):
        ref = request.query_params.get("ref", "").strip()
        if not ref:
            return Response({"detail": "Query parameter 'ref' is required", "code": "validation_error"}, status=400)
        qs = self.get_queryset()
        if not qs.exists():
            return Response({"detail": "No parallel passages found", "code": "not_found"}, status=404)
        return super().get(request, *args, **kwargs)


class CrossReferencesGroupedView(generics.ListAPIView):
    """Group cross-references by strength (confidence) for a textual reference.

    Strength buckets (by confidence):
    - very_strong: >= 0.85
    - strong:      >= 0.65
    - moderate:    >= 0.40
    - weak:        < 0.40
    """

    serializer_class = CrossReferenceSerializer

    BUCKETS = (
        ("very_strong", 0.85),
        ("strong", 0.65),
        ("moderate", 0.40),
        ("weak", 0.0),
    )

    def _resolve_from(self):
        ref = self.request.query_params.get("ref", "").strip()
        if not ref:
            return None, None, None
        parsed = _parse_reference_string(ref)
        if not parsed["items"]:
            return None, None, None
        entry = parsed["items"][0]
        lang = getattr(self.request, "lang_code", "en")
        book = resolve_book_by_alias(entry.get("book_raw"), lang) or None
        if book is None:
            try:
                book = get_canonical_book_by_name(entry.get("book_raw"))
            except Exception:
                book = None
        if not book or not entry.get("chapter") or not entry.get("verse_start"):
            return None, None, None
        return book, entry["chapter"], entry["verse_start"]

    @extend_schema(
        summary="Group cross-references by strength",
        tags=["cross-references"],
        parameters=[OpenApiParameter(name="ref", description="Text reference (e.g., 'Jo 3:16')", required=True)],
        responses={200: CrossReferenceSerializer(many=True), **get_error_responses()},
        examples=[
            OpenApiExample(
                "Grouped by confidence",
                value={
                    "input": "Jo 3:16",
                    "total": 4,
                    "by_source": {"TSK": 3, "OpenBible": 1},
                    "groups": [
                        {"strength": "very_strong", "count": 2, "items": []},
                        {"strength": "strong", "count": 1, "items": []},
                        {"strength": "moderate", "count": 1, "items": []},
                        {"strength": "weak", "count": 0, "items": []},
                    ],
                },
                response_only=True,
            )
        ],
    )
    def get(self, request, *args, **kwargs):
        book, chapter, verse = self._resolve_from()
        if not book:
            return Response(
                {
                    "detail": "Query parameter 'ref' is required and must include book/chapter/verse",
                    "code": "validation_error",
                },
                status=400,
            )

        base = (
            CrossReference.objects.filter(from_book=book, from_chapter=chapter, from_verse=verse)
            .select_related("from_book", "to_book")
            .order_by("-confidence", "-votes")
        )

        groups = {name: [] for name, _ in self.BUCKETS}
        by_source = {}
        total = 0

        for cr in base:
            total += 1
            by_source[cr.source or "unknown"] = by_source.get(cr.source or "unknown", 0) + 1
            strength = next((name for name, thr in self.BUCKETS if cr.confidence >= thr), "weak")
            groups[strength].append(cr)

        # Serialize groups
        data_groups = []
        serializer = CrossReferenceSerializer
        for name, _ in self.BUCKETS:
            items = serializer(groups[name], many=True).data if groups[name] else []
            data_groups.append({"strength": name, "count": len(items), "items": items})

        payload = {
            "input": request.query_params.get("ref"),
            "total": total,
            "by_source": by_source,
            "groups": data_groups,
        }
        return Response(payload, status=200)


class CrossReferencesByVerseDeprecatedView(generics.ListAPIView):
    """DEPRECATED: GET /api/v1/bible/cross-references/verse/<verse_id>/

    Use /api/v1/bible/cross-references/for/?ref=<textual_reference> instead.
    """

    serializer_class = CrossReferenceSerializer

    def get_queryset(self):
        verse_id = self.kwargs.get("verse_id")
        if verse_id is None:
            return CrossReference.objects.none()

        v = Verse.objects.filter(pk=verse_id).select_related("book").first()
        if not v:
            return CrossReference.objects.none()

        base = CrossReference.objects.select_related("from_book", "to_book").order_by(
            "from_book", "from_chapter", "from_verse"
        )
        return base.filter(from_book=v.book, from_chapter=v.chapter, from_verse=v.number)

    @extend_schema(
        deprecated=True,
        summary="[DEPRECATED] List cross-references for a verse by ID",
        description="This endpoint is deprecated. Use /for/?ref=<textual_reference> instead.",
        tags=["cross-references"],
        responses={200: CrossReferenceSerializer(many=True), **get_error_responses()},
    )
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        # Add deprecation headers
        response["Deprecation"] = "true"
        response["Sunset"] = "2025-03-31"
        response["Link"] = '</api/v1/bible/cross-references/for/>; rel="successor-version"'

        return response


class CrossReferencesByThemeView(generics.ListAPIView):
    """GET /api/v1/bible/cross-references/by-theme/<theme_id>/"""

    serializer_class = CrossReferenceSerializer

    def get_queryset(self):
        # TODO: Update this once theme relationships are properly implemented with new model
        return CrossReference.objects.select_related("from_book", "to_book").order_by(
            "from_book", "from_chapter", "from_verse"
        )

    @extend_schema(
        summary="List cross-references by theme",
        tags=["cross-references"],
        responses={
            200: CrossReferenceSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
