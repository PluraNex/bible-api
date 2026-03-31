"""Serializers for Biblical Symbols domain."""

from rest_framework import serializers

from .models import BiblicalSymbol, SymbolMeaning, SymbolProgression


# ─── Nested ──────────────────────────────────────────────

class SymbolMeaningSerializer(serializers.ModelSerializer):
    class Meta:
        model = SymbolMeaning
        fields = [
            "id", "meaning", "meaning_pt",
            "theological_context", "valence",
            "is_primary_meaning", "primary_reference",
            "supporting_references", "testament_focus", "frequency",
        ]


class SymbolProgressionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SymbolProgression
        fields = [
            "stage_order", "stage_name", "stage_name_pt",
            "description", "biblical_era", "primary_book",
            "key_reference", "is_fulfilled_in_christ",
        ]


class SymbolCompactSerializer(serializers.ModelSerializer):
    """Minimal reference for related_symbols."""

    class Meta:
        model = BiblicalSymbol
        fields = ["canonical_id", "primary_name", "emoji"]


# ─── List (compact) ─────────────────────────────────────

class SymbolListSerializer(serializers.ModelSerializer):
    """Compact serializer for list/search results."""

    meaning_count = serializers.IntegerField(read_only=True, default=0)
    primary_meaning = serializers.SerializerMethodField()

    class Meta:
        model = BiblicalSymbol
        fields = [
            "canonical_id", "namespace", "primary_name", "primary_name_pt",
            "literal_meaning", "emoji",
            "priority", "boost", "frequency",
            "meaning_count", "primary_meaning",
        ]

    def get_primary_meaning(self, obj):
        if hasattr(obj, "_prefetched_objects_cache") and "meanings" in obj._prefetched_objects_cache:
            for m in obj.meanings.all():
                if m.is_primary_meaning:
                    return m.meaning
            first = obj.meanings.all()[:1]
            return first[0].meaning if first else None
        meaning = obj.meanings.filter(is_primary_meaning=True).first()
        if meaning:
            return meaning.meaning
        meaning = obj.meanings.first()
        return meaning.meaning if meaning else None


# ─── Detail (full) ──────────────────────────────────────

class SymbolDetailSerializer(serializers.ModelSerializer):
    """Full detail with nested meanings, progressions, related symbols."""

    meanings = SymbolMeaningSerializer(many=True, read_only=True)
    progressions = SymbolProgressionSerializer(many=True, read_only=True)
    related_symbols = SymbolCompactSerializer(many=True, read_only=True)
    opposite_symbol = SymbolCompactSerializer(read_only=True)

    class Meta:
        model = BiblicalSymbol
        fields = [
            "canonical_id", "namespace", "primary_name", "primary_name_pt",
            "primary_name_original",
            "description", "description_pt",
            "aliases", "associated_concepts",
            "literal_meaning", "literal_meaning_pt",
            "emoji", "icon_name",
            "priority", "boost", "frequency",
            "study_value", "difficulty_level",
            "hebrew_word", "hebrew_transliteration",
            "greek_word", "greek_transliteration",
            "strongs_hebrew", "strongs_greek",
            "ai_summary", "ai_hermeneutical_guide",
            "meanings", "progressions",
            "related_symbols", "opposite_symbol",
            "view_count", "bookmark_count",
            "created_at", "updated_at",
        ]


# ─── By-Verse (StudyRail) ───────────────────────────────

class SymbolByVerseSerializer(serializers.Serializer):
    """Focused response for by-verse endpoint (SymbolsTab)."""

    canonical_id = serializers.CharField()
    namespace = serializers.CharField()
    primary_name = serializers.CharField()
    emoji = serializers.CharField(allow_blank=True)
    literal_meaning = serializers.CharField()
    usage_type = serializers.CharField()
    context_note = serializers.CharField()
