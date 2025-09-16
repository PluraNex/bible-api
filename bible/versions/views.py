"""Views for versions domain."""
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from bible.auth.permissions import HasAPIScopes
from common.openapi import LANG_PARAMETER, get_error_responses

from ..models import Version
from .serializers import VersionSerializer


class VersionListView(generics.ListAPIView):
    serializer_class = VersionSerializer
    permission_classes = [HasAPIScopes]
    required_scopes = ["read"]

    def get_queryset(self):
        qs = Version.objects.all().order_by("name")
        language = self.request.query_params.get("language")
        if language:
            try:
                language_id = int(language)
                qs = qs.filter(language__id=language_id)
            except (ValueError, TypeError):
                # If language is not a number, try to filter by language code
                qs = qs.filter(language__code__iexact=language)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            normalized = str(is_active).lower() in {"1", "true", "yes"}
            qs = qs.filter(is_active=normalized)
        return qs

    @extend_schema(
        summary="List Bible versions",
        tags=["versions"],
        parameters=[LANG_PARAMETER],
        responses={200: VersionSerializer(many=True), **get_error_responses()},
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
    permission_classes = [HasAPIScopes]
    required_scopes = ["read"]

    def get_object(self):
        """Get version by code or abbreviation (case-insensitive)."""
        abbreviation = self.kwargs["abbreviation"]
        # Try to find by exact code first, then by code ending with abbreviation
        queryset = self.get_queryset()
        try:
            return queryset.get(code__iexact=abbreviation)
        except Version.DoesNotExist:
            # Try to find by code ending with the abbreviation (e.g., "KJV" matches "EN_KJV")
            return generics.get_object_or_404(queryset, code__iendswith=f"_{abbreviation}")

    @extend_schema(
        summary="Get version by abbreviation",
        tags=["versions"],
        responses={200: VersionSerializer, **get_error_responses()},
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


class VersionDefaultView(APIView):
    """Return default active version for a given language."""

    permission_classes = [HasAPIScopes]
    required_scopes = ["read"]
    throttle_scope = "read"

    def _get_default_version_for_language(self, lang_code):
        """Get default version with base → regional fallback logic.

        When multiple versions exist for the same language, returns the first
        version ordered alphabetically by name (ascending) for predictable results.
        """
        # First, try to find active version for the exact language code
        version = Version.objects.filter(language__code=lang_code, is_active=True).order_by("name").first()

        if version:
            return version

        # If base language (e.g., 'pt'), try regional variants (e.g., 'pt-BR')
        if "-" not in lang_code:
            regional_version = (
                Version.objects.filter(language__code__startswith=f"{lang_code}-", is_active=True)
                .order_by("name")
                .first()
            )

            if regional_version:
                return regional_version

        # If regional language (e.g., 'pt-BR'), try base (e.g., 'pt')
        if "-" in lang_code:
            base_lang = lang_code.split("-")[0]
            base_version = Version.objects.filter(language__code=base_lang, is_active=True).order_by("name").first()

            if base_version:
                return base_version

        # Finally, fallback to English
        if lang_code != "en":
            en_version = Version.objects.filter(language__code="en", is_active=True).order_by("name").first()

            if en_version:
                return en_version

        return None

    @extend_schema(
        summary="Get default version for language",
        tags=["versions"],
        parameters=[LANG_PARAMETER],
        responses={
            200: VersionSerializer,
            404: {
                "description": "No active version found for the language",
                "examples": {
                    "no_version": {
                        "summary": "No active version found",
                        "value": {"detail": "No active version found for language 'xyz'", "code": "version_not_found"},
                    }
                },
            },
            **get_error_responses(),
        },
        examples=[
            OpenApiExample(
                "Default Portuguese version",
                value={
                    "id": 2,
                    "name": "Nova Versão Internacional",
                    "code": "PT_NVI",
                    "abbreviation": "NVI",
                    "language": "pt",
                    "description": "Tradução em português",
                    "is_active": True,
                },
                request_only=False,
                response_only=True,
            ),
            OpenApiExample(
                "Default English version",
                value={
                    "id": 1,
                    "name": "King James Version",
                    "code": "EN_KJV",
                    "abbreviation": "KJV",
                    "language": "en",
                    "description": "Classic English translation",
                    "is_active": True,
                },
                request_only=False,
                response_only=True,
            ),
        ],
    )
    def get(self, request):
        """Get default active version for the requested language."""
        lang_code = request.query_params.get("lang", "en")

        version = self._get_default_version_for_language(lang_code)

        if not version:
            return Response(
                {"detail": f"No active version found for language '{lang_code}'", "code": "version_not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = VersionSerializer(version)
        response = Response(serializer.data)

        # Note: No Vary header needed since this endpoint only uses lang query param,
        # not Accept-Language header resolution

        return response
