"""
Topic models for Bible API (topical references/encyclopedia entries).

Follows the BookName pattern for i18n support and Domain-Driven Design principles:
- Topic = Canonical entry (language-agnostic)
- TopicName = Localized names/aliases
- TopicContent = Localized content (summary, outline, etc.)
- TopicDefinition = Dictionary definitions from sources (EAS, SMI, NAV, etc.)
- TopicThemeLink = AI-extracted themes with full metadata
- TopicCrossReference = Cross-reference network from TSK
"""

from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.db import models

from .books import Language
from .crossrefs import CrossReference
from .themes import Theme
from .verses import Verse


class Topic(models.Model):
    """
    Biblical topic/encyclopedia entry from Nave's, Torrey's, etc.

    Canonical entry - language-agnostic.
    Names and content are stored in TopicName and TopicContent.
    """

    class TopicType(models.TextChoices):
        PERSON = "person", "Person"
        PLACE = "place", "Place"
        CONCEPT = "concept", "Concept"
        EVENT = "event", "Event"
        OBJECT = "object", "Object"
        LITERARY = "literary", "Literary Term"

    # === Identification ===
    slug = models.SlugField(max_length=150, unique=True, db_index=True)
    canonical_id = models.CharField(max_length=100, unique=True)  # "UNIFIED:abraham"
    canonical_name = models.CharField(max_length=200)  # "ABRAHAM"
    name_normalized = models.CharField(max_length=200, db_index=True)  # "abraham"

    # Topic type for classification
    topic_type = models.CharField(
        max_length=20,
        choices=TopicType.choices,
        default=TopicType.CONCEPT,
        db_index=True,
    )

    # === Sources ===
    primary_source = models.CharField(max_length=10)  # "NAV", "TOR"
    available_sources = ArrayField(
        models.CharField(max_length=10),
        default=list,
        blank=True,
    )

    # === Statistics (language-agnostic) ===
    total_verses = models.IntegerField(default=0)
    ot_refs = models.IntegerField(default=0)
    nt_refs = models.IntegerField(default=0)
    books_count = models.IntegerField(default=0)
    aspects_count = models.IntegerField(default=0)

    # Engagement metrics (for analytics/ranking)
    view_count = models.IntegerField(default=0)

    # === AI Enrichment ===
    ai_enriched = models.BooleanField(default=False)
    ai_model = models.CharField(max_length=50, blank=True)
    ai_confidence = models.FloatField(default=0.0)
    ai_enriched_at = models.DateTimeField(null=True, blank=True)
    ai_run_id = models.CharField(max_length=100, blank=True, db_index=True)

    # === Quality ===
    quality_score = models.FloatField(default=0.0)
    needs_review = models.BooleanField(default=False)
    review_notes = models.TextField(blank=True)

    # === Timestamps ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "topics"
        ordering = ["name_normalized"]
        indexes = [
            models.Index(fields=["name_normalized"]),
            models.Index(fields=["primary_source"]),
            models.Index(fields=["ai_enriched"]),
            models.Index(fields=["topic_type"]),
            models.Index(fields=["quality_score"]),
            models.Index(
                fields=["topic_type", "ai_enriched"],
                name="topic_type_enriched_idx",
            ),
        ]

    def __str__(self):
        return self.canonical_name

    def get_display_name(self, language_code: str = "en") -> str:
        """Get localized display name with fallback logic."""
        # Try exact match
        name_obj = self.names.filter(language__code=language_code).first()
        if name_obj:
            return name_obj.name

        # Fallback: pt-BR -> pt
        if language_code.startswith("pt"):
            name_obj = self.names.filter(language__code="pt").first()
            if name_obj:
                return name_obj.name

        # Fallback: en
        name_obj = self.names.filter(language__code="en").first()
        if name_obj:
            return name_obj.name

        return self.canonical_name


class TopicName(models.Model):
    """
    Topic names and aliases by language.
    Follows the BookName pattern.
    """

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="names")
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name="topic_names")

    name = models.CharField(max_length=200)  # "Abraão" (pt), "Abraham" (en)
    aliases = ArrayField(
        models.CharField(max_length=200),
        default=list,
        blank=True,
    )  # ["Abrão"]

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "topic_names"
        ordering = ["topic", "language"]
        constraints = [
            models.UniqueConstraint(
                fields=["topic", "language"],
                name="uniq_topic_name_per_language",
            ),
        ]
        indexes = [
            models.Index(fields=["topic", "language"], name="topicname_topic_lang_idx"),
            models.Index(fields=["name"]),
            GinIndex(fields=["aliases"], name="topicname_aliases_gin"),
        ]

    def __str__(self):
        return f"{self.name} [{self.language.code}]"


