"""Views for commentary domain."""

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from bible.commentaries import Author, CommentaryEntry, CommentarySource
from .serializers import (
    AuthorDetailSerializer,
    AuthorListSerializer,
    CommentaryEntrySerializer,
    CommentarySourceSerializer,
)


class AuthorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for commentary authors (Church Fathers, Reformers, etc.).
    Supports filtering by type, tradition, hermeneutic, and search.
    """

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        "author_type",
        "tradition",
        "primary_hermeneutic",
        "orthodoxy_status",
        "is_saint",
        "is_doctor_of_church",
    ]
    search_fields = ["name", "short_name", "biography_summary", "theological_contributions"]
    ordering_fields = ["name", "birth_year", "death_year", "author_type"]
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AuthorDetailSerializer
        return AuthorListSerializer

    def get_queryset(self):
        qs = Author.objects.all()
        era = self.request.query_params.get("era")
        if era:
            qs = qs.filter(era=era)
        return qs

    @extend_schema(
        summary="List commentary authors",
        description="List all authors with filtering by type, tradition, era, hermeneutic, orthodoxy.",
        tags=["commentaries"],
        parameters=[
            OpenApiParameter(name="era", description="Filter by patristic era (e.g., ante_nicene, nicene, medieval)", required=False, type=str),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Get author detail",
        description="Full author profile with biography, theological metadata, avatar, and entry count.",
        tags=["commentaries"],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Get author's commentary entries",
        description="List all commentary entries by this author.",
        tags=["commentaries"],
    )
    @action(detail=True, methods=["get"])
    def entries(self, request, pk=None):
        author = self.get_object()
        entries = CommentaryEntry.objects.filter(author=author).select_related("book", "source")[:50]
        serializer = CommentaryEntrySerializer(entries, many=True)
        return Response(serializer.data)


class SourceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for commentary sources (Catena Bible, CCEL, etc.)."""

    queryset = CommentarySource.objects.filter(is_active=True)
    serializer_class = CommentarySourceSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "description"]

    @extend_schema(summary="List commentary sources", tags=["commentaries"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Get source detail", tags=["commentaries"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class CommentaryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing commentary entries.
    Supports filtering by book, chapter, verse range, author, and source.
    """

    queryset = CommentaryEntry.objects.select_related("author", "source", "book").all()
    serializer_class = CommentaryEntrySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        "book__osis_code",
        "chapter",
        "author__name",
        "source__short_code",
    ]
    search_fields = ["title", "body_text", "author__name"]
    ordering_fields = ["book__canonical_order", "chapter", "verse_start", "created_at"]
    ordering = ["book__canonical_order", "chapter", "verse_start"]

    @extend_schema(
        summary="List commentary entries",
        description="Filter by book, chapter, verse, author, source. Use ?verse=N for exact verse.",
        tags=["commentaries"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Get commentary entry detail", tags=["commentaries"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        verse = self.request.query_params.get("verse")
        if verse:
            try:
                verse_int = int(verse)
                queryset = queryset.filter(verse_start__lte=verse_int, verse_end__gte=verse_int)
            except (ValueError, TypeError):
                queryset = queryset.none()
        return queryset
