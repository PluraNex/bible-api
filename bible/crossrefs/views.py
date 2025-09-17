"""Views for cross-references domain."""
from django.db.models import Avg, Count, Exists, Max, Min, OuterRef
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import generics
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from bible.references.services import resolve_book_by_alias
from bible.references.views import _parse_reference_string
from bible.utils import get_canonical_book_by_name
from common.openapi import get_error_responses
from common.pagination import StandardResultsSetPagination

from ..models import CrossReference, Theme, Verse
from .serializers import CrossReferenceSerializer


class CrossReferencePagination(StandardResultsSetPagination):
    """Pagination with support for the `limit` alias."""

    limit_query_param = "limit"

    def get_page_size(self, request):
        limit = request.query_params.get(self.limit_query_param)
        if limit is not None and limit != "":
            try:
                value = int(limit)
            except (TypeError, ValueError) as exc:
                raise ValidationError({"limit": "Limit must be a positive integer."}) from exc
            if value <= 0:
                raise ValidationError({"limit": "Limit must be greater than zero."})
            return min(value, self.max_page_size)
        return super().get_page_size(request)


class CrossReferenceFiltersMixin:
    """Helpers to apply common query filters and expose them in responses."""

    def _apply_common_filters(self, queryset):
        self._applied_filters = {}

        source = self.request.query_params.get("source")
        if source:
            normalized = source.strip()
            if normalized:
                queryset = queryset.filter(source__iexact=normalized)
                self._applied_filters["source"] = normalized

        min_conf = self.request.query_params.get("min_confidence")
        if min_conf not in (None, ""):
            try:
                value = float(min_conf)
            except (TypeError, ValueError) as exc:
                raise ValidationError({"min_confidence": "Value must be between 0 and 1."}) from exc
            if not 0.0 <= value <= 1.0:
                raise ValidationError({"min_confidence": "Value must be between 0 and 1."})
            queryset = queryset.filter(confidence__gte=value)
            self._applied_filters["min_confidence"] = value

        return queryset

    @property
    def applied_filters(self):
        return getattr(self, "_applied_filters", {})


class ReferenceResolutionMixin:
    """Resolve textual references into canonical book/chapter/verse."""

    ref_param = "ref"

    def _resolve_reference(self):
        if hasattr(self, "_resolved_reference_cache"):
            return self._resolved_reference_cache

        raw_ref = self.request.query_params.get(self.ref_param, "")
        ref_value = raw_ref.strip()
        if not ref_value:
            raise ValidationError({self.ref_param: "Query parameter 'ref' is required."})

        parsed = _parse_reference_string(ref_value)
        if not parsed.get("items"):
            raise ValidationError({self.ref_param: "Could not parse textual reference."})

        entry = parsed["items"][0]
        lang = getattr(self.request, "lang_code", "en")
        book = resolve_book_by_alias(entry.get("book_raw"), lang) or None
        if book is None:
            try:
                book = get_canonical_book_by_name(entry.get("book_raw"))
            except Exception:
                book = None
        if book is None:
            raise ValidationError({self.ref_param: f"Unknown book '{entry.get('book_raw')}'."})

        chapter = entry.get("chapter")
        verse = entry.get("verse_start")
        try:
            chapter = int(chapter)
            verse = int(verse)
        except (TypeError, ValueError) as exc:
            raise ValidationError({self.ref_param: "Reference must include numeric chapter and verse."}) from exc

        self._input_ref = ref_value
        self._resolved_reference_cache = (ref_value, book, chapter, verse)
        return self._resolved_reference_cache


@method_decorator(cache_page(60), name="get")
class CrossReferencesByVerseView(CrossReferenceFiltersMixin, ReferenceResolutionMixin, generics.ListAPIView):
    serializer_class = CrossReferenceSerializer
    pagination_class = CrossReferencePagination

    def get_queryset(self):
        _, book, chapter, verse = self._resolve_reference()
        base = (
            CrossReference.objects.filter(from_book=book, from_chapter=chapter, from_verse=verse)
            .select_related("from_book", "to_book")
            .order_by("from_book", "from_chapter", "from_verse")
        )
        self._available_total = base.count()
        return self._apply_common_filters(base)

    @extend_schema(
        summary="List cross-references for a verse (by textual reference)",
        tags=["cross-references"],
        parameters=[
            OpenApiParameter(name="ref", description="Text reference (e.g., 'Jo 3:16')", required=True),
            OpenApiParameter(name="source", description="Filter by source code (case-insensitive)", required=False),
            OpenApiParameter(
                name="min_confidence",
                description="Minimum confidence (0-1) to include results",
                required=False,
            ),
            OpenApiParameter(
                name="limit",
                description="Alias for page_size (max 100)",
                required=False,
            ),
        ],
        responses={200: CrossReferenceSerializer(many=True), **get_error_responses()},
        examples=[
            OpenApiExample(
                "For by textual ref",
                value={
                    "pagination": {
                        "count": 2,
                        "num_pages": 1,
                        "current_page": 1,
                        "page_size": 2,
                        "next": None,
                        "previous": None,
                    },
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
                    ],
                    "summary": {
                        "input": "Jo 3:16",
                        "available": 2,
                        "total": 1,
                        "sources": {"TSK": 1},
                        "confidence": {"min": 0.9, "max": 0.9, "avg": 0.9},
                        "filters": {},
                    },
                },
                response_only=True,
            )
        ],
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        available_total = getattr(self, "_available_total", 0)
        if available_total == 0:
            raise NotFound({"detail": "Cross references not found for reference.", "code": "not_found"})

        filtered_total = queryset.count()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            response = Response(serializer.data)

        response.data["summary"] = self._build_summary(queryset, filtered_total, available_total)
        return response

    def _build_summary(self, queryset, filtered_total: int, available_total: int) -> dict:
        summary = {
            "input": getattr(self, "_input_ref", None),
            "available": available_total,
            "total": filtered_total,
            "sources": {},
            "confidence": None,
            "filters": dict(self.applied_filters),
        }

        limit_value = self.request.query_params.get("limit")
        if limit_value not in (None, ""):
            try:
                summary["filters"]["limit"] = int(limit_value)
            except (TypeError, ValueError):
                summary["filters"]["limit"] = limit_value

        source_rows = queryset.values("source").annotate(items=Count("id")).order_by("source")
        summary["sources"] = {(row["source"] or "unknown"): row["items"] for row in source_rows}

        if filtered_total:
            aggregates = queryset.aggregate(
                min_conf=Min("confidence"),
                max_conf=Max("confidence"),
                avg_conf=Avg("confidence"),
            )
            summary["confidence"] = {
                "min": round(float(aggregates["min_conf"]), 3) if aggregates["min_conf"] is not None else None,
                "max": round(float(aggregates["max_conf"]), 3) if aggregates["max_conf"] is not None else None,
                "avg": round(float(aggregates["avg_conf"]), 3) if aggregates["avg_conf"] is not None else None,
            }

        return summary


