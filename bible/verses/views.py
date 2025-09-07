"""Views for verses domain."""
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response

from ..models import Book, Verse
from .serializers import VerseSerializer


class VersesByChapterView(generics.ListAPIView):
    serializer_class = VerseSerializer

    def get_queryset(self):
        book_name = self.kwargs["book_name"]
        chapter = self.kwargs["chapter"]
        book = Book.objects.filter(name__iexact=book_name).first()
        if not book:
            return Verse.objects.none()
        return Verse.objects.filter(book=book, chapter=chapter).select_related("book", "version").order_by("number")

    @extend_schema(
        summary="List verses by chapter",
        tags=["verses"],
        responses={
            200: VerseSerializer(many=True),
            401: {"type": "object", "properties": {"detail": {"type": "string"}}},
            404: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
    )
    def get(self, request, *args, **kwargs):
        qs = self.get_queryset()
        if not qs.exists():
            book = Book.objects.filter(name__iexact=self.kwargs["book_name"]).first()
            if book is None:
                return Response({"detail": "Book not found"}, status=status.HTTP_404_NOT_FOUND)
        return super().get(request, *args, **kwargs)


class VerseDetailView(generics.RetrieveAPIView):
    queryset = Verse.objects.all()
    serializer_class = VerseSerializer
    lookup_field = "pk"

    @extend_schema(
        summary="Get verse by id",
        tags=["verses"],
        responses={
            200: VerseSerializer,
            401: {"type": "object", "properties": {"detail": {"type": "string"}}},
            404: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class VersesByThemeView(generics.ListAPIView):
    """GET /api/v1/bible/verses/by-theme/<theme_id>/"""

    serializer_class = VerseSerializer

    def get_queryset(self):
        theme_id = self.kwargs["theme_id"]
        return (
            Verse.objects.filter(theme_links__theme_id=theme_id)
            .select_related("book", "version")
            .order_by("book__order", "chapter", "number")
        )

    @extend_schema(
        summary="List verses by theme",
        tags=["verses"],
        responses={
            200: VerseSerializer(many=True),
            401: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
