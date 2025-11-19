"""Views for books domain."""

from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import filters, generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import build_error_response
from common.mixins import LanguageSensitiveMixin
from common.openapi import LANG_PARAMETER, get_error_responses
from common.pagination import StandardResultsSetPagination

from ..models import BookCategory, BookName, CanonicalBook, Testament, Theme, Verse
from ..shared_serializers import BookCategorySerializer, TestamentSerializer
from ..utils import get_book_display_name, get_canonical_book_by_name
from .filters import BookFilter
from .serializers import (
    BookAliasSerializer,
    BookCanonResultSerializer,
    BookChapterVersesSerializer,
    # Phase 2 serializers
    BookNeighborsSerializer,
    BookRangeSerializer,
    BookResolveResultSerializer,
    BookRestrictedSearchSerializer,
    BookSearchResultSerializer,
    BookSectionDetailSerializer,
    BookSectionSerializer,
    BookSerializer,
)


class BookListView(LanguageSensitiveMixin, generics.ListAPIView):
    serializer_class = BookSerializer
    filterset_class = BookFilter
    pagination_class = StandardResultsSetPagination
    permission_classes = [AllowAny]  # Public endpoint for development

    def get_queryset(self):
        """Otimizar queries com select_related e prefetch_related."""
        return (
            CanonicalBook.objects.select_related("testament")
            .prefetch_related("names", "names__language")
            .order_by("canonical_order")
        )

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["osis_code", "names__name", "names__abbreviation"]
    ordering_fields = ["canonical_order", "chapter_count"]
    ordering = ["canonical_order"]

    @extend_schema(
        summary="List books",
        tags=["books"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(name="testament", description="Filter by testament code (old/new)"),
            OpenApiParameter(name="testament_id", description="Filter by testament ID"),
            OpenApiParameter(name="category", description="Filter by book category ID"),
            OpenApiParameter(name="category_name", description="Filter by category name"),
            OpenApiParameter(name="is_deuterocanonical", description="Filter by deuterocanonical books"),
            OpenApiParameter(name="osis_code", description="Filter by OSIS code"),
            OpenApiParameter(name="name", description="Search by book name in any language"),
            OpenApiParameter(name="chapter_count_min", description="Minimum number of chapters"),
            OpenApiParameter(name="chapter_count_max", description="Maximum number of chapters"),
            OpenApiParameter(name="search", description="Search in book names and abbreviations"),
            OpenApiParameter(name="ordering", description="Order results by: canonical_order, chapter_count"),
        ],
        responses={
            200: BookSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get_serializer_context(self):
        """Add request context for language resolution."""
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class BookInfoView(LanguageSensitiveMixin, APIView):
    permission_classes = [AllowAny]  # Public endpoint for development

    @extend_schema(
        summary="Get book info",
        description="Retrieve detailed information about a specific book including names, testament, and structure.",
        tags=["books"],
        parameters=[LANG_PARAMETER],
        responses={
            200: BookSerializer,
            **get_error_responses(),
        },
        examples=[
            OpenApiExample("Get book info", value={"book_name": "John"}, request_only=True),
            OpenApiExample(
                "Get book info with Portuguese localization",
                value={"book_name": "João", "lang": "pt-BR"},
                request_only=True,
            ),
        ],
    )
    def get(self, request, book_name):
        try:
            book = get_canonical_book_by_name(book_name)
            serializer = BookSerializer(book, context={"request": request})
            response = Response(serializer.data, status=status.HTTP_200_OK)
            return response
        except Exception:
            return build_error_response(
                "Book not found",
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )


class ChaptersByBookView(LanguageSensitiveMixin, APIView):
    permission_classes = [AllowAny]  # Public endpoint for development

    @extend_schema(
        summary="List chapters by book",
        description="Get the list of all chapter numbers available for a specific book.",
        tags=["books"],
        parameters=[LANG_PARAMETER],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "book": {"type": "string", "description": "Localized book name"},
                    "chapters": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of chapter numbers",
                    },
                },
            },
            **get_error_responses(),
        },
        examples=[
            OpenApiExample("Get chapters for John", value={"book_name": "John"}, request_only=True),
        ],
    )
    def get(self, request, book_name):
        try:
            book = get_canonical_book_by_name(book_name)
            chapters = list(range(1, book.chapter_count + 1))
            display_name = get_book_display_name(book, request.lang_code)
            response = Response({"book": display_name, "chapters": chapters}, status=status.HTTP_200_OK)
            return response
        except Exception:
            return build_error_response(
                "Book not found",
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )


