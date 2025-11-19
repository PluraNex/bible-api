"""Advanced filters for books domain."""

import django_filters
from django.db.models import Q

from ..models import CanonicalBook


class BookFilter(django_filters.FilterSet):
    """Filtros avançados para livros."""

    filterset_fields = ["testament", "is_deuterocanonical"]

    # Filtros por testamento
    testament = django_filters.ChoiceFilter(
        choices=[("old", "Old Testament"), ("new", "New Testament")],
        method="filter_testament",
        help_text="Filter by testament code (old/new)",
    )
    testament_code = django_filters.ChoiceFilter(
        choices=[("old", "Old Testament"), ("new", "New Testament")],
        method="filter_testament",
        help_text="Filter by testament code (old/new)",
    )
    testament_id = django_filters.NumberFilter(field_name="testament__id", help_text="Filter by testament ID")

    # Filtros por livros deuterocanônicos
    is_deuterocanonical = django_filters.BooleanFilter(
        field_name="is_deuterocanonical", help_text="Filter deuterocanonical books (true/false)"
    )

    # Filtros por nome/código
    osis_code = django_filters.CharFilter(
        field_name="osis_code", lookup_expr="iexact", help_text="Filter by OSIS code (e.g., 'John', 'Gen')"
    )
    name = django_filters.CharFilter(method="filter_name", help_text="Search by book name in any language")

    # Filtros por número de capítulos
    chapter_count_min = django_filters.NumberFilter(
        field_name="chapter_count", lookup_expr="gte", help_text="Minimum number of chapters"
    )
    chapter_count_max = django_filters.NumberFilter(
        field_name="chapter_count", lookup_expr="lte", help_text="Maximum number of chapters"
    )

    # Filtros por ordem canônica
    canonical_order_min = django_filters.NumberFilter(
        field_name="canonical_order", lookup_expr="gte", help_text="Minimum canonical order"
    )
    canonical_order_max = django_filters.NumberFilter(
        field_name="canonical_order", lookup_expr="lte", help_text="Maximum canonical order"
    )

    # Filtro por categoria
    category = django_filters.NumberFilter(field_name="category__id", help_text="Filter by book category ID")
    category_name = django_filters.CharFilter(method="filter_category_name", help_text="Filter by category name")

    class Meta:
        model = CanonicalBook
        fields = ["testament", "is_deuterocanonical", "osis_code", "category"]

    def filter_testament(self, queryset, name, value):
        """Filtra por testamento usando code (old/new)."""
        if value == "old":
            # Buscar por testamentos que contenham "old" ou "antigo" no nome
            return queryset.filter(
                Q(testament__name__icontains="old")
                | Q(testament__name__icontains="antigo")
                | Q(testament__display_name__icontains="old")
                | Q(testament__display_name__icontains="antigo")
            )
        elif value == "new":
            # Buscar por testamentos que contenham "new" ou "novo" no nome
            return queryset.filter(
                Q(testament__name__icontains="new")
                | Q(testament__name__icontains="novo")
                | Q(testament__display_name__icontains="new")
                | Q(testament__display_name__icontains="novo")
            )
        return queryset

    def filter_name(self, queryset, name, value):
        """Busca por nome do livro em qualquer idioma."""
        return queryset.filter(
            Q(names__name__icontains=value) | Q(names__abbreviation__icontains=value) | Q(osis_code__icontains=value)
        ).distinct()

    def filter_category_name(self, queryset, name, value):
        """Filtra por nome da categoria em qualquer idioma."""
        return queryset.filter(
            Q(category__name__icontains=value)
            | Q(category__name_pt__icontains=value)
            | Q(category__name_en__icontains=value)
            | Q(category__name_es__icontains=value)
        ).distinct()
