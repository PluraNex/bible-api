"""Serializers for topics domain - i18n aware."""

from rest_framework import serializers

from bible.utils.i18n import get_language_from_context

from ..models import (
    Language,
    Topic,
    TopicAspect,
    TopicContent,
    TopicCrossReference,
    TopicDefinition,
    TopicName,
    TopicRelation,
    TopicThemeLink,
)


def _get_content_by_language(contents_qs, lang_code: str):
    """
    Get content by language code with fallback to English.
    Handles both exact match and regional variant fallback (pt → pt-BR).
    """
    # Try exact match first
    content = contents_qs.filter(language__code=lang_code).first()
    if content:
        return content

    # Try startswith for regional variants (pt → pt-BR)
    lang_prefix = lang_code.split("-")[0] if "-" in lang_code else lang_code
    content = contents_qs.filter(language__code__istartswith=lang_prefix).first()
    if content:
        return content

    # Fallback to English (including en-US, en-GB, etc.)
    content = contents_qs.filter(language__code__istartswith="en").first()
    return content


def _get_name_by_language(names_qs, lang_code: str):
    """
    Get name by language code with fallback to English.
    Handles both exact match and regional variant fallback (pt → pt-BR).
    """
    # Try exact match first
    name = names_qs.filter(language__code=lang_code).first()
    if name:
        return name

    # Try startswith for regional variants
    lang_prefix = lang_code.split("-")[0] if "-" in lang_code else lang_code
    name = names_qs.filter(language__code__istartswith=lang_prefix).first()
    if name:
        return name

    # Fallback to English
    name = names_qs.filter(language__code__istartswith="en").first()
    return name


class TopicListSerializer(serializers.ModelSerializer):
    """
    Compact serializer for topic listings.
    Follows BookSerializer pattern for i18n.
    """

    name = serializers.SerializerMethodField()
    language_code = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = [
            "slug",
            "name",
            "topic_type",
            "total_verses",
            "ot_refs",
            "nt_refs",
            "aspects_count",
            "ai_enriched",
            "primary_source",
            "language_code",
        ]

    def get_name(self, obj) -> str:
        """Get localized topic name."""
        lang_code = get_language_from_context(self.context)
        return obj.get_display_name(lang_code)

    def get_language_code(self, obj) -> str:
        """Return resolved language code."""
        return get_language_from_context(self.context)


class TopicDetailSerializer(serializers.ModelSerializer):
    """
    Full topic serializer with localized name and content.
    Follows BookSerializer pattern for i18n.
    """

    # Localized fields (resolved via get_language_from_context)
    name = serializers.SerializerMethodField()
    aliases = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    outline = serializers.SerializerMethodField()
    key_concepts = serializers.SerializerMethodField()
    theological_significance = serializers.SerializerMethodField()

    # Language of response
    language_code = serializers.SerializerMethodField()

    # Previews
    definitions_preview = serializers.SerializerMethodField()
    themes_preview = serializers.SerializerMethodField()
    aspects_preview = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = [
            "slug",
            "canonical_id",
            "name",
            "aliases",
            "topic_type",
            "summary",
            "outline",
            "key_concepts",
            "theological_significance",
            "total_verses",
            "ot_refs",
            "nt_refs",
            "books_count",
            "aspects_count",
            "ai_enriched",
            "ai_model",
            "ai_confidence",
            "ai_run_id",
            "ai_enriched_at",
            "primary_source",
            "available_sources",
            "quality_score",
            "definitions_preview",
            "themes_preview",
            "aspects_preview",
            "language_code",
        ]

    def get_name(self, obj) -> str:
        """Get localized topic name."""
        lang_code = get_language_from_context(self.context)
        return obj.get_display_name(lang_code)

    def get_aliases(self, obj) -> list:
        """Get aliases in current language."""
        lang_code = get_language_from_context(self.context)
        name_obj = _get_name_by_language(obj.names, lang_code)
        return name_obj.aliases if name_obj else []

    def get_summary(self, obj) -> str:
        """Get localized summary."""
        lang_code = get_language_from_context(self.context)
        content = _get_content_by_language(obj.contents, lang_code)
        return content.summary if content else ""

    def get_outline(self, obj) -> list:
        """Get localized outline."""
        lang_code = get_language_from_context(self.context)
        content = _get_content_by_language(obj.contents, lang_code)
        return content.outline if content else []

    def get_key_concepts(self, obj) -> list:
        """Get localized key concepts."""
        lang_code = get_language_from_context(self.context)
        content = _get_content_by_language(obj.contents, lang_code)
        return content.key_concepts if content else []

    def get_theological_significance(self, obj) -> str:
        """Get localized theological significance."""
        lang_code = get_language_from_context(self.context)
        content = _get_content_by_language(obj.contents, lang_code)
        return content.theological_significance if content else ""

    def get_language_code(self, obj) -> str:
        """Return resolved language code."""
        return get_language_from_context(self.context)

    def get_definitions_preview(self, obj) -> dict:
        """Get preview of available definitions."""
        definitions = {}
        for defn in obj.definitions.all()[:3]:
            definitions[defn.source.lower()] = {
                "excerpt": defn.text[:200] + "..." if len(defn.text) > 200 else defn.text,
                "refs_count": defn.refs_count,
            }
        return definitions

    def get_themes_preview(self, obj) -> list:
        """Get preview of linked themes."""
        lang_code = get_language_from_context(self.context)
        themes = []
        for link in obj.theme_links.all()[:5]:
            label = link.label_original if lang_code.startswith("pt") else link.label_en
            themes.append(
                {
                    "label": label or link.label_normalized,
                    "anchor_verses": link.anchor_verses[:2],
                    "theological_domain": link.theological_domain,
                    "relevance_score": link.relevance_score,
                }
            )
        return themes

    def get_aspects_preview(self, obj) -> list:
        """Get preview of topic aspects."""
        lang_code = get_language_from_context(self.context)
        aspects = []
        for aspect in obj.aspects.all()[:5]:
            aspects.append(
                {
                    "label": aspect.get_label(lang_code),
                    "verse_count": aspect.verse_count,
                }
            )
        return aspects