class BooksByAuthorView(LanguageSensitiveMixin, APIView):
    @extend_schema(
        summary="List books by author",
        tags=["books"],
        responses={
            200: BookSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get(self, request, author_name):
        # TODO: Implementar a lógica para buscar livros por autor
        # Esta é uma implementação temporária que retorna uma resposta 501 Not Implemented
        return build_error_response(
            "Not implemented",
            "not_implemented",
            status.HTTP_501_NOT_IMPLEMENTED,
            request=request,
            vary_accept_language=True,
        )


class BooksByTestamentView(LanguageSensitiveMixin, generics.ListAPIView):
    permission_classes = [AllowAny]  # Public endpoint for development
    serializer_class = BookSerializer
    pagination_class = StandardResultsSetPagination

    @extend_schema(
        summary="List books by testament",
        description="Retrieve all books belonging to a specific testament (old or new).",
        tags=["books"],
        parameters=[LANG_PARAMETER],
        responses={
            200: BookSerializer(many=True),
            **get_error_responses(),
        },
        examples=[
            OpenApiExample("Get Old Testament books", value={"testament_id": 1}, request_only=True),
            OpenApiExample("Get New Testament books", value={"testament_id": 2}, request_only=True),
        ],
    )
    def get_serializer_context(self):
        """Add request context for language resolution."""
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_queryset(self):
        testament_id = self.kwargs["testament_id"]
        return (
            CanonicalBook.objects.filter(testament_id=testament_id)
            .select_related("testament")
            .prefetch_related("names", "names__language")
            .order_by("canonical_order")
        )


class BookOutlineView(LanguageSensitiveMixin, APIView):
    @extend_schema(
        summary="Get book outline",
        tags=["books"],
        parameters=[LANG_PARAMETER],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "book": {"type": "string"},
                    "outline": {"type": "string"},
                },
            },
            **get_error_responses(),
        },
    )
    def get(self, request, book_name):
        try:
            book = get_canonical_book_by_name(book_name)
            display_name = get_book_display_name(book, request.lang_code)

            # Gerar um outline básico baseado nos capítulos do livro
            outline = f"Outline of {display_name}\n\n"
            for i in range(1, book.chapter_count + 1):
                outline += f"Chapter {i}\n"

            response = Response({"book": display_name, "outline": outline}, status=status.HTTP_200_OK)
            return response
        except Exception:
            return build_error_response(
                "Book not found",
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )


class BookContextView(LanguageSensitiveMixin, APIView):
    @extend_schema(
        summary="Get book context",
        tags=["books"],
        parameters=[LANG_PARAMETER],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "book": {"type": "string"},
                    "context": {"type": "string"},
                },
            },
            **get_error_responses(),
        },
    )
    def get(self, request, book_name):
        try:
            book = get_canonical_book_by_name(book_name)
            display_name = get_book_display_name(book, request.lang_code)

            # Gerar contexto básico do livro
            testament_name = book.testament.name if book.testament else "Unknown"
            context = f"{display_name} is a {testament_name.lower()} book with {book.chapter_count} chapters."

            # Adicionar informações sobre o testamento
            if testament_name == "Old Testament":
                context += " It is part of the Old Testament, written before the birth of Jesus Christ."
            elif testament_name == "New Testament":
                context += " It is part of the New Testament, written after the birth of Jesus Christ."

            # Se for deuterocanônico
            if book.is_deuterocanonical:
                context += " This book is considered deuterocanonical."

            response = Response({"book": display_name, "context": context}, status=status.HTTP_200_OK)
            return response
        except Exception:
            return build_error_response(
                "Book not found",
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )


class BookStructureView(LanguageSensitiveMixin, APIView):
    @extend_schema(
        summary="Get book structure",
        tags=["books"],
        parameters=[LANG_PARAMETER],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "book": {"type": "string"},
                    "structure": {"type": "string"},
                },
            },
            **get_error_responses(),
        },
    )
    def get(self, request, book_name):
        try:
            book = get_canonical_book_by_name(book_name)
            display_name = get_book_display_name(book, request.lang_code)

            # Gerar estrutura básica do livro
            structure = f"Structure of {display_name}\n\n"
            structure += f"Total Chapters: {book.chapter_count}\n"
            structure += f"Canonical Order: {book.canonical_order}\n"
            structure += f"Testament: {book.testament.name if book.testament else 'Unknown'}\n"

            # Estimar número de versos (simplificado)
            total_verses = Verse.objects.filter(book=book).count()
            structure += f"Approximate Total Verses: {total_verses}\n"

            # Se for deuterocanônico
            if book.is_deuterocanonical:
                structure += "Deuterocanonical: Yes\n"

            response = Response({"book": display_name, "structure": structure}, status=status.HTTP_200_OK)
            return response
        except Exception:
            return build_error_response(
                "Book not found",
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )


class BookStatisticsView(LanguageSensitiveMixin, APIView):
    @extend_schema(
        summary="Get book statistics",
        tags=["books"],
        parameters=[LANG_PARAMETER],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "book": {"type": "string"},
                    "statistics": {"type": "object"},
                },
            },
            **get_error_responses(),
        },
    )
    def get(self, request, book_name):
        try:
            book = get_canonical_book_by_name(book_name)
            display_name = get_book_display_name(book, request.lang_code)

            # Calcular estatísticas do livro
            total_verses = Verse.objects.filter(book=book).count()
            total_themes = Theme.objects.filter(verse_links__verse__book=book).distinct().count()

            # Calcular estatísticas por capítulo
            chapters_data = []
            for i in range(1, book.chapter_count + 1):
                chapter_verses = Verse.objects.filter(book=book, chapter=i).count()
                chapters_data.append({"chapter": i, "verse_count": chapter_verses})

            statistics = {
                "total_verses": total_verses,
                "total_chapters": book.chapter_count,
                "total_themes": total_themes,
                "chapters": chapters_data,
                "testament": book.testament.name if book.testament else "Unknown",
                "is_deuterocanonical": book.is_deuterocanonical,
            }

            response = Response({"book": display_name, "statistics": statistics}, status=status.HTTP_200_OK)
            return response
        except Exception:
            return build_error_response(
                "Book not found",
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )


# Phase 1: Discovery/Normalization Endpoints


