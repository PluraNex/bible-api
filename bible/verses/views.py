"""Views for verses domain."""
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import filters, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from bible.references.services import resolve_book_by_alias
from bible.references.views import _parse_reference_string  # reuse parser
from bible.utils.i18n import mark_response_language_sensitive
from common.mixins import LanguageSensitiveMixin
from common.openapi import LANG_PARAMETER, get_error_responses

from ..models import Verse, Version
from ..utils import get_canonical_book_by_name
from .serializers import VerseSerializer


class VersesByChapterView(LanguageSensitiveMixin, generics.ListAPIView):
    serializer_class = VerseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["version"]
    search_fields = ["text"]

    def get_queryset(self):
        book_name = self.kwargs["book_name"]
        chapter = self.kwargs["chapter"]
        try:
            book = get_canonical_book_by_name(book_name)
            qs = Verse.objects.filter(book=book, chapter=chapter).select_related("book", "version").order_by("number")

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
        tags=["verses"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(name="version", description="Filter by version ID"),
            OpenApiParameter(name="search", description="Search in verse text"),
        ],
        responses={
            200: VerseSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        # Handle book not found case before calling super()
        qs = self.get_queryset()
        if not qs.exists():
            try:
                get_canonical_book_by_name(self.kwargs["book_name"])
            except Exception:
                response = Response({"detail": "Book not found"}, status=status.HTTP_404_NOT_FOUND)
                # Ensure Vary header on error response
                response["Vary"] = "Accept-Language"
                return response

        return super().get(request, *args, **kwargs)


class VerseDetailView(LanguageSensitiveMixin, generics.RetrieveAPIView):
    queryset = Verse.objects.all()
    serializer_class = VerseSerializer
    lookup_field = "pk"

    @extend_schema(
        summary="Get verse by id",
        tags=["verses"],
        parameters=[LANG_PARAMETER],
        responses={
            200: VerseSerializer,
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class VersesByThemeView(LanguageSensitiveMixin, generics.ListAPIView):
    """GET /api/v1/bible/verses/by-theme/<theme_id>/"""

    serializer_class = VerseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["version", "book"]
    search_fields = ["text"]

    def get_queryset(self):
        theme_id = self.kwargs["theme_id"]
        return (
            Verse.objects.filter(theme_links__theme_id=theme_id)
            .select_related("book", "version")
            .order_by("book__canonical_order", "chapter", "number")
        )

    @extend_schema(
        summary="List verses by theme",
        tags=["verses"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(name="version", description="Filter by version ID"),
            OpenApiParameter(name="book", description="Filter by book ID"),
            OpenApiParameter(name="search", description="Search in verse text"),
        ],
        responses={
            200: VerseSerializer(many=True),
            **get_error_responses(),
        },
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

    @extend_schema(
        summary="List verses by free-text reference",
        tags=["verses"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(name="ref", description="Reference string (e.g., 'Jo 3:16')", required=True),
            OpenApiParameter(name="version", description="Version code or id (optional)"),
        ],
        responses={200: VerseSerializer(many=True), **get_error_responses()},
        examples=[
            OpenApiExample("Single verse", value={"ref": "Jo 3:16"}, request_only=True),
            OpenApiExample("Verse range (same chapter)", value={"ref": "Jo 3:16-18"}, request_only=True),
        ],
    )
    def get(self, request, *args, **kwargs):
        mark_response_language_sensitive(request)
        ref = request.query_params.get("ref", "").strip()
        if not ref:
            return Response(
                {"detail": "Query parameter 'ref' is required", "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(ref) > 200:
            return Response(
                {"detail": "Payload too large", "code": "payload_too_large"},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        lang = getattr(request, "lang_code", "en")
        parsed = _parse_reference_string(ref)
        if not parsed["items"]:
            return Response(
                {"detail": "Unable to parse reference", "code": "validation_error"}, status=status.HTTP_400_BAD_REQUEST
            )

        entry = parsed["items"][0]
        book = resolve_book_by_alias(entry.get("book_raw"), lang) or None
        if book is None:
            try:
                book = get_canonical_book_by_name(entry.get("book_raw"))
            except Exception:
                book = None
        if book is None:
            return Response({"detail": "Book not found", "code": "not_found"}, status=status.HTTP_404_NOT_FOUND)

        version_param = request.query_params.get("version")
        qs = Verse.objects.filter(book=book)
        if entry.get("chapter"):
            qs = qs.filter(chapter=entry["chapter"])
        if entry.get("verse_start"):
            qs = qs.filter(number__gte=entry["verse_start"])  # if only one verse, verse_end will equal start
        if entry.get("verse_end"):
            qs = qs.filter(number__lte=entry["verse_end"])  # limited to chapter in this MVP

        qs = qs.select_related("book", "version").order_by("book__canonical_order", "chapter", "number")

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
        tags=["verses"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(name="ref", description="Range reference (e.g., 'Jo 3:16-18')", required=True),
            OpenApiParameter(name="version", description="Version code or id (optional)"),
        ],
        responses={200: VerseSerializer(many=True), **get_error_responses()},
        examples=[
            OpenApiExample("Cross-chapter range", value={"ref": "Jo 1:31-2:3"}, request_only=True),
            OpenApiExample("Chapter range", value={"ref": "Jo 1-3"}, request_only=True),
        ],
    )
    def get(self, request, *args, **kwargs):
        mark_response_language_sensitive(request)
        ref = request.query_params.get("ref", "").strip()
        if not ref:
            return Response({"detail": "Query parameter 'ref' is required", "code": "validation_error"}, status=400)
        if len(ref) > 200:
            return Response({"detail": "Payload too large", "code": "payload_too_large"}, status=413)

        lang = getattr(request, "lang_code", "en")
        parsed = _parse_reference_string(ref)
        if not parsed["items"]:
            return Response({"detail": "Unable to parse reference", "code": "validation_error"}, status=400)
        entry = parsed["items"][0]

        book = resolve_book_by_alias(entry.get("book_raw"), lang) or None
        if book is None:
            try:
                book = get_canonical_book_by_name(entry.get("book_raw"))
            except Exception:
                book = None
        if book is None:
            return Response({"detail": "Book not found", "code": "not_found"}, status=404)

        start_ch = entry.get("chapter")
        start_v = entry.get("verse_start")
        end_ch = entry.get("chapter_end") or start_ch
        end_v = entry.get("verse_end")
        if start_ch is None:
            return Response({"detail": "Range requires chapter", "code": "validation_error"}, status=400)
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
            return Response({"detail": "Range too large (max 300 verses)", "code": "payload_too_large"}, status=413)

        serializer = VerseSerializer(
            qs.select_related("book", "version").order_by("book__canonical_order", "chapter", "number"), many=True
        )
        return Response(serializer.data)


class VersesCompareView(LanguageSensitiveMixin, APIView):
    @extend_schema(
        summary="Compare verse across versions",
        tags=["verses"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(name="ref", description="Reference string (e.g., 'Jo 3:16')", required=True),
            OpenApiParameter(
                name="versions", description="Comma-separated version codes/ids (e.g., 'KJV,NVI,ARA')", required=True
            ),
        ],
        responses={200: VerseSerializer(many=True), **get_error_responses()},
        examples=[
            OpenApiExample(
                "Compare across versions", value={"ref": "Jo 3:16", "versions": "KJV,NVI,ARA"}, request_only=True
            ),
        ],
    )
    def get(self, request):
        mark_response_language_sensitive(request)
        ref = request.query_params.get("ref", "").strip()
        versions_param = request.query_params.get("versions", "").strip()
        if not ref or not versions_param:
            return Response(
                {"detail": "Parameters 'ref' and 'versions' are required", "code": "validation_error"}, status=400
            )
        versions_list = [v.strip() for v in versions_param.split(",") if v.strip()]
        if len(versions_list) > 5:
            return Response(
                {"detail": "Too many versions (max 5)", "code": "payload_too_large"},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )
        lang = getattr(request, "lang_code", "en")

        parsed = _parse_reference_string(ref)
        if not parsed["items"]:
            return Response({"detail": "Unable to parse reference", "code": "validation_error"}, status=400)
        entry = parsed["items"][0]
        book = resolve_book_by_alias(entry.get("book_raw"), lang) or None
        if book is None:
            try:
                book = get_canonical_book_by_name(entry.get("book_raw"))
            except Exception:
                book = None
        if book is None:
            return Response({"detail": "Book not found", "code": "not_found"}, status=404)

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
            verses = VerseSerializer(qs.select_related("book", "version").order_by("number"), many=True).data
            results.append(
                {
                    "version": v_obj.code,
                    "abbreviation": v_obj.abbreviation,
                    "language": getattr(v_obj.language, "code", None),
                    "verses": verses,
                }
            )

        return Response({"results": results})
