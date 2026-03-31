"""Views for Biblical Symbols domain."""

from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from bible.models import CanonicalBook

from .models import BiblicalSymbol, SymbolOccurrence
from .serializers import (
    SymbolByVerseSerializer,
    SymbolDetailSerializer,
    SymbolListSerializer,
)


class BiblicalSymbolViewSet(viewsets.ReadOnlyModelViewSet):
    """Biblical symbols with theological meanings and progressions."""

    lookup_field = "canonical_id"
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["namespace", "status"]
    search_fields = ["primary_name", "primary_name_pt", "literal_meaning"]
    ordering_fields = ["primary_name", "priority", "boost", "frequency"]
    ordering = ["-priority", "primary_name"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SymbolDetailSerializer
        return SymbolListSerializer

    def get_queryset(self):
        qs = BiblicalSymbol.objects.all()
        if self.action == "list":
            qs = qs.annotate(meaning_count=Count("meanings")).prefetch_related("meanings")
        elif self.action == "retrieve":
            qs = qs.prefetch_related(
                "meanings", "progressions", "related_symbols", "opposite_symbol",
            )
        return qs

    @extend_schema(
        summary="List biblical symbols",
        tags=["symbols"],
        parameters=[
            OpenApiParameter(name="namespace", description="Filter by namespace (NATURAL, OBJECT, etc.)", required=False, type=str),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Get symbol detail with meanings and progressions", tags=["symbols"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Symbols for a Bible verse (StudyRail SymbolsTab)",
        tags=["symbols"],
    )
    @action(detail=False, url_path="by-verse/(?P<book>[^/]+)/(?P<chapter>[0-9]+)/(?P<verse>[0-9]+)")
    def by_verse(self, request, book=None, chapter=None, verse=None):
        try:
            canonical_book = CanonicalBook.objects.get(osis_code__iexact=book)
        except CanonicalBook.DoesNotExist:
            return Response({"detail": f'Book "{book}" not found.'}, status=404)

        occurrences = (
            SymbolOccurrence.objects
            .filter(
                verse__book=canonical_book,
                verse__chapter=int(chapter),
                verse__number=int(verse),
            )
            .select_related("symbol", "meaning")
        )

        results = []
        for occ in occurrences:
            s = occ.symbol
            results.append({
                "canonical_id": s.canonical_id,
                "namespace": s.namespace,
                "primary_name": s.primary_name,
                "emoji": s.emoji,
                "literal_meaning": s.literal_meaning,
                "usage_type": occ.usage_type,
                "context_note": occ.context_note,
            })

        serializer = SymbolByVerseSerializer(results, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Symbols for an entire chapter (for inline annotations)",
        tags=["symbols"],
    )
    @action(detail=False, url_path="by-chapter/(?P<book>[^/]+)/(?P<chapter>[0-9]+)")
    def by_chapter(self, request, book=None, chapter=None):
        try:
            canonical_book = CanonicalBook.objects.get(osis_code__iexact=book)
        except CanonicalBook.DoesNotExist:
            return Response({"detail": f'Book "{book}" not found.'}, status=404)

        from collections import defaultdict

        occurrences = (
            SymbolOccurrence.objects
            .filter(verse__book=canonical_book, verse__chapter=int(chapter))
            .select_related("symbol")
        )

        symbol_verses = defaultdict(dict)
        symbol_contexts = defaultdict(dict)
        symbol_data = {}
        for occ in occurrences:
            s = occ.symbol
            v_num = occ.verse.number
            symbol_verses[s.canonical_id][v_num] = occ.match_words or []
            if occ.context_note:
                symbol_contexts[s.canonical_id][v_num] = occ.context_note
            if s.canonical_id not in symbol_data:
                symbol_data[s.canonical_id] = {
                    "canonical_id": s.canonical_id,
                    "primary_name": s.primary_name,
                    "namespace": s.namespace,
                    "kind": "symbol",
                }

        results = []
        for cid, data in symbol_data.items():
            verse_map = symbol_verses[cid]
            ctx_map = symbol_contexts.get(cid, {})
            data["verses"] = sorted(verse_map.keys())
            data["match_words"] = {str(k): v for k, v in verse_map.items()}
            if ctx_map:
                data["contexts"] = {str(k): v for k, v in ctx_map.items()}
            results.append(data)

        return Response(results)

    @extend_schema(
        summary="Search symbols",
        tags=["symbols"],
        parameters=[
            OpenApiParameter(name="q", description="Search query", required=True, type=str),
            OpenApiParameter(name="namespace", description="Filter by namespace", required=False, type=str),
        ],
    )
    @action(detail=False, url_path="search")
    def search(self, request):
        q = request.query_params.get("q", "").strip()
        if not q:
            return Response({"detail": 'Query parameter "q" is required.'}, status=400)

        limit = min(int(request.query_params.get("limit", 20)), 50)

        qs = (
            BiblicalSymbol.objects
            .filter(
                Q(primary_name__icontains=q)
                | Q(primary_name_pt__icontains=q)
                | Q(aliases__contains=[q])
                | Q(meanings__meaning__icontains=q)
                | Q(canonical_id__iexact=q)
            )
            .distinct()
        )

        namespace = request.query_params.get("namespace")
        if namespace:
            qs = qs.filter(namespace=namespace)

        qs = qs.order_by("-boost", "-priority")[:limit]
        serializer = SymbolListSerializer(qs, many=True)
        return Response(serializer.data)

    @extend_schema(summary="Symbol namespace counts", tags=["symbols"])
    @action(detail=False, url_path="namespaces")
    def namespaces(self, request):
        data = (
            BiblicalSymbol.objects
            .values("namespace")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        results = [
            {"namespace": d["namespace"], "count": d["count"]}
            for d in data
        ]
        return Response(results)

    @extend_schema(
        summary="Symbols by theological context",
        tags=["symbols"],
    )
    @action(detail=False, url_path="by-context/(?P<context>[a-z_]+)")
    def by_context(self, request, context=None):
        symbols = (
            BiblicalSymbol.objects
            .filter(meanings__theological_context=context)
            .distinct()
            .order_by("-boost", "-priority")[:50]
        )
        serializer = SymbolListSerializer(symbols, many=True)
        return Response(serializer.data)
