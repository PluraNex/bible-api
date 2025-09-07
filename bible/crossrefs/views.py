"""Views for cross-references domain."""
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from ..models import CrossReference
from .serializers import CrossReferenceSerializer


class CrossReferencesByVerseView(generics.ListAPIView):
    serializer_class = CrossReferenceSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = []

    def get_queryset(self):
        verse_id = self.kwargs["verse_id"]
        return CrossReference.objects.filter(from_verse_id=verse_id).order_by("to_verse_id")

    @extend_schema(summary="List cross-references for a verse", responses={200: CrossReferenceSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CrossReferencesByThemeView(generics.ListAPIView):
    """GET /api/v1/bible/cross-references/by-theme/<theme_id>/"""

    serializer_class = CrossReferenceSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = []

    def get_queryset(self):
        theme_id = self.kwargs["theme_id"]
        return (
            CrossReference.objects.filter(from_verse__theme_links__theme_id=theme_id)
            .select_related("from_verse", "to_verse")
            .order_by("from_verse_id", "to_verse_id")
        )

    @extend_schema(summary="List cross-references by theme", responses={200: CrossReferenceSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