class TopicContent(models.Model):
    """
    Localized content for a Topic.
    Allows summary, outline, and theological content in multiple languages.
    """

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="contents")
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name="topic_contents")

    # Localized content
    summary = models.TextField(blank=True)  # AI-generated summary
    outline = ArrayField(models.TextField(), default=list, blank=True)
    key_concepts = ArrayField(models.CharField(max_length=200), default=list, blank=True)
    theological_significance = models.TextField(blank=True)

    # Raw content (original source material)
    primary_content = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "topic_contents"
        constraints = [
            models.UniqueConstraint(
                fields=["topic", "language"],
                name="uniq_topic_content_per_language",
            ),
        ]
        indexes = [
            models.Index(fields=["topic", "language"], name="topiccontent_topic_lang_idx"),
        ]

    def __str__(self):
        return f"Content for {self.topic.slug} [{self.language.code}]"


class TopicDefinition(models.Model):
    """
    Dictionary definitions for a Topic from different sources.

    Sources:
    - EAS: Easton's Bible Dictionary
    - SMI: Smith's Bible Dictionary
    - NAV: Nave's Topical Bible (index entries)
    - TOR: Torrey's Topical Textbook
    - ATS: American Tract Society Dictionary
    - ISB: International Standard Bible Encyclopedia
    """

    class SourceType(models.TextChoices):
        EAS = "EAS", "Easton's Bible Dictionary"
        SMI = "SMI", "Smith's Bible Dictionary"
        NAV = "NAV", "Nave's Topical Bible"
        TOR = "TOR", "Torrey's Topical Textbook"
        ATS = "ATS", "American Tract Society Dictionary"
        ISB = "ISB", "International Standard Bible Encyclopedia"

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="definitions")

    source = models.CharField(max_length=3, choices=SourceType.choices, db_index=True)

    # Raw dictionary content (language-agnostic, generally in English)
    text = models.TextField()
    text_length = models.IntegerField(default=0)  # For sorting/pagination

    # References automatically extracted from text
    extracted_refs = models.JSONField(default=list)  # Array of {book, chapter, verses, ...}
    refs_count = models.IntegerField(default=0)

    # Processing metadata
    processed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "topic_definitions"
        ordering = ["topic", "source"]
        constraints = [
            models.UniqueConstraint(
                fields=["topic", "source"],
                name="uniq_topic_definition_source",
            ),
        ]
        indexes = [
            models.Index(fields=["source"]),
            models.Index(fields=["refs_count"]),
        ]

    def __str__(self):
        return f"{self.topic.slug} ({self.source})"

    def save(self, *args, **kwargs):
        self.text_length = len(self.text)
        self.refs_count = len(self.extracted_refs) if self.extracted_refs else 0
        super().save(*args, **kwargs)


