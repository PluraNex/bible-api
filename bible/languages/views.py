"""Views for languages listing."""
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics

from common.openapi import get_error_responses

from ..books.serializers import LanguageSerializer
from ..models import Language


class LanguageListView(generics.ListAPIView):
    """List available languages with optional filtering by code."""

    queryset = Language.objects.all().order_by("name")
    serializer_class = LanguageSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["code"]

    @extend_schema(
        summary="List languages",
        tags=["languages"],
        parameters=[
            OpenApiParameter(name="code", description="Filter by language code (e.g., 'en', 'pt', 'pt-BR')"),
        ],
        responses={200: LanguageSerializer(many=True), **get_error_responses()},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