class BookSearchView(LanguageSensitiveMixin, generics.GenericAPIView):
    permission_classes = [AllowAny]  # Public endpoint for development
    serializer_class = BookSearchResultSerializer
    pagination_class = StandardResultsSetPagination
    """Search books by name, OSIS code, or aliases with multilingual support."""

    @extend_schema(
        summary="Search books",
        description="""Search books by name, OSIS code, abbreviation, or aliases across all languages.

        Language precedence: 'lang' parameter > 'language' parameter (for filtering) > Accept-Language header > 'en' default.
        The 'language' parameter filters results to specific language codes, while 'lang' affects localized names in responses.""",
        tags=["books"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(
                name="q", description="Search query for book name, OSIS code, or abbreviation", required=True, type=str
            ),
            OpenApiParameter(
                name="language",
                description="Filter results by specific language code (e.g., 'en', 'pt'). Kept for backward compatibility.",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="page_size",
                description="Number of results per page (default: 20, max: 100)",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="limit",
                description="Deprecated alias for page_size (will be removed in v2)",
                required=False,
                type=int,
                deprecated=True,
            ),
        ],
        responses={
            200: BookSearchResultSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        query = request.query_params.get("q", "").strip()
        if not query:
            return build_error_response(
                'Query parameter "q" is required.',
                "validation_error",
                status.HTTP_400_BAD_REQUEST,
                request=request,
                vary_accept_language=True,
            )

        # Language filter precedence: 'language' param for filtering (backward compatibility)
        language_filter = request.query_params.get("language", "").strip()
        # If no explicit 'language' filter but a 'lang' param is provided, default
        # the search to that language to improve i18n relevance
        if not language_filter and "lang" in request.query_params:
            language_filter = getattr(request, "lang_code", "").strip()
        search_results = []

        # 1. Search by OSIS code first (exact match has highest priority)
        try:
            osis_book = (
                CanonicalBook.objects.select_related("testament").prefetch_related("names").get(osis_code__iexact=query)
            )
            search_results.append(self._format_search_result(osis_book, query, "osis", "canonical"))
        except CanonicalBook.DoesNotExist:
            pass

        # 2. Search by name and abbreviation in BookName model
        name_query = Q(name__icontains=query) | Q(abbreviation__iexact=query)
        if language_filter:
            name_query &= Q(language__code=language_filter)

        book_names = (
            BookName.objects.filter(name_query)
            .select_related("canonical_book__testament", "language", "version")
            .order_by("canonical_book__canonical_order")
        )

        # Track books already added to avoid duplicates
        added_books = {result["osis_code"] for result in search_results}

        for book_name in book_names:
            if book_name.canonical_book.osis_code not in added_books:
                match_type = (
                    "abbreviation"
                    if book_name.abbreviation and book_name.abbreviation.lower() == query.lower()
                    else "name"
                )
                search_results.append(
                    self._format_search_result(book_name.canonical_book, query, match_type, book_name.language.code)
                )
                added_books.add(book_name.canonical_book.osis_code)

        if not search_results:
            return build_error_response(
                f'No books found matching "{query}".',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )

        page = self.paginate_queryset(search_results)
        serializer = self.get_serializer(page if page is not None else search_results, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    def _format_search_result(self, book, query, match_type, language):
        """Format a book into search result format."""
        # Get all aliases for this book
        aliases = []
        for book_name in book.names.all():
            if book_name.name:
                aliases.append(book_name.name)
            if book_name.abbreviation:
                aliases.append(book_name.abbreviation)

        # Remove duplicates and the primary name
        # Get request from context or default to English
        request_context = getattr(self, "request", None)
        lang_code = request_context.lang_code if request_context else "en"
        primary_name = get_book_display_name(book, (lang_code if language == "canonical" else language))
        aliases = list(set(aliases))
        if primary_name in aliases:
            aliases.remove(primary_name)

        return {
            "osis_code": book.osis_code,
            "name": primary_name,
            "aliases": aliases,
            "canonical_order": book.canonical_order,
            "testament": book.testament.name if book.testament else "Unknown",
            "is_deuterocanonical": book.is_deuterocanonical,
            "chapter_count": book.chapter_count,
            "match_type": match_type,
            "language": language,
        }


class BookAliasesView(LanguageSensitiveMixin, APIView):
    """Get comprehensive mapping of book names and aliases by language."""

    @extend_schema(
        summary="Get book aliases",
        description="""Get comprehensive mapping of all book names and aliases organized by language.

        Note: The 'canonical_name' field uses the language specified by the 'lang' parameter for localization.
        All other alias data shows names as they exist in each respective language/version.""",
        tags=["books"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(
                name="language",
                description="Filter aliases by specific language code (e.g., 'en', 'pt')",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="book", description="Filter aliases for specific book (OSIS code)", required=False, type=str
            ),
        ],
        responses={
            200: BookAliasSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        language_filter = request.query_params.get("language", "").strip()
        book_filter = request.query_params.get("book", "").strip()

        # Base query for canonical books
        books_query = (
            CanonicalBook.objects.select_related("testament")
            .prefetch_related("names__language", "names__version")
            .order_by("canonical_order")
        )

        # Filter by specific book if requested
        if book_filter:
            books_query = books_query.filter(osis_code__iexact=book_filter)

        books = books_query.all()
        if not books:
            return build_error_response(
                "No books found.",
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )

        results = []
        for book in books:
            # Get canonical name (request language default)
            canonical_name = get_book_display_name(book, request.lang_code)

            # Collect all aliases
            aliases_data = []
            book_names = book.names.all()

            # Filter by language if specified
            if language_filter:
                book_names = book_names.filter(language__code=language_filter)

            for book_name in book_names:
                alias_entry = {
                    "language": book_name.language.code,
                    "language_name": book_name.language.name,
                    "name": book_name.name,
                    "abbreviation": book_name.abbreviation,
                    "version": book_name.version.code if book_name.version else None,
                    "version_name": book_name.version.name if book_name.version else None,
                }
                aliases_data.append(alias_entry)

            # Sort aliases by language, then by version
            aliases_data.sort(key=lambda x: (x["language"], x["version"] or ""))

            result = {
                "osis_code": book.osis_code,
                "canonical_name": canonical_name,
                "aliases": aliases_data,
                "testament": book.testament.name if book.testament else "Unknown",
                "canonical_order": book.canonical_order,
            }
            results.append(result)

        serializer = BookAliasSerializer(results, many=True)
        return Response(serializer.data)


class BookResolveView(LanguageSensitiveMixin, APIView):
    """Normalize any book identifier (OSIS, name, abbreviation) to canonical format."""

    @extend_schema(
        summary="Resolve book identifier",
        description="""Normalize any book identifier (OSIS code, name, abbreviation, or alias) to canonical format.

        The 'canonical_name' in the response uses the language specified by the 'lang' parameter (defaults to English).
        The 'aliases' array shows all available names in their respective languages/versions.""",
        tags=["books"],
        parameters=[LANG_PARAMETER],
        responses={
            200: BookResolveResultSerializer,
            **get_error_responses(),
        },
    )
    def get(self, request, identifier, *args, **kwargs):
        if not identifier or not identifier.strip():
            return build_error_response(
                "Book identifier is required.",
                "validation_error",
                status.HTTP_400_BAD_REQUEST,
                request=request,
                vary_accept_language=True,
            )

        identifier = identifier.strip()
        book = None
        resolution_type = None

        # Try multiple resolution strategies

        # 1. Try exact OSIS code match
        try:
            book = (
                CanonicalBook.objects.select_related("testament")
                .prefetch_related("names__language", "names__version")
                .get(osis_code__iexact=identifier)
            )
            resolution_type = "osis_exact"
        except CanonicalBook.DoesNotExist:
            pass

        # 2. Try name/abbreviation match via BookName
        if not book:
            book_name = (
                BookName.objects.filter(Q(name__iexact=identifier) | Q(abbreviation__iexact=identifier))
                .select_related("canonical_book__testament")
                .prefetch_related("canonical_book__names__language", "canonical_book__names__version")
                .first()
            )

            if book_name:
                book = book_name.canonical_book
                resolution_type = (
                    "name_exact"
                    if book_name.name and book_name.name.lower() == identifier.lower()
                    else "abbreviation_exact"
                )

        # 3. Try partial name match (case-insensitive contains)
        if not book:
            book_name = (
                BookName.objects.filter(name__icontains=identifier)
                .select_related("canonical_book__testament")
                .prefetch_related("canonical_book__names__language", "canonical_book__names__version")
                .order_by("canonical_book__canonical_order")
                .first()
            )

            if book_name:
                book = book_name.canonical_book
                resolution_type = "name_partial"

        if not book:
            return build_error_response(
                f'Book identifier "{identifier}" could not be resolved.',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )

        # Format response
        canonical_name = get_book_display_name(book, request.lang_code)

        # Get all aliases organized by language
        aliases_by_language = {}
        for book_name in book.names.all():
            lang_code = book_name.language.code
            if lang_code not in aliases_by_language:
                aliases_by_language[lang_code] = {
                    "language": lang_code,
                    "language_name": book_name.language.name,
                    "names": [],
                    "abbreviations": [],
                }

            if book_name.name:
                aliases_by_language[lang_code]["names"].append(book_name.name)
            if book_name.abbreviation:
                aliases_by_language[lang_code]["abbreviations"].append(book_name.abbreviation)

        # Convert to list and remove duplicates
        aliases = []
        for lang_data in aliases_by_language.values():
            lang_data["names"] = list(set(lang_data["names"]))
            lang_data["abbreviations"] = list(set(lang_data["abbreviations"]))
            aliases.append(lang_data)

        # Sort by language code
        aliases.sort(key=lambda x: x["language"])

        result_data = {
            "osis_code": book.osis_code,
            "canonical_name": canonical_name,
            "aliases": aliases,
            "canonical_order": book.canonical_order,
            "testament": book.testament.name if book.testament else "Unknown",
            "is_deuterocanonical": book.is_deuterocanonical,
            "chapter_count": book.chapter_count,
            "resolved_from": identifier,
            "resolution_type": resolution_type,
        }

        serializer = BookResolveResultSerializer(data=result_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class BookCanonView(LanguageSensitiveMixin, APIView):
    """Get books filtered by canonical tradition (Protestant, Catholic, Orthodox, etc.)."""

    # Define canonical traditions and their rules
    CANON_TRADITIONS = {
        "protestant": {
            "name": "Protestant Canon",
            "description": "Standard Protestant Bible (66 books)",
            "include_deuterocanonical": False,
            "books": None,  # All non-deuterocanonical books
        },
        "catholic": {
            "name": "Catholic Canon",
            "description": "Roman Catholic Bible (73 books)",
            "include_deuterocanonical": True,
            "books": None,  # All books
        },
        "orthodox": {
            "name": "Eastern Orthodox Canon",
            "description": "Eastern Orthodox Bible (varies by tradition)",
            "include_deuterocanonical": True,
            "books": None,  # All books (could be refined with specific Orthodox books)
        },
        "lxx": {
            "name": "Septuagint (LXX)",
            "description": "Greek translation of Hebrew Bible with additional books",
            "include_deuterocanonical": True,
            "books": None,  # All books (primarily OT focus)
        },
    }

    @extend_schema(
        summary="List books by canonical tradition",
        description="Get books filtered by canonical tradition (protestant, catholic, orthodox, lxx)",
        tags=["books"],
        responses={
            200: BookCanonResultSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get(self, request, tradition, *args, **kwargs):
        tradition = tradition.lower().strip()

        if tradition not in self.CANON_TRADITIONS:
            available_traditions = ", ".join(self.CANON_TRADITIONS.keys())
            return build_error_response(
                f'Invalid canonical tradition "{tradition}". Available options: {available_traditions}',
                "validation_error",
                status.HTTP_400_BAD_REQUEST,
                request=request,
                vary_accept_language=True,
                errors={"available_traditions": list(self.CANON_TRADITIONS.keys())},
            )

        tradition_config = self.CANON_TRADITIONS[tradition]

        # Build query based on tradition rules
        books_query = (
            CanonicalBook.objects.select_related("testament")
            .prefetch_related("names__language")
            .order_by("canonical_order")
        )

        # Apply deuterocanonical filter
        if not tradition_config["include_deuterocanonical"]:
            books_query = books_query.filter(is_deuterocanonical=False)

        # For LXX, focus primarily on Old Testament + deuterocanonical
        if tradition == "lxx":
            books_query = books_query.filter(testament__name__icontains="old")

        books = books_query.all()

        if not books:
            return build_error_response(
                f'No books found for tradition "{tradition}".',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )

        # Format results
        results = []
        for book in books:
            canonical_name = get_book_display_name(book, request.lang_code)

            # Determine inclusion reason
            inclusion_reason = self._get_inclusion_reason(book, tradition, tradition_config)

            result = {
                "osis_code": book.osis_code,
                "name": canonical_name,
                "canonical_order": book.canonical_order,
                "testament": book.testament.name if book.testament else "Unknown",
                "is_deuterocanonical": book.is_deuterocanonical,
                "chapter_count": book.chapter_count,
                "inclusion_reason": inclusion_reason,
            }
            results.append(result)

        serializer = BookCanonResultSerializer(results, many=True)
        return Response(serializer.data)

    def _get_inclusion_reason(self, book, tradition, tradition_config):
        """Determine why a book is included in the specified tradition."""
        if tradition == "protestant":
            return "Part of the standard Protestant 66-book canon"
        elif tradition == "catholic":
            if book.is_deuterocanonical:
                return "Deuterocanonical book accepted by Catholic Church"
            else:
                return "Part of the standard Christian canon accepted by all traditions"
        elif tradition == "orthodox":
            if book.is_deuterocanonical:
                return "Deuterocanonical book accepted by Eastern Orthodox traditions"
            else:
                return "Part of the standard Christian canon"
        elif tradition == "lxx":
            if book.testament and "old" in book.testament.name.lower():
                if book.is_deuterocanonical:
                    return "Greek book included in the Septuagint translation"
                else:
                    return "Hebrew book translated in the Septuagint"
            else:
                return "Included in extended Septuagint collections"

        return "Included in this canonical tradition"


# Phase 2: Navigation/Structure Views


class BookNeighborsView(LanguageSensitiveMixin, APIView):
    """Get navigation information for a book (previous/next books)."""

    @extend_schema(
        summary="Get book navigation neighbors",
        description="Get previous and next books in canonical order for navigation purposes, including testament-specific neighbors.",
        tags=["books"],
        parameters=[LANG_PARAMETER],
        responses={
            200: BookNeighborsSerializer,
            **get_error_responses(),
        },
        examples=[
            OpenApiExample("Get navigation for John", value={"book_name": "John"}, request_only=True),
        ],
    )
    def get(self, request, book_name, *args, **kwargs):
        try:
            book = get_canonical_book_by_name(book_name)
        except Exception:
            return build_error_response(
                f'Book "{book_name}" not found.',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )

        # Get current book info
        current_name = get_book_display_name(book, request.lang_code)
        current_info = {
            "osis_code": book.osis_code,
            "name": current_name,
            "canonical_order": book.canonical_order,
            "testament": book.testament.name if book.testament else "Unknown",
            "chapter_count": book.chapter_count,
        }

        # Get previous book in canonical order
        previous_book = (
            CanonicalBook.objects.filter(canonical_order__lt=book.canonical_order).order_by("-canonical_order").first()
        )

        previous_info = None
        if previous_book:
            previous_name = get_book_display_name(previous_book, request.lang_code)
            previous_info = {
                "osis_code": previous_book.osis_code,
                "name": previous_name,
                "canonical_order": previous_book.canonical_order,
                "testament": previous_book.testament.name if previous_book.testament else "Unknown",
            }

        # Get next book in canonical order
        next_book = (
            CanonicalBook.objects.filter(canonical_order__gt=book.canonical_order).order_by("canonical_order").first()
        )

        next_info = None
        if next_book:
            next_name = get_book_display_name(next_book, request.lang_code)
            next_info = {
                "osis_code": next_book.osis_code,
                "name": next_name,
                "canonical_order": next_book.canonical_order,
                "testament": next_book.testament.name if next_book.testament else "Unknown",
            }

        # Get testament-specific neighbors
        testament_prev = (
            CanonicalBook.objects.filter(testament=book.testament, canonical_order__lt=book.canonical_order)
            .order_by("-canonical_order")
            .first()
        )

        testament_next = (
            CanonicalBook.objects.filter(testament=book.testament, canonical_order__gt=book.canonical_order)
            .order_by("canonical_order")
            .first()
        )

        testament_neighbors = {
            "previous": None,
            "next": None,
        }

        if testament_prev:
            prev_name = get_book_display_name(testament_prev, request.lang_code)
            testament_neighbors["previous"] = {
                "osis_code": testament_prev.osis_code,
                "name": prev_name,
                "canonical_order": testament_prev.canonical_order,
            }

        if testament_next:
            next_name = get_book_display_name(testament_next, request.lang_code)
            testament_neighbors["next"] = {
                "osis_code": testament_next.osis_code,
                "name": next_name,
                "canonical_order": testament_next.canonical_order,
            }

        result = {
            "current": current_info,
            "previous": previous_info,
            "next": next_info,
            "testament_neighbors": testament_neighbors,
        }

        serializer = BookNeighborsSerializer(result)
        return Response(serializer.data)


class BookSectionsView(LanguageSensitiveMixin, APIView):
    """List sections/perícopes for a book."""

    @extend_schema(
        summary="List book sections/perícopes",
        description="Get structural sections or perícopes for a book. Currently supports chapter-based sections.",
        tags=["books"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(
                name="type", description="Filter by section type: chapter (default), pericope, theme", required=False
            ),
        ],
        responses={
            200: BookSectionSerializer(many=True),
            **get_error_responses(),
        },
        examples=[
            OpenApiExample("Get chapters for John", value={"book_name": "John", "type": "chapter"}, request_only=True),
        ],
    )
    def get(self, request, book_name, *args, **kwargs):
        try:
            book = get_canonical_book_by_name(book_name)
        except Exception:
            return build_error_response(
                f'Book "{book_name}" not found.',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )

        section_type = request.query_params.get("type", "chapter")

        # For now, generate chapter-based sections as default
        # In a full implementation, this would come from outline_data or a separate model
        sections = []

        if section_type == "chapter":
            for chapter_num in range(1, book.chapter_count + 1):
                section = {
                    "id": chapter_num,
                    "title": f"Chapter {chapter_num}",
                    "description": f"Chapter {chapter_num} of {get_book_display_name(book, request.lang_code)}",
                    "start_chapter": chapter_num,
                    "start_verse": 1,
                    "end_chapter": chapter_num,
                    "end_verse": 999,  # Would be actual verse count in real implementation
                    "section_type": "chapter",
                }
                sections.append(section)

        elif section_type == "pericope":
            # This would come from outline_data or specialized pericope data
            # For now, return empty list as placeholder
            pass

        elif section_type == "theme":
            # This would integrate with theme data
            # For now, return empty list as placeholder
            pass

        serializer = BookSectionSerializer(sections, many=True)
        return Response(serializer.data)


class BookSectionDetailView(LanguageSensitiveMixin, APIView):
    """Get detailed information about a specific book section."""

    @extend_schema(
        summary="Get book section details",
        description="Get detailed information about a specific book section/perícope including verse ranges and context.",
        tags=["books"],
        parameters=[LANG_PARAMETER],
        responses={
            200: BookSectionDetailSerializer,
            **get_error_responses(),
        },
        examples=[
            OpenApiExample(
                "Get details for John chapter 3", value={"book_name": "John", "section_id": 3}, request_only=True
            ),
        ],
    )
    def get(self, request, book_name, section_id, *args, **kwargs):
        try:
            book = get_canonical_book_by_name(book_name)
        except Exception:
            return build_error_response(
                f'Book "{book_name}" not found.',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )

        try:
            section_id = int(section_id)
        except ValueError:
            return build_error_response(
                "Invalid section ID format.",
                "validation_error",
                status.HTTP_400_BAD_REQUEST,
                request=request,
                vary_accept_language=True,
            )

        # For now, assume chapter-based sections
        if section_id < 1 or section_id > book.chapter_count:
            return build_error_response(
                f'Section {section_id} not found in book "{book_name}".',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )

        book_display_name = get_book_display_name(book, request.lang_code)

        section_detail = {
            "id": section_id,
            "title": f"Chapter {section_id}",
            "description": f"Chapter {section_id} of {book_display_name}",
            "start_chapter": section_id,
            "start_verse": 1,
            "end_chapter": section_id,
            "end_verse": 999,  # Would be actual verse count
            "section_type": "chapter",
            "book_info": {
                "osis_code": book.osis_code,
                "name": book_display_name,
                "canonical_order": book.canonical_order,
                "testament": book.testament.name if book.testament else "Unknown",
            },
            "verse_range": f"{book_display_name} {section_id}:1-{section_id}:999",
            "context": None,  # Would include contextual information
        }

        serializer = BookSectionDetailSerializer(section_detail)
        return Response(serializer.data)


class BookRestrictedSearchView(LanguageSensitiveMixin, APIView):
    """Search for verses within a specific book."""

    @extend_schema(
        summary="Search within a specific book",
        description="Search for text within verses of a specific book. Returns matching verses with text previews and relevance scores.",
        tags=["books"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(name="q", description="Search query text", required=True),
            OpenApiParameter(
                name="version",
                description="Bible version code to search in (optional, searches all versions if not specified)",
                required=False,
            ),
            OpenApiParameter(
                name="limit", description="Maximum number of results to return (default: 20, max: 100)", required=False
            ),
        ],
        responses={
            200: BookRestrictedSearchSerializer(many=True),
            **get_error_responses(),
        },
        examples=[
            OpenApiExample("Search for 'love' in John", value={"book_name": "John", "q": "love"}, request_only=True),
            OpenApiExample(
                "Search for 'light' in John NIV",
                value={"book_name": "John", "q": "light", "version": "NIV"},
                request_only=True,
            ),
        ],
    )
    def get(self, request, book_name, *args, **kwargs):
        try:
            book = get_canonical_book_by_name(book_name)
        except Exception:
            return build_error_response(
                f'Book "{book_name}" not found.',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )

        query = request.query_params.get("q", "").strip()
        if not query:
            return build_error_response(
                'Search query "q" parameter is required.',
                "validation_error",
                status.HTTP_400_BAD_REQUEST,
                request=request,
                vary_accept_language=True,
            )

        version_code = request.query_params.get("version")
        limit = int(request.query_params.get("limit", 20))

        # Search verses in the book
        verses_query = Verse.objects.filter(book=book)

        if version_code:
            verses_query = verses_query.filter(version__code__iexact=version_code)

        # Basic text search
        verses_query = (
            verses_query.filter(text__icontains=query).select_related("version").order_by("chapter", "number")[:limit]
        )

        results = []
        for verse in verses_query:
            # Create text preview with highlighted search term
            text_preview = verse.text
            if len(text_preview) > 150:
                # Find query in text and create preview around it
                query_pos = text_preview.lower().find(query.lower())
                if query_pos >= 0:
                    start = max(0, query_pos - 75)
                    end = min(len(text_preview), query_pos + 75)
                    text_preview = text_preview[start:end]
                    if start > 0:
                        text_preview = "..." + text_preview
                    if end < len(verse.text):
                        text_preview = text_preview + "..."

            match_score = 1.0  # Would be calculated based on relevance
            book_display_name = get_book_display_name(book, request.lang_code)

            result = {
                "chapter": verse.chapter,
                "verse": verse.number,
                "text_preview": text_preview,
                "match_score": match_score,
                "verse_reference": f"{book_display_name} {verse.chapter}:{verse.number}",
            }
            results.append(result)

        serializer = BookRestrictedSearchSerializer(results, many=True)
        return Response(serializer.data)


class BookChapterVersesView(LanguageSensitiveMixin, APIView):
    """List all verses in a specific chapter of a book."""

    @extend_schema(
        summary="List verses in a book chapter",
        description="Get all verses for a specific chapter in a book with full text and metadata.",
        tags=["books"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(
                name="version",
                description="Bible version code to retrieve verses from (optional, uses first available if not specified)",
                required=False,
            ),
        ],
        responses={
            200: BookChapterVersesSerializer,
            **get_error_responses(),
        },
        examples=[
            OpenApiExample("Get all verses in John 3", value={"book_name": "John", "chapter": 3}, request_only=True),
            OpenApiExample(
                "Get John 3 in NIV version",
                value={"book_name": "John", "chapter": 3, "version": "NIV"},
                request_only=True,
            ),
        ],
    )
    def get(self, request, book_name, chapter, *args, **kwargs):
        try:
            book = get_canonical_book_by_name(book_name)
        except Exception:
            return build_error_response(
                f'Book "{book_name}" not found.',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )

        try:
            chapter = int(chapter)
        except ValueError:
            return build_error_response(
                "Invalid chapter number format.",
                "validation_error",
                status.HTTP_400_BAD_REQUEST,
                request=request,
                vary_accept_language=True,
            )

        if chapter < 1 or chapter > book.chapter_count:
            return build_error_response(
                f'Chapter {chapter} not found in book "{book_name}" (max: {book.chapter_count}).',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )

        version_code = request.query_params.get("version")

        # Get verses for the chapter
        verses_query = Verse.objects.filter(book=book, chapter=chapter)

        if version_code:
            verses_query = verses_query.filter(version__code__iexact=version_code)
        else:
            # Get first available version if not specified
            verses_query = verses_query.filter(version__isnull=False)

        verses = verses_query.select_related("version").order_by("number")

        if not verses:
            return build_error_response(
                f"No verses found for {book_name} {chapter}.",
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )

        # Format verse data
        verse_list = []
        for verse in verses:
            verse_data = {
                "number": verse.number,
                "text": verse.text,
                "reference": f"{get_book_display_name(book, request.lang_code)} {verse.chapter}:{verse.number}",
                "version": verse.version.code if verse.version else None,
            }
            verse_list.append(verse_data)

        result = {
            "chapter_number": chapter,
            "verse_count": len(verse_list),
            "verses": verse_list,
            "chapter_info": {
                "book": get_book_display_name(book, request.lang_code),
                "osis_code": book.osis_code,
                "testament": book.testament.name if book.testament else "Unknown",
                "canonical_order": book.canonical_order,
            },
        }

        serializer = BookChapterVersesSerializer(result)
        return Response(serializer.data)


class BookRangeView(LanguageSensitiveMixin, APIView):
    """Get verses for a specific range within a book."""

    @extend_schema(
        summary="Get verses for a book range",
        description="Get verses for a specific verse range within a book. Supports both single-chapter and cross-chapter ranges.",
        tags=["books"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(name="start_chapter", description="Starting chapter number", required=True, type=int),
            OpenApiParameter(name="start_verse", description="Starting verse number", required=True, type=int),
            OpenApiParameter(
                name="end_chapter",
                description="Ending chapter number (defaults to start_chapter if not provided)",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="end_verse",
                description="Ending verse number (defaults to start_verse if not provided)",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="version",
                description="Bible version code to retrieve verses from (optional, uses first available if not specified)",
                required=False,
            ),
        ],
        responses={
            200: BookRangeSerializer,
            **get_error_responses(),
        },
        examples=[
            OpenApiExample(
                "Get John 3:16-18",
                value={"book_name": "John", "start_chapter": 3, "start_verse": 16, "end_chapter": 3, "end_verse": 18},
                request_only=True,
            ),
            OpenApiExample(
                "Get cross-chapter range John 3:16-4:3",
                value={"book_name": "John", "start_chapter": 3, "start_verse": 16, "end_chapter": 4, "end_verse": 3},
                request_only=True,
            ),
        ],
    )
    def get(self, request, book_name, *args, **kwargs):
        try:
            book = get_canonical_book_by_name(book_name)
        except Exception:
            return build_error_response(
                f'Book "{book_name}" not found.',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )

        # Parse range parameters
        try:
            start_chapter = int(request.query_params.get("start_chapter"))
            start_verse = int(request.query_params.get("start_verse"))
            end_chapter = int(request.query_params.get("end_chapter", start_chapter))
            end_verse = int(request.query_params.get("end_verse", start_verse))
        except (ValueError, TypeError):
            return build_error_response(
                "Invalid range parameters. start_chapter and start_verse are required.",
                "validation_error",
                status.HTTP_400_BAD_REQUEST,
                request=request,
                vary_accept_language=True,
            )

        # Validate range
        if start_chapter < 1 or start_chapter > book.chapter_count:
            return build_error_response(
                f'Start chapter {start_chapter} is out of range for book "{book_name}".',
                "validation_error",
                status.HTTP_400_BAD_REQUEST,
                request=request,
                vary_accept_language=True,
            )

        if end_chapter < 1 or end_chapter > book.chapter_count:
            return build_error_response(
                f'End chapter {end_chapter} is out of range for book "{book_name}".',
                "validation_error",
                status.HTTP_400_BAD_REQUEST,
                request=request,
                vary_accept_language=True,
            )

        if start_chapter > end_chapter or (start_chapter == end_chapter and start_verse > end_verse):
            return build_error_response(
                "Invalid range: start must be before or equal to end.",
                "validation_error",
                status.HTTP_400_BAD_REQUEST,
                request=request,
                vary_accept_language=True,
            )

        version_code = request.query_params.get("version")

        # Build query for verse range
        verses_query = Verse.objects.filter(book=book)

        if version_code:
            verses_query = verses_query.filter(version__code__iexact=version_code)

        # Filter by range
        if start_chapter == end_chapter:
            # Single chapter range
            verses_query = verses_query.filter(chapter=start_chapter, number__gte=start_verse, number__lte=end_verse)
        else:
            # Multi-chapter range
            verses_query = verses_query.filter(
                Q(chapter=start_chapter, number__gte=start_verse)
                | Q(chapter__gt=start_chapter, chapter__lt=end_chapter)
                | Q(chapter=end_chapter, number__lte=end_verse)
            )

        verses = verses_query.select_related("version").order_by("chapter", "number")

        if not verses:
            return build_error_response(
                "No verses found for the specified range.",
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
                vary_accept_language=True,
            )

        # Format verse data
        verse_list = []
        for verse in verses:
            verse_data = {
                "chapter": verse.chapter,
                "verse": verse.number,
                "text": verse.text,
                "reference": f"{get_book_display_name(book, request.lang_code)} {verse.chapter}:{verse.number}",
                "version": verse.version.code if verse.version else None,
            }
            verse_list.append(verse_data)

        book_display_name = get_book_display_name(book, request.lang_code)
        start_ref = f"{book_display_name} {start_chapter}:{start_verse}"
        end_ref = f"{book_display_name} {end_chapter}:{end_verse}"

        result = {
            "book": book_display_name,
            "start_reference": start_ref,
            "end_reference": end_ref,
            "verse_count": len(verse_list),
            "verses": verse_list,
            "range_info": {
                "osis_code": book.osis_code,
                "testament": book.testament.name if book.testament else "Unknown",
                "canonical_order": book.canonical_order,
                "span_chapters": end_chapter - start_chapter + 1,
            },
        }

        serializer = BookRangeSerializer(result)
        return Response(serializer.data)


# New endpoints for frontend filters


class TestamentListView(LanguageSensitiveMixin, generics.ListAPIView):
    """List all testaments with localized names."""

    serializer_class = TestamentSerializer
    permission_classes = [AllowAny]
    queryset = Testament.objects.all().order_by("order")

    @extend_schema(
        summary="List testaments",
        description="Get all testaments (Old/New) with localized names and descriptions.",
        tags=["books"],
        parameters=[LANG_PARAMETER],
        responses={
            200: TestamentSerializer(many=True),
            **get_error_responses(),
        },
        examples=[
            OpenApiExample(
                "List testaments in Portuguese",
                value=[
                    {
                        "code": "old",
                        "name": "Antigo Testamento",
                        "description": "Livros escritos antes de Cristo",
                        "order": 1,
                    },
                    {
                        "code": "new",
                        "name": "Novo Testamento",
                        "description": "Livros escritos após Cristo",
                        "order": 2,
                    },
                ],
                response_only=True,
            ),
        ],
    )
    def get_serializer_context(self):
        """Add request context for language resolution."""
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class BookCategoryListView(LanguageSensitiveMixin, generics.ListAPIView):
    """List book categories, optionally filtered by testament."""

    serializer_class = BookCategorySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """Get categories with optional testament filter."""
        qs = BookCategory.objects.select_related("testament").order_by("testament__order", "order")
        testament_code = self.request.query_params.get("testament")

        if testament_code:
            # Filter by testament code (old/new)
            if testament_code.lower() == "old":
                qs = qs.filter(testament__name__icontains="old")
            elif testament_code.lower() == "new":
                qs = qs.filter(testament__name__icontains="new")

        return qs

    @extend_schema(
        summary="List book categories",
        description="Get all book categories (Pentateuch, Gospels, Epistles, etc.) with optional testament filter.",
        tags=["books"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(
                name="testament",
                description="Filter by testament code (old/new)",
                required=False,
                type=str,
            ),
        ],
        responses={
            200: BookCategorySerializer(many=True),
            **get_error_responses(),
        },
        examples=[
            OpenApiExample(
                "List all categories",
                summary="Get all book categories",
                response_only=True,
            ),
            OpenApiExample(
                "List Old Testament categories",
                value={"testament": "old"},
                request_only=True,
            ),
        ],
    )
    def get_serializer_context(self):
        """Add request context for language resolution."""
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
