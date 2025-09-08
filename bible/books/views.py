"""Views for books domain."""
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.openapi import get_error_responses

from ..models import Book
from .serializers import BookSerializer


class BookListView(generics.ListAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    @extend_schema(
        summary="List books",
        tags=["books"],
        responses={
            200: BookSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class BookInfoView(APIView):
    @extend_schema(
        summary="Get book info",
        tags=["books"],
        responses={
            200: BookSerializer,
            **get_error_responses(),
        },
    )
    def get(self, request, book_name):
        book = Book.objects.filter(name__iexact=book_name).first()
        if not book:
            return Response({"detail": "Book not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(BookSerializer(book).data, status=status.HTTP_200_OK)


class ChaptersByBookView(APIView):
    @extend_schema(
        summary="List chapters by book",
        tags=["books"],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "book": {"type": "string"},
                    "chapters": {"type": "array", "items": {"type": "integer"}},
                },
            },
            **get_error_responses(),
        },
    )
    def get(self, request, book_name):
        book = Book.objects.filter(name__iexact=book_name).first()
        if not book:
            return Response({"detail": "Book not found"}, status=status.HTTP_404_NOT_FOUND)
        chapters = list(range(1, book.chapter_count + 1))
        return Response({"book": book.name, "chapters": chapters}, status=status.HTTP_200_OK)
