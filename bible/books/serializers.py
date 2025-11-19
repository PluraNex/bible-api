"""Serializers for books domain."""

from rest_framework import serializers

from ..models import BookName, CanonicalBook, Language
from ..shared_serializers import BookCategorySerializer, TestamentSerializer


class BookSerializer(serializers.ModelSerializer):
    """
    Serializer melhorado para livros - frontend-friendly.

    Inclui objeto testament normalizado com código (old/new).
    Inclui objeto category para categorização de livros.
    Resposta otimizada sem campos duplicados.
    """

    name = serializers.SerializerMethodField()
    abbreviation = serializers.SerializerMethodField()
    order = serializers.IntegerField(source="canonical_order")

    # Objeto testament normalizado (único, sem duplicação)
    testament = serializers.SerializerMethodField()

    # Objeto category (categorização de livros)
    category = BookCategorySerializer(read_only=True)

    # Aliases do livro
    aliases = serializers.SerializerMethodField()

    # Idioma da resposta
    language_code = serializers.SerializerMethodField()

    class Meta:
        model = CanonicalBook
        fields = [
            "osis_code",
            "name",
            "abbreviation",
            "aliases",
            "order",
            "testament",
            "category",
            "chapter_count",
            "is_deuterocanonical",
            "language_code",
        ]

    def get_name(self, obj) -> str:
        """Get localized name using the existing utility function with fallback logic."""
        from bible.utils import get_book_display_name
        from bible.utils.i18n import get_language_from_context

        lang_code = get_language_from_context(self.context)
        return get_book_display_name(obj, lang_code)

    def get_abbreviation(self, obj) -> str:
        """Get localized abbreviation using the existing utility function with fallback logic."""
        from bible.utils import get_book_abbreviation
        from bible.utils.i18n import get_language_from_context

        lang_code = get_language_from_context(self.context)
        return get_book_abbreviation(obj, lang_code)

    def get_testament(self, obj):
        """Testament serializado com context."""
        serializer = TestamentSerializer(obj.testament, context=self.context)
        return serializer.data

    def get_aliases(self, obj):
        """Todos os aliases do livro no idioma da requisição."""
        from bible.utils.i18n import get_language_from_context

        lang_code = get_language_from_context(self.context)

        # Otimização: usar values_list para evitar instanciar objetos
        aliases = set()
        names_qs = obj.names.filter(language__code=lang_code).values_list("name", "abbreviation")

        for name, abbr in names_qs:
            if name:
                aliases.add(name)
            if abbr:
                aliases.add(abbr)

        # Remove o nome principal
        primary_name = self.get_name(obj)
        aliases.discard(primary_name)

        return sorted(aliases)  # Ordena para consistência

    def get_language_code(self, obj):
        """Idioma da resposta."""
        from bible.utils.i18n import get_language_from_context

        return get_language_from_context(self.context)


class CanonicalBookSerializer(serializers.ModelSerializer):
    """Full blueprint serializer for canonical books."""

    testament_name = serializers.CharField(source="testament.name", read_only=True)

    class Meta:
        model = CanonicalBook
        fields = [
            "id",
            "osis_code",
            "canonical_order",
            "testament",
            "testament_name",
            "is_deuterocanonical",
            "chapter_count",
            "created_at",
            "updated_at",
        ]


class BookNameSerializer(serializers.ModelSerializer):
    """Serializer for book names in different languages."""

    canonical_book_osis = serializers.CharField(source="canonical_book.osis_code", read_only=True)
    language_code = serializers.CharField(source="language.code", read_only=True)
    language_name = serializers.CharField(source="language.name", read_only=True)
    version_code = serializers.CharField(source="version.code", read_only=True)

    class Meta:
        model = BookName
        fields = [
            "id",
            "name",
            "abbreviation",
            "canonical_book",
            "canonical_book_osis",
            "language",
            "language_code",
            "language_name",
            "version",
            "version_code",
        ]


class LanguageSerializer(serializers.ModelSerializer):
    """Serializer for language information."""

    class Meta:
        model = Language
        fields = ["id", "name", "code", "created_at", "updated_at"]


