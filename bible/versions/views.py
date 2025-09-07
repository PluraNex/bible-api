"""Views for versions domain."""
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import generics

from ..models import Version
from .serializers import VersionSerializer


class VersionListView(generics.ListAPIView):
    serializer_class = VersionSerializer

    def get_queryset(self):
        qs = Version.objects.all().order_by("name")
        language = self.request.query_params.get("language")
        if language:
            qs = qs.filter(language__iexact=language)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            normalized = str(is_active).lower() in {"1", "true", "yes"}
            qs = qs.filter(is_active=normalized)
        return qs

    @extend_schema(
        summary="List Bible versions",
        tags=["versions"],
        responses={
            200: VersionSerializer(many=True),
            401: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
        examples=[
            OpenApiExample(
                "List versions",
                value={
                    "count": 2,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "id": 1,
                            "name": "King James Version",
                            "abbreviation": "KJV",
                            "language": "en",
                            "description": "Classic English translation",
                            "is_active": True,
                        },
                        {
                            "id": 2,
                            "name": "Nova Versão Internacional",
                            "abbreviation": "NVI",
                            "language": "pt",
                            "description": "Tradução em português",
                            "is_active": True,
                        },
                    ],
                },
            )
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class VersionDetailView(generics.RetrieveAPIView):
    queryset = Version.objects.all()
    serializer_class = VersionSerializer
    lookup_field = "abbreviation"

    @extend_schema(
        summary="Get version by abbreviation",
        tags=["versions"],
        responses={
            200: VersionSerializer,
            401: {"type": "object", "properties": {"detail": {"type": "string"}}},
            404: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
        examples=[
            OpenApiExample(
                "Version detail",
                value={
                    "id": 1,
                    "name": "King James Version",
                    "abbreviation": "KJV",
                    "language": "en",
                    "description": "Classic English translation",
                    "is_active": True,
                },
            )
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