@method_decorator(cache_page(60), name="get")
class CrossReferencesParallelsView(ReferenceResolutionMixin, generics.ListAPIView):
    """Return parallel passages (Gospels) for a textual reference."""

    serializer_class = CrossReferenceSerializer
    pagination_class = CrossReferencePagination

    GOSPELS = {"Matt", "Mark", "Luke", "John"}

    def get_queryset(self):
        _, book, chapter, verse = self._resolve_reference()
        base = (
            CrossReference.objects.filter(from_book=book, from_chapter=chapter, from_verse=verse)
            .select_related("from_book", "to_book")
            .order_by("to_book__canonical_order", "to_chapter", "to_verse_start")
        )
        return base.filter(to_book__osis_code__in=self.GOSPELS)

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
        self._resolve_reference()
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({"detail": "No parallel passages found", "code": "not_found"}, status=404)
        return super().get(request, *args, **kwargs)


@method_decorator(cache_page(60), name="get")
class CrossReferencesGroupedView(CrossReferenceFiltersMixin, ReferenceResolutionMixin, generics.ListAPIView):
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

    @extend_schema(
        summary="Group cross-references by strength",
        tags=["cross-references"],
        parameters=[
            OpenApiParameter(name="ref", description="Text reference (e.g., 'Jo 3:16')", required=True),
            OpenApiParameter(name="source", description="Filter by source code (case-insensitive)", required=False),
            OpenApiParameter(
                name="min_confidence",
                description="Minimum confidence (0-1) to include in groups",
                required=False,
            ),
        ],
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
        _, book, chapter, verse = self._resolve_reference()
        base = (
            CrossReference.objects.filter(from_book=book, from_chapter=chapter, from_verse=verse)
            .select_related("from_book", "to_book")
            .order_by("-confidence", "-votes")
        )

        queryset = self._apply_common_filters(base)

        groups = {name: [] for name, _ in self.BUCKETS}
        by_source = {}
        total = 0

        for cr in queryset:
            total += 1
            by_source[cr.source or "unknown"] = by_source.get(cr.source or "unknown", 0) + 1
            strength = next((name for name, thr in self.BUCKETS if cr.confidence >= thr), "weak")
            groups[strength].append(cr)

        serializer = CrossReferenceSerializer
        data_groups = []
        for name, _ in self.BUCKETS:
            items = serializer(groups[name], many=True).data if groups[name] else []
            data_groups.append({"strength": name, "count": len(items), "items": items})

        payload = {
            "input": getattr(self, "_input_ref", request.query_params.get("ref")),
            "total": total,
            "by_source": by_source,
            "groups": data_groups,
        }
        if self.applied_filters:
            payload["filters"] = self.applied_filters

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


@method_decorator(cache_page(60), name="get")
class CrossReferencesByThemeView(CrossReferenceFiltersMixin, generics.ListAPIView):
    """GET /api/v1/bible/cross-references/by-theme/<theme_id>/"""

    serializer_class = CrossReferenceSerializer
    pagination_class = CrossReferencePagination

    @extend_schema(
        summary="List cross-references by theme",
        tags=["cross-references"],
        parameters=[
            OpenApiParameter(name="source", description="Filter by source code (case-insensitive)", required=False),
            OpenApiParameter(
                name="min_confidence",
                description="Minimum confidence (0-1) to include results",
                required=False,
            ),
            OpenApiParameter(
                name="limit",
                description="Alias for page_size (max 100)",
                required=False,
            ),
        ],
        responses={
            200: CrossReferenceSerializer(many=True),
            **get_error_responses(),
        },
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if getattr(self, "_available_total", 0) == 0:
            raise NotFound({"detail": "No cross references found for theme.", "code": "not_found"})

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        theme_id = self.kwargs.get("theme_id")
        try:
            theme = Theme.objects.get(pk=theme_id)
        except Theme.DoesNotExist as exc:
            raise NotFound({"detail": "Theme not found", "code": "not_found"}) from exc

        verse_subquery = Verse.objects.filter(
            themes=theme,
            book=OuterRef("from_book"),
            chapter=OuterRef("from_chapter"),
            number=OuterRef("from_verse"),
        )

        base = (
            CrossReference.objects.annotate(is_theme_ref=Exists(verse_subquery))
            .filter(is_theme_ref=True)
            .select_related("from_book", "to_book")
            .order_by("from_book", "from_chapter", "from_verse")
        )
        self._available_total = base.count()
        return self._apply_common_filters(base)
