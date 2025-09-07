"""Views for themes domain."""
from drf_spectacular.utils import extend_schema
from rest_framework import generics

from ..models import Theme
from .serializers import ThemeSerializer


class ThemeListView(generics.ListAPIView):
    queryset = Theme.objects.all()
    serializer_class = ThemeSerializer

    @extend_schema(summary="List themes")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ThemeDetailView(generics.RetrieveAPIView):
    queryset = Theme.objects.all()
    serializer_class = ThemeSerializer
    lookup_field = "pk"

    @extend_schema(summary="Get theme detail")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

