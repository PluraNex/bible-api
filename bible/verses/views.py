"""Views for verses domain."""

import urllib.parse

from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import filters, generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from bible.references.services import resolve_book_by_alias
from bible.references.views import _parse_reference_string  # reuse parser
from bible.utils.i18n import mark_response_language_sensitive
from common.exceptions import build_error_response
from common.mixins import LanguageSensitiveMixin
from common.openapi import LANG_PARAMETER, get_error_responses
from common.pagination import StandardResultsSetPagination

from ..models import Verse, Version
from ..utils import get_canonical_book_by_name
from .filters import VerseFilter
from .serializers import VerseSerializer


class VersesByChapterView(LanguageSensitiveMixin, generics.ListAPIView):
    serializer_class = VerseSerializer
    filterset_class = VerseFilter
    filterset_fields = ["version"]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["text"]
    ordering_fields = ["chapter", "number", "book__canonical_order"]
    ordering = ["number"]
    pagination_class = StandardResultsSetPagination
    permission_classes = [AllowAny]  # Public endpoint for development

    def get_queryset(self):
        book_name = self.kwargs["book_name"]
        # URL decode the book_name parameter to handle special characters
        book_name = urllib.parse.unquote(book_name)
        chapter = self.kwargs["chapter"]
        try:
            book = get_canonical_book_by_name(book_name)
            qs = (
                Verse.objects.filter(book=book, chapter=chapter)
                .select_related(
                    "book",
                    "book__testament",  # Para objeto testament aninhado
                    "version",
                    "version__language",  # Para language_code
                    "version__license",  # Para license info
                )
                .prefetch_related("book__names")
                .order_by("number")
            )

            # Apply default version by language if no explicit version provided
            version_param = self.request.query_params.get("version")
            if version_param:
                return qs

            lang_code = getattr(self.request, "lang_code", "en")

            # Fallback logic aligned with VersionDefaultView
            def pick_default_version(lang: str):
                # exact language
                v = Version.objects.filter(language__code=lang, is_active=True).order_by("name").first()
                if v:
                    return v
                # base -> regional
                if "-" not in lang:
                    v = (
                        Version.objects.filter(language__code__startswith=f"{lang}-", is_active=True)
                        .order_by("name")
                        .first()
                    )
                    if v:
                        return v
                # regional -> base
                if "-" in lang:
                    base = lang.split("-")[0]
                    v = Version.objects.filter(language__code=base, is_active=True).order_by("name").first()
                    if v:
                        return v
                # fallback to English
                if lang != "en":
                    return Version.objects.filter(language__code="en", is_active=True).order_by("name").first()
                return None

            default_version = pick_default_version(lang_code)
            if default_version:
                qs = qs.filter(version=default_version)

            return qs
        except Exception:
            return Verse.objects.none()

    @extend_schema(
        summary="List verses by chapter",
        description="Retrieve all verses from a specific book chapter. Supports URL-encoded book names for special characters and automatic version selection based on language.",
        tags=["verses"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(
                name="version",
                description="Filter by version ID. If not provided, uses default version for request language (optional)",
            ),
            OpenApiParameter(name="search", description="Search within verse text content (optional)"),
        ],
        responses={
            200: VerseSerializer(many=True),
            **get_error_responses(),
        },
        examples=[
            OpenApiExample("Get John chapter 3", value={"book_name": "John", "chapter": 3}, request_only=True),
            OpenApiExample(
                "Get Genesis 1 in Portuguese",
                value={"book_name": "Gênesis", "chapter": 1},
                request_only=True,
                summary="URL-encoded special characters",
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        # Handle book not found case before calling super()
        qs = self.get_queryset()
        if not qs.exists():
            try:
                # URL decode the book_name parameter for error handling
                book_name = urllib.parse.unquote(self.kwargs["book_name"])
                get_canonical_book_by_name(book_name)
            except Exception:
                return build_error_response(
                    "Book not found",
                    "not_found",
                    status.HTTP_404_NOT_FOUND,
                    request=request,
                    vary_accept_language=True,
                )

        return super().get(request, *args, **kwargs)


class VerseListView(LanguageSensitiveMixin, generics.ListAPIView):
    """Listagem geral de versículos com filtros avançados."""

    serializer_class = VerseSerializer
    filterset_class = VerseFilter
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["text", "reference"]
    ordering_fields = ["book__canonical_order", "chapter", "number", "created_at"]
    ordering = ["book__canonical_order", "chapter", "number"]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Queryset base com otimizações."""
        qs = Verse.objects.select_related(
            "book", "book__testament", "version", "version__language", "version__license"
        ).prefetch_related("book__names")

        # Aplicar versão padrão se não especificada
        version_param = self.request.query_params.get("version") or self.request.query_params.get("version_code")

        if not version_param:
            lang_code = getattr(self.request, "lang_code", "en")
            default_version = _pick_default_version_for_lang(lang_code)
            if default_version:
                qs = qs.filter(version=default_version)

        return qs

    @extend_schema(
        summary="List verses with advanced filters",
        description="""General verse listing with comprehensive filtering options.

        Supports filtering by version, book, chapter ranges, testament, language, and more.
        Returns paginated results with full nested objects for book and version.""",
        tags=["verses"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(name="version", description="Filter by version ID"),
            OpenApiParameter(name="version_code", description="Filter by version code (e.g., 'NVI', 'KJV')"),
            OpenApiParameter(name="book", description="Filter by book ID"),
            OpenApiParameter(name="book_osis", description="Filter by book OSIS code (e.g., 'John', 'Gen')"),
            OpenApiParameter(name="book_name", description="Filter by book name (localized)"),
            OpenApiParameter(name="chapter", description="Filter by chapter number"),
            OpenApiParameter(name="chapter_min", description="Minimum chapter number"),
            OpenApiParameter(name="chapter_max", description="Maximum chapter number"),
            OpenApiParameter(name="number", description="Filter by verse number"),
            OpenApiParameter(name="verse_min", description="Minimum verse number"),
            OpenApiParameter(name="verse_max", description="Maximum verse number"),
            OpenApiParameter(name="testament", description="Filter by testament (old/new)"),
            OpenApiParameter(name="testament_id", description="Filter by testament ID"),
            OpenApiParameter(name="language_code", description="Filter by language code (e.g., 'pt-BR', 'en')"),
            OpenApiParameter(name="is_deuterocanonical", description="Filter deuterocanonical books"),
            OpenApiParameter(name="search", description="Search in verse text and reference"),
            OpenApiParameter(
                name="ordering", description="Order by: book__canonical_order, chapter, number, created_at"
            ),
            OpenApiParameter(name="include", description="Include nested objects: book,version (default: both)"),
        ],
        responses={
            200: VerseSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class VerseDetailView(LanguageSensitiveMixin, generics.RetrieveAPIView):
    serializer_class = VerseSerializer
    lookup_field = "pk"

    def get_queryset(self):
        """Otimizar queries com select_related."""
        return Verse.objects.select_related(
            "book", "book__testament", "version", "version__language", "version__license"
        ).prefetch_related("book__names")

    @extend_schema(
        summary="Get verse by id",
        description="Retrieve a single verse by its unique identifier with full nested book and version information.",
        tags=["verses"],
        parameters=[LANG_PARAMETER],
        responses={
            200: VerseSerializer,
            **get_error_responses(),
        },
        examples=[
            OpenApiExample("Get specific verse", value={"pk": 12345}, request_only=True),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class VersesByThemeView(LanguageSensitiveMixin, generics.ListAPIView):
    """GET /api/v1/bible/verses/by-theme/<theme_id>/"""

    serializer_class = VerseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["version", "book"]
    search_fields = ["text"]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        theme_id = self.kwargs["theme_id"]
        return (
            Verse.objects.filter(theme_links__theme_id=theme_id)
            .select_related("book", "book__testament", "version", "version__language", "version__license")
            .prefetch_related("book__names")
            .order_by("book__canonical_order", "chapter", "number")
        )

    @extend_schema(
        summary="List verses by theme",
        description="Retrieve all verses associated with a specific theme. Themes are categorized topics or concepts found in the Bible text.",
        tags=["verses"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(name="version", description="Filter by version ID (optional)"),
            OpenApiParameter(name="book", description="Filter by book ID to limit results to specific book (optional)"),
            OpenApiParameter(name="search", description="Search within verse text content (optional)"),
        ],
        responses={
            200: VerseSerializer(many=True),
            **get_error_responses(),
        },
        examples=[
            OpenApiExample("Get verses for theme ID 42", value={"theme_id": 42}, request_only=True),
            OpenApiExample(
                "Get love-themed verses from John",
                value={"theme_id": 42, "book": 43, "search": "love"},
                request_only=True,
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


def _pick_default_version_for_lang(lang: str) -> Version | None:
    # exact language
    v = Version.objects.filter(language__code=lang, is_active=True).order_by("name").first()
    if v:
        return v
    # base -> regional
    if "-" not in lang:
        v = Version.objects.filter(language__code__startswith=f"{lang}-", is_active=True).order_by("name").first()
        if v:
            return v
    # regional -> base
    if "-" in lang:
        base = lang.split("-")[0]
        v = Version.objects.filter(language__code=base, is_active=True).order_by("name").first()
        if v:
            return v
    # fallback to English
    if lang != "en":
        return Version.objects.filter(language__code="en", is_active=True).order_by("name").first()
    return None


class VersesByReferenceView(LanguageSensitiveMixin, generics.ListAPIView):
    serializer_class = VerseSerializer
    permission_classes = [AllowAny]  # Public endpoint for development

    @extend_schema(
        summary="List verses by free-text reference",
        description="Parse and retrieve verses using natural language reference strings. Supports various formats like 'John 3:16', 'Jo 3:16', or localized book names.",
        tags=["verses"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(
                name="ref",
                description="Reference string in formats like 'John 3:16', 'Jo 3:16-18', or localized names. Supports single verses and ranges within the same chapter.",
                required=True,
            ),
            OpenApiParameter(
                name="version",
                description="Version code (e.g., 'NVI', 'KJV') or ID. If not provided, uses default version for request language (optional)",
            ),
        ],
        responses={200: VerseSerializer(many=True), **get_error_responses()},
        examples=[
            OpenApiExample("Single verse", value={"ref": "Jo 3:16"}, request_only=True),
            OpenApiExample("Verse range (same chapter)", value={"ref": "Jo 3:16-18"}, request_only=True),
            OpenApiExample("Localized book name", value={"ref": "João 3:16", "version": "NVI"}, request_only=True),
        ],
    )
    def get(self, request, *args, **kwargs):
        mark_response_language_sensitive(request)
        ref = request.query_params.get("ref", "").strip()
        if not ref:
            return build_error_response(
                "Query parameter 'ref' is required",
                "validation_error",
                status.HTTP_400_BAD_REQUEST,
                request=request,
                vary_accept_language=True,
            )
        if len(ref) > 200:
            return build_error_response(
                "Payload too large",
                "payload_too_large",
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                request=request,
                vary_accept_language=True,
            )

        # Decodificar URL encoding (ex: Jo%C3%A3o -> João)
        ref = urllib.parse.unquote(ref) if ref else ""

        lang = getattr(request, "lang_code", "en")
        parsed = _parse_reference_string(ref)
        if not parsed["items"]:
            return build_error_response(
                "Unable to parse reference",
                "validation_error",
                status.HTTP_400_BAD_REQUEST,
                request=request,
                vary_accept_language=True,
            )

        entry = parsed["items"][0]
        book = resolve_book_by_alias(entry.get("book_raw"), lang) or None
        if book is None:
            try:
                book = get_canonical_book_by_name(entry.get("book_raw"))
            except Exception:
                book = None
        if book is None:
            return build_error_response(
                "Book not found",
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )

        version_param = request.query_params.get("version")
        qs = Verse.objects.filter(book=book)
        if entry.get("chapter"):
            qs = qs.filter(chapter=entry["chapter"])
        if entry.get("verse_start"):
            qs = qs.filter(number__gte=entry["verse_start"])  # if only one verse, verse_end will equal start
        if entry.get("verse_end"):
            qs = qs.filter(number__lte=entry["verse_end"])  # limited to chapter in this MVP

        qs = (
            qs.select_related("book", "book__testament", "version", "version__language", "version__license")
            .prefetch_related("book__names")
            .order_by("book__canonical_order", "chapter", "number")
        )

        if version_param:
            try:
                # try by id
                version_id = int(version_param)
                qs = qs.filter(version_id=version_id)
            except (ValueError, TypeError):
                # try by code exact, then by suffix
                v = (
                    Version.objects.filter(code__iexact=version_param).first()
                    or Version.objects.filter(code__iendswith=f"_{version_param}").first()
                )
                if v:
                    qs = qs.filter(version=v)
        else:
            default_v = _pick_default_version_for_lang(lang)
            if default_v:
                qs = qs.filter(version=default_v)

        serializer = VerseSerializer(qs, many=True)
        return Response(serializer.data)


class VersesRangeView(LanguageSensitiveMixin, generics.ListAPIView):
    serializer_class = VerseSerializer

    @extend_schema(
        summary="List verses by range reference",
        description="Retrieve verses using range references that can span multiple chapters. Supports formats like 'John 1:31-2:3' for cross-chapter ranges or 'John 1-3' for chapter ranges.",
        tags=["verses"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(
                name="ref",
                description="Range reference supporting cross-chapter formats like 'John 1:31-2:3' or chapter ranges like 'John 1-3'. Maximum 300 verses per request.",
                required=True,
            ),
            OpenApiParameter(
                name="version",
                description="Version code (e.g., 'NVI', 'KJV') or ID. If not provided, uses default version for request language (optional)",
            ),
        ],
        responses={200: VerseSerializer(many=True), **get_error_responses()},
        examples=[
            OpenApiExample("Cross-chapter range", value={"ref": "Jo 1:31-2:3"}, request_only=True),
            OpenApiExample("Chapter range", value={"ref": "Jo 1-3"}, request_only=True),
            OpenApiExample("Single chapter with verses", value={"ref": "Jo 3:16-20"}, request_only=True),
        ],
    )
    def get(self, request, *args, **kwargs):
        mark_response_language_sensitive(request)
        ref = request.query_params.get("ref", "").strip()
        if not ref:
            return build_error_response(
                "Query parameter 'ref' is required",
                "validation_error",
                status.HTTP_400_BAD_REQUEST,
                request=request,
                vary_accept_language=True,
            )
        if len(ref) > 200:
            return build_error_response(
                "Payload too large",
                "payload_too_large",
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                request=request,
                vary_accept_language=True,
            )

        # Decodificar URL encoding (ex: Jo%C3%A3o -> João)
        ref = urllib.parse.unquote(ref) if ref else ""

        lang = getattr(request, "lang_code", "en")
        parsed = _parse_reference_string(ref)
        if not parsed["items"]:
            return build_error_response(
                "Unable to parse reference",
                "validation_error",
                status.HTTP_400_BAD_REQUEST,
                request=request,
                vary_accept_language=True,
            )
        entry = parsed["items"][0]

        book = resolve_book_by_alias(entry.get("book_raw"), lang) or None
        if book is None:
            try:
                book = get_canonical_book_by_name(entry.get("book_raw"))
            except Exception:
                book = None
        if book is None:
            return build_error_response(
                "Book not found",
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )

        start_ch = entry.get("chapter")
        start_v = entry.get("verse_start")
        end_ch = entry.get("chapter_end") or start_ch
        end_v = entry.get("verse_end")
        if start_ch is None:
            return build_error_response(
                "Range requires chapter",
                "validation_error",
                status.HTTP_400_BAD_REQUEST,
                request=request,
                vary_accept_language=True,
            )
        # If no verses provided, interpret as chapter range (e.g., "Jo 1-3") or single chapter ("Jo 1")

        version_param = request.query_params.get("version")
        qs = Verse.objects.filter(book=book)

        # Apply cross-chapter range filter
        if end_ch and end_ch != start_ch:
            # start boundary: same chapter >= start_v (or all verses if start_v missing)
            cond = (
                (Q(chapter=start_ch) & Q(number__gte=start_v or 1))
                | (Q(chapter=end_ch) & Q(number__lte=end_v or 10_000))
                | Q(chapter__gt=start_ch, chapter__lt=end_ch)
            )
            qs = qs.filter(cond)
        else:
            # same chapter
            qs = qs.filter(chapter=start_ch)
            if start_v or end_v:
                if start_v:
                    qs = qs.filter(number__gte=start_v)
                if end_v:
                    qs = qs.filter(number__lte=end_v)

        # Version filtering
        if version_param:
            try:
                version_id = int(version_param)
                qs = qs.filter(version_id=version_id)
            except (ValueError, TypeError):
                v = (
                    Version.objects.filter(code__iexact=version_param).first()
                    or Version.objects.filter(code__iendswith=f"_{version_param}").first()
                )
                if v:
                    qs = qs.filter(version=v)
        else:
            default_v = _pick_default_version_for_lang(lang)
            if default_v:
                qs = qs.filter(version=default_v)

        # Safety limit: cap large ranges
        if qs.count() > 300:
            return build_error_response(
                "Range too large (max 300 verses)",
                "payload_too_large",
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                request=request,
                vary_accept_language=True,
            )

        serializer = VerseSerializer(
            qs.select_related("book", "book__testament", "version", "version__language", "version__license")
            .prefetch_related("book__names")
            .order_by("book__canonical_order", "chapter", "number"),
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class VersesCompareView(LanguageSensitiveMixin, APIView):
    permission_classes = [AllowAny]  # Public endpoint for verse comparison

    @extend_schema(
        summary="Compare verse across versions",
        description="Compare the same verse or verse range across multiple Bible versions. Useful for studying textual variations and translations.",
        tags=["verses"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(
                name="ref",
                description="Reference string for the verse(s) to compare (e.g., 'John 3:16'). Supports single verses and same-chapter ranges.",
                required=True,
            ),
            OpenApiParameter(
                name="versions",
                description="Comma-separated list of version codes or IDs (e.g., 'KJV,NVI,ARA'). Maximum 5 versions per request.",
                required=True,
            ),
        ],
        responses={200: VerseSerializer(many=True), **get_error_responses()},
        examples=[
            OpenApiExample(
                "Compare across versions", value={"ref": "Jo 3:16", "versions": "KJV,NVI,ARA"}, request_only=True
            ),
            OpenApiExample(
                "Compare verse range", value={"ref": "Jo 3:16-18", "versions": "NIV,KJV"}, request_only=True
            ),
        ],
    )
    def get(self, request):
        mark_response_language_sensitive(request)
        ref_raw = request.query_params.get("ref", "").strip()
        versions_param = request.query_params.get("versions", "").strip()
        # Decodificar URL encoding (ex: Jo%C3%A3o -> João)
        ref = urllib.parse.unquote(ref_raw) if ref_raw else ""
        if not ref or not versions_param:
            return build_error_response(
                "Parameters 'ref' and 'versions' are required",
                "validation_error",
                status.HTTP_400_BAD_REQUEST,
                request=request,
                vary_accept_language=True,
            )
        versions_list = [v.strip() for v in versions_param.split(",") if v.strip()]
        if len(versions_list) > 5:
            return build_error_response(
                "Too many versions (max 5)",
                "payload_too_large",
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                request=request,
                vary_accept_language=True,
            )
        lang = getattr(request, "lang_code", "en")

        parsed = _parse_reference_string(ref)
        if not parsed["items"]:
            return build_error_response(
                "Unable to parse reference",
                "validation_error",
                status.HTTP_400_BAD_REQUEST,
                request=request,
                vary_accept_language=True,
            )
        entry = parsed["items"][0]
        book = resolve_book_by_alias(entry.get("book_raw"), lang) or None
        if book is None:
            try:
                book = get_canonical_book_by_name(entry.get("book_raw"))
            except Exception:
                book = None
        if book is None:
            return build_error_response(
                "Book not found",
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )

        # For each version, get verses
        results = []
        for vref in versions_list:
            v_obj = None
            try:
                v_id = int(vref)
                v_obj = Version.objects.filter(pk=v_id).first()
            except (ValueError, TypeError):
                v_obj = (
                    Version.objects.filter(code__iexact=vref).first()
                    or Version.objects.filter(code__iendswith=f"_{vref}").first()
                )
            if not v_obj:
                results.append({"version": vref, "error": "version_not_found"})
                continue

            qs = Verse.objects.filter(book=book, version=v_obj)
            if entry.get("chapter"):
                qs = qs.filter(chapter=entry["chapter"])
            if entry.get("verse_start"):
                qs = qs.filter(number__gte=entry["verse_start"])  # if only one verse, same num
            if entry.get("verse_end"):
                qs = qs.filter(number__lte=entry["verse_end"])  # same-chapter MVP
            # Safety: cap per-version
            if qs.count() > 300:
                return Response(
                    {
                        "detail": f"Range too large for version {v_obj.code} (max 300 verses)",
                        "code": "payload_too_large",
                    },
                    status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                )
            verses = VerseSerializer(
                qs.select_related("book", "book__testament", "version", "version__language", "version__license")
                .prefetch_related("book__names")
                .order_by("number"),
                many=True,
                context={"request": request},
            ).data
            results.append(
                {
                    "version": v_obj.code,
                    "abbreviation": v_obj.abbreviation,
                    "language": getattr(v_obj.language, "code", None),
                    "verses": verses,
                }
            )

        return Response({"results": results})
