"""Advanced filters for verses domain."""

import re

import django_filters
from django.db.models import Q
from django.http import Http404

from ..models import Verse, Version


class VerseFilter(django_filters.FilterSet):
    """Filtros avançados para versículos."""

    # Filtro versão (aceita ID ou código)
    version = django_filters.CharFilter(
        method="filter_version", help_text="Filter by version ID or code (e.g., '1' or 'ACF')"
    )

    # Filtro de busca por palavra completa
    word = django_filters.CharFilter(
        method="filter_word",
        help_text="Search for complete word(s) in verse text. Separates 'amor' from 'amorreu'. Supports multiple words separated by space (AND logic).",
    )

    # Filtros por versão
    version_code = django_filters.CharFilter(
        field_name="version__code", lookup_expr="iexact", help_text="Filter by version code (e.g., 'NVI', 'KJV', 'ACF')"
    )
    version_name = django_filters.CharFilter(
        field_name="version__name", lookup_expr="iexact", help_text="Filter by version name"
    )

    # Filtros por livro
    book_osis = django_filters.CharFilter(
        field_name="book__osis_code", lookup_expr="iexact", help_text="Filter by book OSIS code (e.g., 'John', 'Gen')"
    )
    book_name = django_filters.CharFilter(
        method="filter_book_name", help_text="Filter by book name (localized, e.g., 'João', 'John')"
    )

    # Filtros por range de capítulos
    chapter_min = django_filters.NumberFilter(
        field_name="chapter", lookup_expr="gte", help_text="Minimum chapter number"
    )
    chapter_max = django_filters.NumberFilter(
        field_name="chapter", lookup_expr="lte", help_text="Maximum chapter number"
    )

    # Filtros por range de versículos
    verse_min = django_filters.NumberFilter(field_name="number", lookup_expr="gte", help_text="Minimum verse number")
    verse_max = django_filters.NumberFilter(field_name="number", lookup_expr="lte", help_text="Maximum verse number")

    # Filtros por testamento
    testament = django_filters.ChoiceFilter(
        choices=[("old", "Old Testament"), ("new", "New Testament")],
        method="filter_testament",
        help_text="Filter by testament (old/new)",
    )
    testament_id = django_filters.NumberFilter(field_name="book__testament__id", help_text="Filter by testament ID")

    # Filtros por idioma
    language_code = django_filters.CharFilter(
        field_name="version__language__code",
        lookup_expr="iexact",
        help_text="Filter by language code (e.g., 'pt-BR', 'en')",
    )

    # Filtro por livros deuterocanônicos
    is_deuterocanonical = django_filters.BooleanFilter(
        field_name="book__is_deuterocanonical", help_text="Filter deuterocanonical books"
    )

    class Meta:
        model = Verse
        fields = ["version", "book", "chapter", "number"]

    def filter_book_name(self, queryset, name, value):
        """Filtra por nome do livro (localizado ou OSIS)."""
        from ..utils import get_canonical_book_by_name

        try:
            book = get_canonical_book_by_name(value)
            return queryset.filter(book=book)
        except Http404:
            # Se não encontrar, busca por nome em qualquer idioma
            return queryset.filter(
                Q(book__names__name__icontains=value)
                | Q(book__names__abbreviation__iexact=value)
                | Q(book__osis_code__iexact=value)
            ).distinct()

    def filter_version(self, queryset, name, value):
        """Filtra por versão (aceita ID ou código)."""
        try:
            # Tentar como ID numérico primeiro
            version_id = int(value)
            return queryset.filter(version_id=version_id)
        except (ValueError, TypeError):
            # Se não for número, buscar versão pelo código ou nome
            version = Version.objects.filter(Q(code__iexact=value) | Q(name__iexact=value)).first()

            if version:
                return queryset.filter(version=version)

            # Se não encontrar, retornar queryset vazio
            return queryset.none()

    def filter_testament(self, queryset, name, value):
        """Filtra por testamento."""
        if value == "old":
            return queryset.filter(book__testament__name__icontains="old")
        elif value == "new":
            return queryset.filter(book__testament__name__icontains="new")
        return queryset

    def filter_word(self, queryset, name, value):
        """
        Filtra por palavra(s) completa(s) no texto do versículo.

        Diferente do filtro 'search' que usa icontains (match parcial),
        este filtro usa regex para garantir match de palavra completa.
        Isso separa 'amor' de 'amorreu', 'amores', etc.

        Suporta múltiplas palavras separadas por espaço (lógica AND).
        Exemplo: 'amor fé' encontra versículos que contêm AMBAS as palavras.
        """
        if not value or not value.strip():
            return queryset

        words = value.strip().split()

        for word in words:
            # Escapar caracteres especiais de regex para segurança
            escaped_word = re.escape(word.strip())
            # Padrão regex para palavra completa (case-insensitive via iregex)
            # \y é word boundary para PostgreSQL, mas Django usa \b
            # No PostgreSQL: usamos \m e \M ou (?<![a-zA-ZÀ-ÿ]) e (?![a-zA-ZÀ-ÿ])
            # Alternativa mais segura: usar espaços/pontuação como delimitadores
            pattern = rf"(^|[^a-zA-ZÀ-ÿ]){escaped_word}([^a-zA-ZÀ-ÿ]|$)"
            queryset = queryset.filter(text__iregex=pattern)

        return queryset