class TopicAspect(models.Model):
    """
    Structured aspect/subtopic within a Topic.

    Maps to `reference_groups` from JSON:
    - "Divine call of" → aspect with references [Gn 12:1, Hb 11:8, ...]
    """

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="aspects")

    # Canonical label (English)
    canonical_label = models.CharField(max_length=500)

    # Slug for friendly URLs
    slug = models.SlugField(max_length=150, blank=True)

    order = models.IntegerField(default=0)

    # Raw references (preserves original format from JSON)
    # Ex: ["Gn 12:1", "Hb 11:8"]
    raw_references = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
    )

    # Aspect statistics
    verse_count = models.IntegerField(default=0)
    ot_refs = models.IntegerField(default=0)
    nt_refs = models.IntegerField(default=0)

    # Books where it appears (OSIS codes)
    books = ArrayField(models.CharField(max_length=20), default=list, blank=True)

    # Aspect source
    source = models.CharField(max_length=10, default="NAV")  # NAV, TOR, AI

    class Meta:
        db_table = "topic_aspects"
        ordering = ["topic", "order"]
        indexes = [
            models.Index(fields=["topic", "order"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return f"{self.topic.slug}: {self.canonical_label[:50]}"

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify

            self.slug = slugify(self.canonical_label[:100])
        super().save(*args, **kwargs)

    def get_label(self, language_code: str = "en") -> str:
        """Get localized label with fallback logic."""
        label_obj = self.labels.filter(language__code=language_code).first()
        if label_obj:
            return label_obj.label

        # Fallback
        if language_code.startswith("pt"):
            label_obj = self.labels.filter(language__code="pt").first()
            if label_obj:
                return label_obj.label

        label_obj = self.labels.filter(language__code="en").first()
        if label_obj:
            return label_obj.label

        return self.canonical_label


class TopicAspectLabel(models.Model):
    """
    Localized labels for TopicAspect.
    """

    aspect = models.ForeignKey(TopicAspect, on_delete=models.CASCADE, related_name="labels")
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name="aspect_labels")

    label = models.CharField(max_length=500)  # "Chamado divino de" (pt)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "topic_aspect_labels"
        constraints = [
            models.UniqueConstraint(
                fields=["aspect", "language"],
                name="uniq_aspect_label_per_language",
            ),
        ]

    def __str__(self):
        return f"{self.label[:50]} [{self.language.code}]"


class TopicVerse(models.Model):
    """
    Association between a Topic and a Verse.
    """

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="verse_links")
    verse = models.ForeignKey(Verse, on_delete=models.CASCADE, related_name="topic_links")
    aspect = models.ForeignKey(TopicAspect, on_delete=models.SET_NULL, null=True, blank=True)

    # Reference context
    relevance_score = models.FloatField(default=1.0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "topic_verses"
        constraints = [
            models.UniqueConstraint(fields=["topic", "verse"], name="uniq_topic_verse"),
        ]
        indexes = [
            models.Index(fields=["topic"]),
            models.Index(fields=["verse"]),
        ]

    def __str__(self):
        return f"{self.topic.slug} ~ {self.verse.reference}"


class TopicThemeLink(models.Model):
    """
    AI-extracted themes for a Topic with full metadata.

    Maps to `ai_themes_normalized[]` from JSON.
    This is a rich link table with analysis results.
    """

    class TheologicalDomain(models.TextChoices):
        THEOLOGY_PROPER = "theology_proper", "Theology Proper (God)"
        CHRISTOLOGY = "christology", "Christology (Christ)"
        PNEUMATOLOGY = "pneumatology", "Pneumatology (Holy Spirit)"
        ANTHROPOLOGY = "anthropology", "Anthropology (Humanity)"
        HAMARTIOLOGY = "hamartiology", "Hamartiology (Sin)"
        SOTERIOLOGY = "soteriology", "Soteriology (Salvation)"
        ECCLESIOLOGY = "ecclesiology", "Ecclesiology (Church)"
        ESCHATOLOGY = "eschatology", "Eschatology (End Times)"
        BIBLIOLOGY = "bibliology", "Bibliology (Scripture)"
        ANGELOLOGY = "angelology", "Angelology (Angels/Demons)"
        ETHICS = "ethics", "Ethics/Morality"
        WORSHIP = "worship", "Worship/Liturgy"

    class AnchorSource(models.TextChoices):
        AI_TRUSTED = "ai_trusted", "AI Trusted"
        AI_FALLBACK = "ai_fallback", "AI Fallback"
        MANUAL = "manual", "Manual/Curated"
        DERIVED = "derived", "Derived from Data"

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="theme_links")
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name="topic_sources")

    # === Theme Identification ===
    # Preserve proposal_id for traceability
    proposal_id = models.CharField(max_length=100, blank=True, db_index=True)

    # Multilingual labels
    label_original = models.CharField(max_length=300)  # "Fé e obediência de Abraão"
    label_en = models.CharField(max_length=300)  # "Faith and Obedience"
    label_normalized = models.CharField(max_length=200, db_index=True)  # "faith_and_obedience"

    # === Anchor Verses (CRITICAL) ===
    anchor_verses = ArrayField(
        models.CharField(max_length=100),
        default=list,
        help_text="Key verses that anchor this theme, e.g., ['Genesis 12:1', 'Hebrews 11:8']",
    )
    anchor_source = models.CharField(
        max_length=20,
        choices=AnchorSource.choices,
        default=AnchorSource.AI_TRUSTED,
    )
    anchor_meta = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadata about anchor selection: ai_suggested, validated, fallback_used",
    )

    # === Semantic Analysis ===
    semantic_keywords = ArrayField(
        models.CharField(max_length=100),
        default=list,
        help_text="Keywords for semantic search: ['faith', 'obedience', 'trust']",
    )

    # === Theological Classification ===
    theological_domain = models.CharField(
        max_length=30,
        choices=TheologicalDomain.choices,
        blank=True,
    )

    # === Theme Hierarchy ===
    parent_theme = models.ForeignKey(
        Theme,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_topic_links",
    )

    # === Context ===
    aspect = models.TextField(blank=True)  # "A disposição de Abraão em seguir..."

    # === Metrics ===
    relevance_score = models.FloatField(default=0.0)  # 0-10
    confidence = models.FloatField(default=1.0)

    # === Provenance ===
    source = models.CharField(max_length=20, default="ai_enrichment")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "topic_theme_links"
        constraints = [
            models.UniqueConstraint(
                fields=["topic", "theme"],
                name="uniq_topic_theme_link",
            ),
        ]
        indexes = [
            models.Index(fields=["topic"]),
            models.Index(fields=["theme"]),
            models.Index(fields=["label_normalized"]),
            models.Index(fields=["theological_domain"]),
            models.Index(fields=["relevance_score"]),
            GinIndex(fields=["semantic_keywords"], name="topictheme_keywords_gin"),
            GinIndex(fields=["anchor_verses"], name="topictheme_anchors_gin"),
        ]

    def __str__(self):
        return f"{self.topic.slug} -> {self.theme.name}"


