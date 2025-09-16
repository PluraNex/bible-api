"""Views for References domain (T-006). Minimal functional implementation."""
import re

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bible.utils import get_book_display_name, get_canonical_book_by_name
from bible.utils.i18n import mark_response_language_sensitive
from common.exceptions import ValidationError as APIValidationError
from common.openapi import get_error_responses

from .serializers import (
    ReferenceNormalizeRequestSerializer,
    ReferenceNormalizeResponseSerializer,
    ReferenceParseResponseSerializer,
    ReferenceResolveRequestSerializer,
    ReferenceResolveResponseSerializer,
)
from .services import resolve_book_by_alias

_SEGMENT_SPLIT_RE = re.compile(r"[;\uFF1B]+")  # semicolon, fullwidth semicolon
_REF_RE = re.compile(
    r"^\s*(?P<book>[1-3]?\s?[A-Za-zÀ-ÿ\.]+)\s+"  # book (with optional leading ordinal)
    r"(?P<chapter>\d+)?"  # optional start chapter
    r"(?::(?P<v1>\d+))?"  # optional start verse
    r"(?:-(?:(?P<chapter2>\d+):)?(?P<v2>\d+))?\s*$",  # optional -[end_chapter:]end_verse
    flags=re.IGNORECASE,
)


def _parse_reference_string(q: str) -> dict:
    items: list[dict] = []
    warnings: list[str] = []
    if not q or not q.strip():
        return {"input": q or "", "items": items, "warnings": ["empty_query"]}

    for raw_segment in _SEGMENT_SPLIT_RE.split(q):
        segment = raw_segment.strip()
        if not segment:
            continue
        m = _REF_RE.match(segment)
        if not m:
            warnings.append(f"unparsed_segment:{segment}")
            items.append({"raw": segment, "parsed": False})
            continue

        book = m.group("book")
        chapter = m.group("chapter")
        v1 = m.group("v1")
        v2 = m.group("v2")
        ch2 = m.group("chapter2")
        entry: dict = {"raw": segment, "parsed": True, "book_raw": book}
        if chapter:
            entry["chapter"] = int(chapter)
        if v1:
            entry["verse_start"] = int(v1)
        if v2:
            entry["verse_end"] = int(v2)
        elif v1:
            entry["verse_end"] = int(v1)
        if ch2:
            entry["chapter_end"] = int(ch2)
        # If no colon present at all and we matched a dash number as v2, treat it as chapter_end
        if ":" not in segment and entry.get("chapter") is not None and "verse_start" not in entry:
            if "verse_end" in entry:
                entry["chapter_end"] = entry.pop("verse_end")
        items.append(entry)

    return {"input": q, "items": items, "warnings": warnings}


class ReferenceParseView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "search"

    @extend_schema(
        summary="Parse free-text Bible references",
        parameters=[OpenApiParameter(name="q", required=True, type=str)],
        responses={200: ReferenceParseResponseSerializer, **get_error_responses()},
        tags=["references"],
    )
    def get(self, request):
        q = request.query_params.get("q", "")
        if not q:
            raise APIValidationError("Query parameter 'q' is required")
        if len(q) > 500:
            return Response(
                {"detail": "Payload too large", "code": "payload_too_large"},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )
        result = _parse_reference_string(q)
        return Response(result, status=status.HTTP_200_OK)


class ReferenceResolveView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "search"

    @extend_schema(
        summary="Resolve references into canonical structures",
        request=ReferenceResolveRequestSerializer,
        responses={200: ReferenceResolveResponseSerializer, **get_error_responses()},
        tags=["references"],
    )
    def post(self, request):
        payload = ReferenceResolveRequestSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        items = payload.validated_data["items"]
        if len(items) > 50:
            return Response(
                {"detail": "Too many items (max 50)", "code": "payload_too_large"},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        # mark language-sensitive for display names (if any)
        mark_response_language_sensitive(request)
        lang = request.query_params.get("lang") or getattr(request, "lang_code", "en")

        results: list[dict] = []
        for s in items:
            parsed = _parse_reference_string(s)
            if not parsed["items"]:
                results.append({"input": s, "error": "unparsed"})
                continue
            # resolve per parsed item
            for entry in parsed["items"]:
                book_raw = entry.get("book_raw")
                book = resolve_book_by_alias(book_raw, lang) or None
                if book is None:
                    # Fallback to global resolver (any language) as last resort
                    try:
                        book = get_canonical_book_by_name(book_raw)
                    except Exception:
                        book = None
                if book is None:
                    results.append({"input": s, "raw": entry.get("raw"), "error": "book_not_found"})
                    continue
                result_item = {
                    "input": s,
                    "book": {
                        "osis_code": book.osis_code,
                        "display_name": get_book_display_name(book, lang),
                    },
                    "chapter": entry.get("chapter"),
                    "verse_start": entry.get("verse_start"),
                    "verse_end": entry.get("verse_end"),
                }
                results.append(result_item)

        return Response({"results": results}, status=status.HTTP_200_OK)


class ReferenceNormalizeView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "search"

    @extend_schema(
        summary="Normalize book names/abbreviations",
        request=ReferenceNormalizeRequestSerializer,
        responses={200: ReferenceNormalizeResponseSerializer, **get_error_responses()},
        tags=["references"],
    )
    def post(self, request):
        payload = ReferenceNormalizeRequestSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        items = payload.validated_data["items"]
        if len(items) > 100:
            return Response(
                {"detail": "Too many items (max 100)", "code": "payload_too_large"},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        mark_response_language_sensitive(request)
        lang = request.query_params.get("lang") or getattr(request, "lang_code", "en")

        normalized: list[dict] = []
        for s in items:
            seg = s.strip()
            m = _REF_RE.match(seg)
            book_raw = seg
            if m:
                book_raw = m.group("book")
            book = resolve_book_by_alias(book_raw, lang) or None
            if book is None:
                try:
                    book = get_canonical_book_by_name(book_raw)
                except Exception:
                    book = None
            if book is None:
                normalized.append({"input": s, "book_raw": book_raw, "error": "book_not_found"})
            else:
                normalized.append(
                    {
                        "input": s,
                        "book_raw": book_raw,
                        "normalized_book": book.osis_code,
                        "display_name": get_book_display_name(book, lang),
                    }
                )

        return Response({"normalized": normalized}, status=status.HTTP_200_OK)
