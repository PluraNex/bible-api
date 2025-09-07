"""Views for themes domain."""
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from ..models import Theme
from .serializers import ThemeSerializer


class ThemeListView(generics.ListAPIView):
    queryset = Theme.objects.all()
    serializer_class = ThemeSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = []

    @extend_schema(summary="List themes", responses={200: ThemeSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ThemeDetailView(generics.RetrieveAPIView):
    queryset = Theme.objects.all()
    serializer_class = ThemeSerializer
    lookup_field = "pk"
    permission_classes = [IsAuthenticated]
    authentication_classes = []

    @extend_schema(summary="Get theme detail", responses={200: ThemeSerializer})
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
