"""Views for commentary domain."""

from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from bible.models import CommentaryEntry
from .serializers import CommentaryEntrySerializer


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
        "source__language__code",
    ]
    search_fields = ["title", "body_text", "author__name"]
    ordering_fields = ["book__canonical_order", "chapter", "verse_start", "created_at"]
    ordering = ["book__canonical_order", "chapter", "verse_start"]

    def get_queryset(self):
        """
        Custom queryset to handle verse range filtering.
        """
        queryset = super().get_queryset()
        
        # Filter by verse range if provided
        verse = self.request.query_params.get("verse")
        if verse:
            # Simple check: entry covers this verse
            # verse_start <= verse <= verse_end
            queryset = queryset.filter(verse_start__lte=verse, verse_end__gte=verse)

        return queryset
