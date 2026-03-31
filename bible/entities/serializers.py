"""Serializers for Biblical Entities domain."""

from rest_framework import serializers

from .models import (
    CanonicalEntity,
    EntityAlias,
    EntityRelationship,
    EntityRole,
)


# ─── Nested / Compact ───────────────────────────────────

class EntityAliasSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityAlias
        fields = ["name", "language_code", "is_primary"]


class EntityRoleCompactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityRole
        fields = ["role_type", "role_label", "narrative_order"]


class EntityCompactSerializer(serializers.ModelSerializer):
    """Minimal entity reference for relationship endpoints."""

    class Meta:
        model = CanonicalEntity
        fields = ["canonical_id", "namespace", "primary_name"]


# ─── Relationships ───────────────────────────────────────

class EntityRelationshipSerializer(serializers.Serializer):
    """Relationship with direction context."""

    relationship_type = serializers.CharField()
    direction = serializers.CharField()
    related_entity = EntityCompactSerializer()
    description = serializers.CharField()


# ─── List (compact) ─────────────────────────────────────

class EntityListSerializer(serializers.ModelSerializer):
    """Compact serializer for list/search results."""

    person_slug = serializers.SerializerMethodField()

    class Meta:
        model = CanonicalEntity
        fields = [
            "canonical_id", "namespace", "primary_name",
            "description", "categories",
            "priority", "boost", "verse_count",
            "is_type_of_christ", "biblical_era",
            "person_slug",
        ]

    def get_person_slug(self, obj):
        if hasattr(obj, "person") and obj.person_id:
            return obj.person.slug
        return None


# ─── Detail (full) ──────────────────────────────────────

class EntityDetailSerializer(serializers.ModelSerializer):
    """Full detail with nested aliases and roles."""

    aliases = EntityAliasSerializer(many=True, read_only=True)
    roles = EntityRoleCompactSerializer(many=True, read_only=True, source="current_roles")
    person_slug = serializers.SerializerMethodField()

    class Meta:
        model = CanonicalEntity
        fields = [
            "canonical_id", "namespace", "primary_name", "primary_name_original",
            "description", "description_pt",
            "categories", "priority", "boost",
            "birth_year", "death_year", "active_period", "biblical_era",
            "verse_count", "study_value", "difficulty_level",
            "is_type_of_christ", "typology_explanation",
            "etymology", "hebrew_transliteration", "greek_transliteration",
            "strongs_hebrew", "strongs_greek",
            "ai_summary", "ai_theological_significance", "ai_historical_context",
            "wikidata_id", "wikipedia_url",
            "aliases", "roles",
            "person_slug",
            "view_count", "bookmark_count",
            "created_at", "updated_at",
        ]

    def get_person_slug(self, obj):
        if hasattr(obj, "person") and obj.person_id:
            return obj.person.slug
        return None


# ─── By-Verse (StudyRail) ───────────────────────────────

class EntityByVerseSerializer(serializers.Serializer):
    """Focused response for by-verse endpoint (EntitiesTab)."""

    canonical_id = serializers.CharField()
    namespace = serializers.CharField()
    primary_name = serializers.CharField()
    description = serializers.CharField()
    mention_type = serializers.CharField()
    is_primary_subject = serializers.BooleanField()
    relevance = serializers.FloatField()
