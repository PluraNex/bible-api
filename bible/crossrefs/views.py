"""Views for cross-references domain."""
from drf_spectacular.utils import extend_schema
from rest_framework import generics

from common.openapi import get_error_responses

from ..models import CrossReference
from .serializers import CrossReferenceSerializer


class CrossReferencesByVerseView(generics.ListAPIView):
    serializer_class = CrossReferenceSerializer

    def get_queryset(self):
        verse_id = self.kwargs["verse_id"]
        return CrossReference.objects.filter(from_verse_id=verse_id).order_by("to_verse_id")

    @extend_schema(
        summary="List cross-references for a verse",
        tags=["cross-references"],
        responses={
            200: CrossReferenceSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CrossReferencesByThemeView(generics.ListAPIView):
    """GET /api/v1/bible/cross-references/by-theme/<theme_id>/"""

    serializer_class = CrossReferenceSerializer

    def get_queryset(self):
        theme_id = self.kwargs["theme_id"]
        return (
            CrossReference.objects.filter(from_verse__theme_links__theme_id=theme_id)
            .select_related("from_verse", "to_verse")
            .order_by("from_verse_id", "to_verse_id")
        )

    @extend_schema(
        summary="List cross-references by theme",
        tags=["cross-references"],
        responses={
            200: CrossReferenceSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
