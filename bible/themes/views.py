"""Views for themes domain."""
from drf_spectacular.utils import extend_schema
from rest_framework import generics

from ..models import Theme
from .serializers import ThemeSerializer


class ThemeListView(generics.ListAPIView):
    queryset = Theme.objects.all()
    serializer_class = ThemeSerializer

    @extend_schema(
        summary="List themes",
        tags=["themes"],
        responses={
            200: ThemeSerializer(many=True),
            401: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ThemeDetailView(generics.RetrieveAPIView):
    queryset = Theme.objects.all()
    serializer_class = ThemeSerializer
    lookup_field = "pk"

    @extend_schema(
        summary="Get theme detail",
        tags=["themes"],
        responses={
            200: ThemeSerializer,
            401: {"type": "object", "properties": {"detail": {"type": "string"}}},
            404: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
