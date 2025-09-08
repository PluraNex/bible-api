"""Views for themes domain."""
from drf_spectacular.utils import extend_schema
from rest_framework import generics

from common.openapi import get_error_responses

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
            **get_error_responses(),
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
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
