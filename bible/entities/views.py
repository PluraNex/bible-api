"""Views for Biblical Entities domain."""

from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from bible.models import CanonicalBook

from .models import (
    CanonicalEntity,
    EntityRelationship,
    EntityVerseLink,
)
from .serializers import (
    EntityByVerseSerializer,
    EntityCompactSerializer,
    EntityDetailSerializer,
    EntityListSerializer,
    EntityRelationshipSerializer,
)


class CanonicalEntityViewSet(viewsets.ReadOnlyModelViewSet):
    """Biblical entities: people, places, objects, events, etc."""

    lookup_field = "canonical_id"
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["namespace", "status"]
    search_fields = ["primary_name", "description", "aliases__name"]
    ordering_fields = ["primary_name", "priority", "boost", "verse_count"]
    ordering = ["-priority", "primary_name"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return EntityDetailSerializer
        return EntityListSerializer

    def get_queryset(self):
        qs = CanonicalEntity.objects.select_related("person")
        if self.action == "retrieve":
            qs = qs.prefetch_related("aliases", "roles")
        return qs

    @extend_schema(
        summary="List biblical entities",
        tags=["entities"],
        parameters=[
            OpenApiParameter(name="namespace", description="Filter by namespace (PERSON, PLACE, etc.)", required=False, type=str),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Get entity detail", tags=["entities"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Entity relationships",
        tags=["entities"],
        parameters=[
            OpenApiParameter(name="direction", description="Filter: outgoing, incoming, all (default)", required=False, type=str),
        ],
    )
    @action(detail=True, methods=["get"])
    def relationships(self, request, canonical_id=None):
        entity = self.get_object()

        direction = request.query_params.get("direction", "all")

        rels = EntityRelationship.objects.select_related("source", "target")

        if direction == "outgoing":
            rels = rels.filter(source=entity)
        elif direction == "incoming":
            rels = rels.filter(target=entity)
        else:
            rels = rels.filter(Q(source=entity) | Q(target=entity))

        results = []
        for rel in rels[:100]:
            if rel.source_id == entity.id:
                dir_label = "outgoing"
                related = rel.target
            else:
                dir_label = "incoming"
                related = rel.source

            results.append({
                "relationship_type": rel.relationship_type,
                "direction": dir_label,
                "related_entity": EntityCompactSerializer(related).data,
                "description": rel.description,
            })

        serializer = EntityRelationshipSerializer(results, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Entities for a Bible verse (StudyRail EntitiesTab)",
        tags=["entities"],
    )
    @action(detail=False, url_path="by-verse/(?P<book>[^/]+)/(?P<chapter>[0-9]+)/(?P<verse>[0-9]+)")
    def by_verse(self, request, book=None, chapter=None, verse=None):
        try:
            canonical_book = CanonicalBook.objects.get(osis_code__iexact=book)
        except CanonicalBook.DoesNotExist:
            return Response({"detail": f'Book "{book}" not found.'}, status=404)

        links = (
            EntityVerseLink.objects
            .filter(
                verse__book=canonical_book,
                verse__chapter=int(chapter),
                verse__number=int(verse),
            )
            .select_related("entity")
        )

        results = []
        for link in links:
            e = link.entity
            results.append({
                "canonical_id": e.canonical_id,
                "namespace": e.namespace,
                "primary_name": e.primary_name,
                "description": e.description,
                "mention_type": link.mention_type,
                "is_primary_subject": link.is_primary_subject,
                "relevance": link.relevance,
            })

        serializer = EntityByVerseSerializer(results, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Search entities",
        tags=["entities"],
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
            CanonicalEntity.objects
            .select_related("person")
            .filter(
                Q(primary_name__icontains=q)
                | Q(description__icontains=q)
                | Q(aliases__name__icontains=q)
                | Q(canonical_id__iexact=q)
            )
            .distinct()
        )

        namespace = request.query_params.get("namespace")
        if namespace:
            qs = qs.filter(namespace=namespace)

        qs = qs.order_by("-boost", "-priority")[:limit]
        serializer = EntityListSerializer(qs, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Entities for an entire chapter (for inline annotations)",
        tags=["entities"],
    )
    @action(detail=False, url_path="by-chapter/(?P<book>[^/]+)/(?P<chapter>[0-9]+)")
    def by_chapter(self, request, book=None, chapter=None):
        try:
            canonical_book = CanonicalBook.objects.get(osis_code__iexact=book)
        except CanonicalBook.DoesNotExist:
            return Response({"detail": f'Book "{book}" not found.'}, status=404)

        from collections import defaultdict

        links = (
            EntityVerseLink.objects
            .filter(verse__book=canonical_book, verse__chapter=int(chapter))
            .select_related("entity")
        )

        entity_verses = defaultdict(dict)
        entity_contexts = defaultdict(dict)
        entity_data = {}
        for link in links:
            e = link.entity
            v_num = link.verse.number
            entity_verses[e.canonical_id][v_num] = link.match_words or []
            if link.context_note:
                entity_contexts[e.canonical_id][v_num] = link.context_note
            if e.canonical_id not in entity_data:
                entity_data[e.canonical_id] = {
                    "canonical_id": e.canonical_id,
                    "primary_name": e.primary_name,
                    "namespace": e.namespace,
                }

        results = []
        for cid, data in entity_data.items():
            verse_map = entity_verses[cid]
            ctx_map = entity_contexts.get(cid, {})
            data["verses"] = sorted(verse_map.keys())
            data["match_words"] = {str(k): v for k, v in verse_map.items()}
            if ctx_map:
                data["contexts"] = {str(k): v for k, v in ctx_map.items()}
            results.append(data)

        return Response(results)

    @extend_schema(summary="Images depicting this entity", tags=["entities"])
    @action(detail=True, methods=["get"])
    def images(self, request, canonical_id=None):
        from bible.images.serializers import BiblicalImageListSerializer
        from bible.integration.models import ImageEntityLink

        entity = self.get_object()
        links = (
            ImageEntityLink.objects
            .filter(entity=entity)
            .select_related("image__artist")
            .order_by("-confidence")[:50]
        )
        images = [link.image for link in links]
        serializer = BiblicalImageListSerializer(images, many=True)
        return Response(serializer.data)

    @extend_schema(summary="Entity namespace counts", tags=["entities"])
    @action(detail=False, url_path="namespaces")
    def namespaces(self, request):
        data = (
            CanonicalEntity.objects
            .values("namespace")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        results = [
            {"namespace": d["namespace"], "count": d["count"]}
            for d in data
        ]
        return Response(results)
