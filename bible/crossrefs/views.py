"""Views for cross-references domain."""
from drf_spectacular.utils import extend_schema
from rest_framework import generics

from ..models import CrossReference
from .serializers import CrossReferenceSerializer


class CrossReferencesByVerseView(generics.ListAPIView):
    serializer_class = CrossReferenceSerializer

    def get_queryset(self):
        verse_id = self.kwargs["verse_id"]
        return CrossReference.objects.filter(from_verse_id=verse_id).order_by("to_verse_id")

    @extend_schema(summary="List cross-references for a verse")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

