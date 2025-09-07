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
        return Verse.objects.filter(book=book, chapter=chapter).order_by("number")

    @extend_schema(summary="List verses by chapter")
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

    @extend_schema(summary="Get verse by id")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

