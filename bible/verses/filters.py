"""Advanced filters for verses domain."""

import django_filters
from django.db.models import Q

from ..models import Verse, Version


class VerseFilter(django_filters.FilterSet):
    """Filtros avançados para versículos."""

    # Filtro versão (aceita ID ou código)
    version = django_filters.CharFilter(
        method="filter_version", help_text="Filter by version ID or code (e.g., '1' or 'ACF')"
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
        except Exception:
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