class BookSearchResultSerializer(serializers.Serializer):
    """Serializer for book search results."""

    osis_code = serializers.CharField()
    name = serializers.CharField()
    aliases = serializers.ListSerializer(child=serializers.CharField(), help_text="Alternative names and abbreviations")
    canonical_order = serializers.IntegerField()
    testament = serializers.CharField()
    is_deuterocanonical = serializers.BooleanField()
    chapter_count = serializers.IntegerField()
    match_type = serializers.CharField(help_text="Type of match: osis, name, abbreviation")
    language = serializers.CharField(help_text="Language of the matched name")


class BookAliasSerializer(serializers.Serializer):
    """Serializer for book alias information."""

    osis_code = serializers.CharField()
    canonical_name = serializers.CharField(help_text="Primary canonical name")
    aliases = serializers.ListSerializer(
        child=serializers.DictField(), help_text="List of aliases with language and version info"
    )
    testament = serializers.CharField()
    canonical_order = serializers.IntegerField()


class BookResolveResultSerializer(serializers.Serializer):
    """Serializer for book identifier resolution results."""

    osis_code = serializers.CharField()
    canonical_name = serializers.CharField()
    aliases = serializers.ListSerializer(
        child=serializers.DictField(), help_text="List of alternative names by language"
    )
    canonical_order = serializers.IntegerField()
    testament = serializers.CharField()
    is_deuterocanonical = serializers.BooleanField()
    chapter_count = serializers.IntegerField()
    resolved_from = serializers.CharField(help_text="Original identifier that was resolved")
    resolution_type = serializers.CharField(help_text="How the identifier was resolved")


class BookCanonResultSerializer(serializers.Serializer):
    """Serializer for canon tradition filtering results."""

    osis_code = serializers.CharField()
    name = serializers.CharField()
    canonical_order = serializers.IntegerField()
    testament = serializers.CharField()
    is_deuterocanonical = serializers.BooleanField()
    chapter_count = serializers.IntegerField()
    inclusion_reason = serializers.CharField(help_text="Why this book is included in the tradition")


# Phase 2: Navigation/Structure Serializers


class BookNeighborsSerializer(serializers.Serializer):
    """Serializer for book navigation (previous/next books)."""

    current = serializers.DictField(help_text="Current book information")
    previous = serializers.DictField(allow_null=True, help_text="Previous book in canonical order")
    next = serializers.DictField(allow_null=True, help_text="Next book in canonical order")
    testament_neighbors = serializers.DictField(help_text="Navigation within same testament")


class BookSectionSerializer(serializers.Serializer):
    """Serializer for book sections/perícopes."""

    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    start_chapter = serializers.IntegerField()
    start_verse = serializers.IntegerField()
    end_chapter = serializers.IntegerField()
    end_verse = serializers.IntegerField()
    section_type = serializers.CharField(help_text="Type: chapter, pericope, theme")


class BookSectionDetailSerializer(serializers.Serializer):
    """Detailed serializer for a specific book section."""

    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    start_chapter = serializers.IntegerField()
    start_verse = serializers.IntegerField()
    end_chapter = serializers.IntegerField()
    end_verse = serializers.IntegerField()
    section_type = serializers.CharField()
    book_info = serializers.DictField(help_text="Associated book information")
    verse_range = serializers.CharField(help_text="Human-readable verse range")
    context = serializers.DictField(allow_null=True, help_text="Additional contextual information")


class BookRestrictedSearchSerializer(serializers.Serializer):
    """Serializer for book-restricted search results."""

    chapter = serializers.IntegerField()
    verse = serializers.IntegerField()
    text_preview = serializers.CharField(help_text="Preview of matching text")
    match_score = serializers.FloatField(help_text="Relevance score")
    verse_reference = serializers.CharField(help_text="Human-readable reference")


class BookChapterVersesSerializer(serializers.Serializer):
    """Serializer for chapter verses listing."""

    chapter_number = serializers.IntegerField()
    verse_count = serializers.IntegerField()
    verses = serializers.ListSerializer(child=serializers.DictField(), help_text="List of verses in the chapter")
    chapter_info = serializers.DictField(help_text="Additional chapter metadata")


class BookRangeSerializer(serializers.Serializer):
    """Serializer for verse range results."""

    book = serializers.CharField()
    start_reference = serializers.CharField()
    end_reference = serializers.CharField()
    verse_count = serializers.IntegerField()
    verses = serializers.ListSerializer(child=serializers.DictField(), help_text="List of verses in the range")
    range_info = serializers.DictField(help_text="Additional range metadata")
