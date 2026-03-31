"""Serializers for themes domain.

Two levels of detail controlled by ?detail=full query param:
- Default: clean product response (what the frontend needs)
- Full: includes research metadata (grades, evidence_score, etc.)
"""

from rest_framework import serializers

from .models import Theme, ThemeVerseLink


# ─── Verse serializers ───────────────────────────────────────

class VerseSerializer(serializers.ModelSerializer):
    """Verse within a theme — clean product response."""

    ref = serializers.SerializerMethodField()
    text = serializers.CharField(source="verse.text", read_only=True)
    book = serializers.CharField(source="verse.book.osis_code", read_only=True)
    chapter = serializers.IntegerField(source="verse.chapter", read_only=True)
    verse = serializers.IntegerField(source="verse.number", read_only=True)

    class Meta:
        model = ThemeVerseLink
        fields = ["ref", "book", "chapter", "verse", "text"]

    def get_ref(self, obj):
        v = obj.verse
        return f"{v.book.osis_code}.{v.chapter}.{v.number}"


class VerseFullSerializer(VerseSerializer):
    """Verse with research metadata (grade, relevance, source)."""

    class Meta(VerseSerializer.Meta):
        fields = [
            "id", "ref", "book", "chapter", "verse", "text",
            "grade", "relevance_score", "is_primary_theme", "source",
        ]


# ─── Theme serializers ───────────────────────────────────────

class ThemeListSerializer(serializers.ModelSerializer):
    """Theme list — clean for product."""

    name = serializers.CharField(source="name_pt", read_only=True)

    class Meta:
        model = Theme
        fields = ["id", "slug", "name", "name_en", "verse_count"]


class ThemeListFullSerializer(serializers.ModelSerializer):
    """Theme list — with research metadata."""

    name = serializers.CharField(source="name_pt", read_only=True)
    grade_distribution = serializers.SerializerMethodField()

    class Meta:
        model = Theme
        fields = [
            "id", "slug", "name", "name_en", "name_pt",
            "status", "evidence_score", "verse_count", "priority",
            "grade_distribution",
        ]

    def get_grade_distribution(self, obj):
        links = obj.verse_links.all()
        return {
            "grade_3": links.filter(grade=3).count(),
            "grade_2": links.filter(grade=2).count(),
            "grade_1": links.filter(grade=1).count(),
        }


class ThemeDetailSerializer(serializers.ModelSerializer):
    """Theme detail — clean for product, with verses."""

    name = serializers.CharField(source="name_pt", read_only=True)
    description = serializers.CharField(source="description_pt", read_only=True)
    verses = VerseSerializer(source="verse_links", many=True, read_only=True)

    class Meta:
        model = Theme
        fields = [
            "id", "slug", "name", "name_en",
            "description", "verse_count",
            "anchor_verses", "verses",
        ]


class ThemeDetailFullSerializer(serializers.ModelSerializer):
    """Theme detail — with research metadata."""

    name = serializers.CharField(source="name_pt", read_only=True)
    description = serializers.CharField(source="description_pt", read_only=True)
    verses = VerseFullSerializer(source="verse_links", many=True, read_only=True)
    grade_distribution = serializers.SerializerMethodField()

    class Meta:
        model = Theme
        fields = [
            "id", "slug", "name", "name_en", "name_pt",
            "description", "description_en",
            "description_short_en", "description_short_pt",
            "status", "evidence_score", "verse_count", "priority",
            "semantic_keywords", "anchor_verses",
            "hebrew_term", "greek_term",
            "ai_summary", "ai_summary_pt",
            "grade_distribution", "verses",
            "created_at", "updated_at",
        ]

    def get_grade_distribution(self, obj):
        links = obj.verse_links.all()
        return {
            "grade_3": links.filter(grade=3).count(),
            "grade_2": links.filter(grade=2).count(),
            "grade_1": links.filter(grade=1).count(),
        }


# ─── Backward compat aliases ─────────────────────────────────

ThemeSerializer = ThemeListSerializer


# ─── Analytics serializers (unchanged) ────────────────────────

class ThemeStatisticsSerializer(serializers.Serializer):
    theme_id = serializers.IntegerField()
    theme_name = serializers.CharField()
    verse_count = serializers.IntegerField()
    book_count = serializers.IntegerField()
    version_count = serializers.IntegerField()
    top_books = serializers.ListSerializer(child=serializers.DictField())
    testament_distribution = serializers.DictField()


class ThemeAnalysisByBookSerializer(serializers.Serializer):
    book_name = serializers.CharField()
    book_osis_code = serializers.CharField()
    canonical_order = serializers.IntegerField()
    theme_distribution = serializers.ListSerializer(child=serializers.DictField())
    chapter_analysis = serializers.ListSerializer(child=serializers.DictField())
    total_themed_verses = serializers.IntegerField()
    total_book_verses = serializers.IntegerField()
    coverage_percentage = serializers.FloatField()


class ThemeProgressionSerializer(serializers.Serializer):
    theme_id = serializers.IntegerField()
    theme_name = serializers.CharField()
    progression_data = serializers.ListSerializer(child=serializers.DictField())
    testament_summary = serializers.DictField()
    peak_books = serializers.ListSerializer(child=serializers.DictField())


class ConceptMapSerializer(serializers.Serializer):
    concept = serializers.CharField()
    related_themes = serializers.ListSerializer(child=serializers.DictField())
    co_occurrence_data = serializers.ListSerializer(child=serializers.DictField())
    strength_metrics = serializers.DictField()
    verse_examples = serializers.ListSerializer(child=serializers.DictField())
