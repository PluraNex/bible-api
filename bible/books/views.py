"""Views for books domain."""
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.mixins import LanguageSensitiveMixin
from common.openapi import LANG_PARAMETER, get_error_responses

from ..models import BookName, CanonicalBook, Theme, Verse
from ..utils import get_book_display_name, get_canonical_book_by_name
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
    queryset = CanonicalBook.objects.select_related("testament").prefetch_related("names").order_by("canonical_order")
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["testament", "is_deuterocanonical"]
    search_fields = ["osis_code", "names__name", "names__abbreviation"]
    ordering_fields = ["canonical_order", "chapter_count"]
    ordering = ["canonical_order"]

    @extend_schema(
        summary="List books",
        tags=["books"],
        parameters=[
            LANG_PARAMETER,
            OpenApiParameter(name="testament", description="Filter by testament ID"),
            OpenApiParameter(name="is_deuterocanonical", description="Filter by deuterocanonical books"),
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
    @extend_schema(
        summary="Get book info",
        tags=["books"],
        parameters=[LANG_PARAMETER],
        responses={
            200: BookSerializer,
            **get_error_responses(),
        },
    )
    def get(self, request, book_name):
        try:
            book = get_canonical_book_by_name(book_name)
            serializer = BookSerializer(book, context={"request": request})
            response = Response(serializer.data, status=status.HTTP_200_OK)
            return response
        except Exception:
            return Response({"detail": "Book not found"}, status=status.HTTP_404_NOT_FOUND)


class ChaptersByBookView(APIView):
    @extend_schema(
        summary="List chapters by book",
        tags=["books"],
        parameters=[LANG_PARAMETER],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "book": {"type": "string"},
                    "chapters": {"type": "array", "items": {"type": "integer"}},
                },
            },
            **get_error_responses(),
        },
    )
    def get(self, request, book_name):
        try:
            book = get_canonical_book_by_name(book_name)
            chapters = list(range(1, book.chapter_count + 1))
            display_name = get_book_display_name(book, request.lang_code)
            response = Response({"book": display_name, "chapters": chapters}, status=status.HTTP_200_OK)
            return response
        except Exception:
            return Response({"detail": "Book not found"}, status=status.HTTP_404_NOT_FOUND)


class BooksByAuthorView(APIView):
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
        return Response({"detail": "Not implemented"}, status=status.HTTP_501_NOT_IMPLEMENTED)


