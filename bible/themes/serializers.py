"""Serializers for themes domain."""
from rest_framework import serializers

from ..models import Theme


class ThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theme
        fields = ["id", "name", "description"]


class ThemeStatisticsSerializer(serializers.Serializer):
    """Statistics data for a specific theme."""

    theme_id = serializers.IntegerField()
    theme_name = serializers.CharField()
    verse_count = serializers.IntegerField()
    book_count = serializers.IntegerField()
    version_count = serializers.IntegerField()
    top_books = serializers.ListSerializer(
        child=serializers.DictField(), help_text="Books with most verses for this theme"
    )
    testament_distribution = serializers.DictField(help_text="Verse count by testament")


class ThemeAnalysisByBookSerializer(serializers.Serializer):
    """Theme analysis data for a specific book."""

    book_name = serializers.CharField()
    book_osis_code = serializers.CharField()
    canonical_order = serializers.IntegerField()
    theme_distribution = serializers.ListSerializer(
        child=serializers.DictField(), help_text="Themes in this book with verse counts"
    )
    chapter_analysis = serializers.ListSerializer(
        child=serializers.DictField(), help_text="Theme distribution by chapter"
    )
    total_themed_verses = serializers.IntegerField()
    total_book_verses = serializers.IntegerField()
    coverage_percentage = serializers.FloatField()


class ThemeProgressionSerializer(serializers.Serializer):
    """Chronological progression data for a theme."""

    theme_id = serializers.IntegerField()
    theme_name = serializers.CharField()
    progression_data = serializers.ListSerializer(
        child=serializers.DictField(), help_text="Theme appearance by canonical book order"
    )
    testament_summary = serializers.DictField(help_text="Summary statistics by testament")
    peak_books = serializers.ListSerializer(
        child=serializers.DictField(), help_text="Books with highest theme concentration"
    )


class ConceptMapSerializer(serializers.Serializer):
    """Concept relationship mapping for themes."""

    concept = serializers.CharField()
    related_themes = serializers.ListSerializer(
        child=serializers.DictField(), help_text="Themes related to this concept"
    )
    co_occurrence_data = serializers.ListSerializer(
        child=serializers.DictField(), help_text="Themes that co-occur with the concept theme"
    )
    strength_metrics = serializers.DictField(help_text="Relationship strength measurements")
    verse_examples = serializers.ListSerializer(
        child=serializers.DictField(), help_text="Example verses showing concept relationships"
    )
