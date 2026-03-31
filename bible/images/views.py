"""Views for Biblical Images domain."""

from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from bible.models import CanonicalBook

from .models import Artist, BiblicalImage, ImageVerseLink
from .serializers import (
    ArtistDetailSerializer,
    ArtistListSerializer,
    BiblicalImageByVerseSerializer,
    BiblicalImageDetailSerializer,
    BiblicalImageListSerializer,
)


class ArtistViewSet(viewsets.ReadOnlyModelViewSet):
    """Artists who created biblical art."""

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "image_count"]
    ordering = ["-image_count"]
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ArtistDetailSerializer
        return ArtistListSerializer

    def get_queryset(self):
        return Artist.objects.all()

    @extend_schema(summary="List artists", tags=["images"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Get artist detail", tags=["images"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Get artist's images",
        tags=["images"],
    )
    @action(detail=True, methods=["get"])
    def images(self, request, slug=None):
        artist = self.get_object()
        images = BiblicalImage.objects.filter(artist=artist).order_by("-completion_year")[:50]
        serializer = BiblicalImageListSerializer(images, many=True)
        return Response(serializer.data)


class BiblicalImageViewSet(viewsets.ReadOnlyModelViewSet):
    """Biblical art images with AI-generated tags and verse links."""

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_tagged", "source"]
    search_fields = ["title", "artist__name"]
    ordering_fields = ["completion_year", "title", "created_at"]
    ordering = ["-completion_year"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return BiblicalImageDetailSerializer
        return BiblicalImageListSerializer

    def get_queryset(self):
        qs = BiblicalImage.objects.select_related("artist")
        if self.action == "retrieve":
            qs = qs.prefetch_related("tag", "verse_links__book")

        # Custom filters for JSONB contains
        style = self.request.query_params.get("style")
        if style:
            qs = qs.filter(styles__contains=[style])
        genre = self.request.query_params.get("genre")
        if genre:
            qs = qs.filter(genres__contains=[genre])
        artist_slug = self.request.query_params.get("artist")
        if artist_slug:
            qs = qs.filter(artist__slug=artist_slug)
        return qs

    @extend_schema(
        summary="List biblical images",
        tags=["images"],
        parameters=[
            OpenApiParameter(name="style", description="Filter by art style (e.g., Baroque)", required=False, type=str),
            OpenApiParameter(name="genre", description="Filter by genre (e.g., religious painting)", required=False, type=str),
            OpenApiParameter(name="artist", description="Filter by artist slug", required=False, type=str),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Get image detail with tags and verse links", tags=["images"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Images for a Bible verse (ArtsTab)",
        description="Returns images linked to a specific verse. Powers the ArtsTab in the study rail.",
        tags=["images"],
    )
    @action(detail=False, url_path="by-verse/(?P<book>[^/]+)/(?P<chapter>[0-9]+)/(?P<verse>[0-9]+)")
    def by_verse(self, request, book=None, chapter=None, verse=None):
        try:
            canonical_book = CanonicalBook.objects.get(osis_code__iexact=book)
        except CanonicalBook.DoesNotExist:
            return Response({"detail": f'Book "{book}" not found.'}, status=404)

        chapter = int(chapter)
        verse = int(verse)

        links = (
            ImageVerseLink.objects
            .filter(
                book=canonical_book,
                chapter=chapter,
                verse_start__lte=verse,
                verse_end__gte=verse,
            )
            .select_related("image__artist", "image__tag")
        )

        results = []
        for link in links:
            img = link.image
            tag = getattr(img, "tag", None)
            results.append({
                "id": img.id,
                "key": img.key,
                "title": img.title,
                "artist_name": img.artist.name,
                "completion_year": img.completion_year,
                "image_url": img.image_url,
                "thumbnail_url": img.thumbnail_url,
                "relevance_type": link.relevance_type,
                "description": tag.description if tag else "",
                "characters": tag.characters if tag else [],
            })

        serializer = BiblicalImageByVerseSerializer(results, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Search images by text",
        tags=["images"],
        parameters=[OpenApiParameter(name="q", description="Search query", required=True, type=str)],
    )
    @action(detail=False, url_path="search")
    def search(self, request):
        q = request.query_params.get("q", "").strip()
        if not q:
            return Response({"detail": 'Query parameter "q" is required.'}, status=400)

        images = (
            BiblicalImage.objects
            .select_related("artist")
            .filter(
                Q(title__icontains=q)
                | Q(artist__name__icontains=q)
                | Q(tag__tag_list__contains=[q])
                | Q(tag__event__icontains=q)
                | Q(tag__description__icontains=q)
            )
            .distinct()[:50]
        )
        serializer = BiblicalImageListSerializer(images, many=True)
        return Response(serializer.data)