class BooksByTestamentView(LanguageSensitiveMixin, generics.ListAPIView):
    serializer_class = BookSerializer

    @extend_schema(
        summary="List books by testament",
        tags=["books"],
        parameters=[LANG_PARAMETER],
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

    def get_queryset(self):
        testament_id = self.kwargs["testament_id"]
        return (
            CanonicalBook.objects.filter(testament_id=testament_id)
            .select_related("testament")
            .prefetch_related("names")
            .order_by("canonical_order")
        )


class BookOutlineView(APIView):
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
            return Response({"detail": "Book not found"}, status=status.HTTP_404_NOT_FOUND)


class BookContextView(APIView):
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
            return Response({"detail": "Book not found"}, status=status.HTTP_404_NOT_FOUND)


class BookStructureView(APIView):
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
            return Response({"detail": "Book not found"}, status=status.HTTP_404_NOT_FOUND)


class BookStatisticsView(APIView):
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
            return Response({"detail": "Book not found"}, status=status.HTTP_404_NOT_FOUND)


# Phase 1: Discovery/Normalization Endpoints


class BookSearchView(LanguageSensitiveMixin, APIView):
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
                name="limit", description="Limit number of results (default: 20)", required=False, type=int
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
            return Response({"detail": 'Query parameter "q" is required.'}, status=400)

        # Language filter precedence: 'language' param for filtering (backward compatibility)
        language_filter = request.query_params.get("language", "").strip()
        # If no explicit 'language' filter but a 'lang' param is provided, default
        # the search to that language to improve i18n relevance
        if not language_filter and "lang" in request.query_params:
            language_filter = getattr(request, "lang_code", "").strip()
        limit = int(request.query_params.get("limit", 20))

        # Store request for context (needed for _format_search_result)
        self.request = request

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

        # Limit results
        search_results = search_results[:limit]

        if not search_results:
            return Response({"detail": f'No books found matching "{query}".'}, status=404)

        serializer = BookSearchResultSerializer(search_results, many=True)
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


class BookAliasesView(APIView):
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
            return Response({"detail": "No books found."}, status=404)

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


class BookResolveView(APIView):
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
            return Response({"detail": "Book identifier is required."}, status=400)

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
            return Response({"detail": f'Book identifier "{identifier}" could not be resolved.'}, status=404)

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


class BookCanonView(APIView):
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
            return Response(
                {"detail": f'Invalid canonical tradition "{tradition}". Available options: {available_traditions}'},
                status=400,
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
            return Response({"detail": f'No books found for tradition "{tradition}".'}, status=404)

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


class BookNeighborsView(APIView):
    """Get navigation information for a book (previous/next books)."""

    @extend_schema(
        summary="Get book navigation neighbors",
        description="Get previous and next books in canonical order for navigation",
        tags=["books"],
        parameters=[LANG_PARAMETER],
        responses={
            200: BookNeighborsSerializer,
            **get_error_responses(),
        },
    )
    def get(self, request, book_name, *args, **kwargs):
        book = get_canonical_book_by_name(book_name)
        if not book:
            return Response({"detail": f'Book "{book_name}" not found.'}, status=404)

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


class BookSectionsView(APIView):
    """List sections/perícopes for a book."""

    @extend_schema(
        summary="List book sections/perícopes",
        description="Get structural sections or perícopes for a book",
        tags=["books"],
        parameters=[
            OpenApiParameter(name="type", description="Filter by section type: chapter, pericope, theme"),
        ],
        responses={
            200: BookSectionSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get(self, request, book_name, *args, **kwargs):
        book = get_canonical_book_by_name(book_name)
        if not book:
            return Response({"detail": f'Book "{book_name}" not found.'}, status=404)

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


class BookSectionDetailView(APIView):
    """Get detailed information about a specific book section."""

    @extend_schema(
        summary="Get book section details",
        description="Get detailed information about a specific book section/perícope",
        tags=["books"],
        responses={
            200: BookSectionDetailSerializer,
            **get_error_responses(),
        },
    )
    def get(self, request, book_name, section_id, *args, **kwargs):
        book = get_canonical_book_by_name(book_name)
        if not book:
            return Response({"detail": f'Book "{book_name}" not found.'}, status=404)

        try:
            section_id = int(section_id)
        except ValueError:
            return Response({"detail": "Invalid section ID format."}, status=400)

        # For now, assume chapter-based sections
        if section_id < 1 or section_id > book.chapter_count:
            return Response({"detail": f'Section {section_id} not found in book "{book_name}".'}, status=404)

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


class BookRestrictedSearchView(APIView):
    """Search for verses within a specific book."""

    @extend_schema(
        summary="Search within a specific book",
        description="Search for text within a specific book's verses",
        tags=["books"],
        parameters=[
            OpenApiParameter(name="q", description="Search query", required=True),
            OpenApiParameter(name="version", description="Bible version code (default: first available)"),
            OpenApiParameter(name="limit", description="Maximum results (default: 20)"),
        ],
        responses={
            200: BookRestrictedSearchSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get(self, request, book_name, *args, **kwargs):
        book = get_canonical_book_by_name(book_name)
        if not book:
            return Response({"detail": f'Book "{book_name}" not found.'}, status=404)

        query = request.query_params.get("q", "").strip()
        if not query:
            return Response({"detail": 'Search query "q" parameter is required.'}, status=400)

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


class BookChapterVersesView(APIView):
    """List all verses in a specific chapter of a book."""

    @extend_schema(
        summary="List verses in a book chapter",
        description="Get all verses for a specific chapter in a book",
        tags=["books"],
        parameters=[
            OpenApiParameter(name="version", description="Bible version code (default: first available)"),
        ],
        responses={
            200: BookChapterVersesSerializer,
            **get_error_responses(),
        },
    )
    def get(self, request, book_name, chapter, *args, **kwargs):
        book = get_canonical_book_by_name(book_name)
        if not book:
            return Response({"detail": f'Book "{book_name}" not found.'}, status=404)

        try:
            chapter = int(chapter)
        except ValueError:
            return Response({"detail": "Invalid chapter number format."}, status=400)

        if chapter < 1 or chapter > book.chapter_count:
            return Response(
                {"detail": f'Chapter {chapter} not found in book "{book_name}" (max: {book.chapter_count}).'},
                status=404,
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
            return Response({"detail": f"No verses found for {book_name} {chapter}."}, status=404)

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


class BookRangeView(APIView):
    """Get verses for a specific range within a book."""

    @extend_schema(
        summary="Get verses for a book range",
        description="Get verses for a specific verse range within a book (e.g., John 3:16-18)",
        tags=["books"],
        parameters=[
            OpenApiParameter(name="start_chapter", description="Start chapter", required=True),
            OpenApiParameter(name="start_verse", description="Start verse", required=True),
            OpenApiParameter(name="end_chapter", description="End chapter"),
            OpenApiParameter(name="end_verse", description="End verse"),
            OpenApiParameter(name="version", description="Bible version code (default: first available)"),
        ],
        responses={
            200: BookRangeSerializer,
            **get_error_responses(),
        },
    )
    def get(self, request, book_name, *args, **kwargs):
        book = get_canonical_book_by_name(book_name)
        if not book:
            return Response({"detail": f'Book "{book_name}" not found.'}, status=404)

        # Parse range parameters
        try:
            start_chapter = int(request.query_params.get("start_chapter"))
            start_verse = int(request.query_params.get("start_verse"))
            end_chapter = int(request.query_params.get("end_chapter", start_chapter))
            end_verse = int(request.query_params.get("end_verse", start_verse))
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid range parameters. start_chapter and start_verse are required."}, status=400
            )

        # Validate range
        if start_chapter < 1 or start_chapter > book.chapter_count:
            return Response(
                {"detail": f'Start chapter {start_chapter} is out of range for book "{book_name}".'}, status=400
            )

        if end_chapter < 1 or end_chapter > book.chapter_count:
            return Response(
                {"detail": f'End chapter {end_chapter} is out of range for book "{book_name}".'}, status=400
            )

        if start_chapter > end_chapter or (start_chapter == end_chapter and start_verse > end_verse):
            return Response({"detail": "Invalid range: start must be before or equal to end."}, status=400)

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
            return Response({"detail": "No verses found for the specified range."}, status=404)

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