class TopicAspectSerializer(serializers.ModelSerializer):
    """Aspect serializer with localized label."""

    label = serializers.SerializerMethodField()

    class Meta:
        model = TopicAspect
        fields = [
            "id",
            "slug",
            "label",
            "order",
            "raw_references",
            "verse_count",
            "ot_refs",
            "nt_refs",
            "books",
            "source",
        ]

    def get_label(self, obj) -> str:
        """Get localized label."""
        lang_code = get_language_from_context(self.context)
        return obj.get_label(lang_code)


class TopicDefinitionSerializer(serializers.ModelSerializer):
    """Serializer for topic dictionary definitions."""

    source_name = serializers.CharField(source="get_source_display", read_only=True)

    class Meta:
        model = TopicDefinition
        fields = [
            "id",
            "source",
            "source_name",
            "text",
            "text_length",
            "extracted_refs",
            "refs_count",
            "processed_at",
        ]


class TopicThemeLinkSerializer(serializers.ModelSerializer):
    """Serializer for topic-theme links with full metadata."""

    theme_id = serializers.IntegerField(source="theme.id", read_only=True)
    theme_name = serializers.CharField(source="theme.name", read_only=True)
    label = serializers.SerializerMethodField()
    theological_domain_display = serializers.CharField(
        source="get_theological_domain_display",
        read_only=True,
    )

    class Meta:
        model = TopicThemeLink
        fields = [
            "id",
            "theme_id",
            "theme_name",
            "proposal_id",
            "label",
            "label_original",
            "label_en",
            "label_normalized",
            "anchor_verses",
            "anchor_source",
            "anchor_meta",
            "semantic_keywords",
            "theological_domain",
            "theological_domain_display",
            "aspect",
            "relevance_score",
            "confidence",
            "source",
        ]

    def get_label(self, obj) -> str:
        """Get label based on language."""
        lang_code = get_language_from_context(self.context)
        if lang_code.startswith("pt"):
            return obj.label_original or obj.label_en
        return obj.label_en or obj.label_original


class TopicCrossReferenceSerializer(serializers.ModelSerializer):
    """Serializer for topic cross-references."""

    class Meta:
        model = TopicCrossReference
        fields = [
            "id",
            "cross_reference",
            "relevance_score",
            "aspect",
            "created_at",
        ]


class TopicRelationSerializer(serializers.ModelSerializer):
    """Serializer for topic relations."""

    target_slug = serializers.CharField(source="target.slug", read_only=True)
    target_name = serializers.SerializerMethodField()
    relation_type_display = serializers.CharField(source="get_relation_type_display", read_only=True)

    class Meta:
        model = TopicRelation
        fields = [
            "id",
            "target_slug",
            "target_name",
            "relation_type",
            "relation_type_display",
        ]

    def get_target_name(self, obj) -> str:
        """Get localized target name."""
        lang_code = get_language_from_context(self.context)
        return obj.target.get_display_name(lang_code)


class TopicSearchResultSerializer(serializers.Serializer):
    """Serializer for topic search results."""

    slug = serializers.CharField()
    name = serializers.CharField()
    topic_type = serializers.CharField()
    summary_preview = serializers.CharField(allow_blank=True)
    total_verses = serializers.IntegerField()
    match_type = serializers.CharField(help_text="Type of match: name, alias, content")
    match_score = serializers.FloatField(help_text="Relevance score")


class TopicStatisticsSerializer(serializers.Serializer):
    """Statistics data for a specific topic."""

    topic_slug = serializers.CharField()
    topic_name = serializers.CharField()
    topic_type = serializers.CharField()
    total_verses = serializers.IntegerField()
    ot_refs = serializers.IntegerField()
    nt_refs = serializers.IntegerField()
    books_count = serializers.IntegerField()
    aspects_count = serializers.IntegerField()
    definitions_count = serializers.IntegerField()
    themes_count = serializers.IntegerField()
    cross_references_count = serializers.IntegerField()
    testament_distribution = serializers.DictField(help_text="Verse count by testament")
    top_books = serializers.ListSerializer(
        child=serializers.DictField(),
        help_text="Books with most references",
    )


class TopicByLetterSerializer(serializers.Serializer):
    """Serializer for topics grouped by letter."""

    letter = serializers.CharField()
    count = serializers.IntegerField()
    topics = TopicListSerializer(many=True)