class TopicCrossReference(models.Model):
    """
    Link between a Topic and an existing CrossReference.

    Instead of duplicating cross-reference data, we link to the canonical
    CrossReference model. This maintains data integrity and reuses the
    existing cross-reference network (TSK, OpenBible, etc.).

    The cross_reference FK points to our existing CrossReference model,
    which already has: from_book, from_chapter, from_verse, to_book, etc.
    """

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="cross_references")

    # Link to the canonical cross-reference (DRY - no duplication)
    cross_reference = models.ForeignKey(
        CrossReference,
        on_delete=models.CASCADE,
        related_name="topic_links",
        help_text="Link to the canonical cross-reference",
    )

    # Topic-specific context/relevance
    relevance_score = models.FloatField(
        default=1.0,
        help_text="How relevant this cross-reference is to this specific topic (0-1)",
    )

    # Optional: which aspect of the topic this xref relates to
    aspect = models.ForeignKey(
        TopicAspect,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cross_references",
        help_text="Which aspect/subtopic this cross-reference relates to",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "topic_cross_references"
        indexes = [
            models.Index(fields=["topic"]),
            models.Index(fields=["cross_reference"]),
            models.Index(fields=["relevance_score"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["topic", "cross_reference"],
                name="uniq_topic_xref",
            ),
        ]

    def __str__(self):
        return f"{self.topic.slug} -> {self.cross_reference}"

    @property
    def from_reference(self) -> str:
        """Get the source reference in human-readable format."""
        xref = self.cross_reference
        return f"{xref.from_book.osis_code} {xref.from_chapter}:{xref.from_verse}"

    @property
    def to_reference(self) -> str:
        """Get the target reference in human-readable format."""
        xref = self.cross_reference
        to_range = f"{xref.to_verse_start}"
        if xref.to_verse_end > xref.to_verse_start:
            to_range += f"-{xref.to_verse_end}"
        return f"{xref.to_book.osis_code} {xref.to_chapter}:{to_range}"


class TopicRelation(models.Model):
    """
    Relations between Topics (see_also, related, etc.)
    """

    class RelationType(models.TextChoices):
        SEE_ALSO = "see_also", "See Also"
        RELATED = "related", "Related"
        PARENT = "parent", "Parent Topic"
        CHILD = "child", "Child Topic"
        ALIAS = "alias", "Alias"

    source = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="outgoing_relations")
    target = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="incoming_relations")

    relation_type = models.CharField(max_length=20, choices=RelationType.choices)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "topic_relations"
        constraints = [
            models.UniqueConstraint(
                fields=["source", "target", "relation_type"],
                name="uniq_topic_relation",
            ),
        ]

    def __str__(self):
        return f"{self.source.slug} --{self.relation_type}--> {self.target.slug}"


class TopicPipelineMetadata(models.Model):
    """
    Pipeline processing metadata for a Topic.

    Stores `phase1_discovery` and other pipeline artifacts for:
    - Processing audit
    - Reproducibility
    - Debugging
    """

    topic = models.OneToOneField(
        Topic,
        on_delete=models.CASCADE,
        related_name="pipeline_metadata",
    )

    # Phase 0: Initial processing
    phase0_processed_at = models.DateTimeField(null=True, blank=True)
    phase0_run_id = models.CharField(max_length=100, blank=True)

    # Phase 1: Theme discovery
    phase1_processed_at = models.DateTimeField(null=True, blank=True)
    phase1_summary = models.JSONField(default=dict, blank=True)
    phase1_results = models.JSONField(default=list, blank=True)

    # Phase 2: Entity resolution (future)
    phase2_processed_at = models.DateTimeField(null=True, blank=True)

    # Full JSON backup (compressed)
    raw_json_backup = models.BinaryField(null=True, blank=True)  # gzip compressed

    # Pipeline version
    pipeline_version = models.CharField(max_length=20, default="1.0")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "topic_pipeline_metadata"

    def __str__(self):
        return f"Pipeline metadata for {self.topic.slug}"
