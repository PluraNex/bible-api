"""
Themes models - Biblical themes with rich metadata and progression.

Key design decisions:
1. Theme = Rich theme model with multilingual support
2. ThemeCategory = Hierarchical organization of themes
3. ThemeProgression = How themes develop through biblical narrative (like SymbolProgression)
4. ThemeVerseLink = Rich verse associations with context and relevance
5. Integration with Theology domain for theological classification

This replaces the basic Theme model in bible/models/themes.py with a
full-featured domain model.
"""

from django.contrib.postgres.fields import ArrayField
from django.db import models


class ThemeStatus(models.TextChoices):
    """Theme curation status."""

    DRAFT = "draft", "Draft"
    REVIEW = "review", "Under Review"
    APPROVED = "approved", "Approved"
    CANONICAL = "canonical", "Canonical"


class ThemeCategory(models.Model):
    """
    Categories for organizing themes hierarchically.

    Examples:
    - Salvation Themes
      - Grace
      - Faith
      - Redemption
    - Character Themes
      - Love
      - Patience
      - Humility
    - Eschatological Themes
      - Second Coming
      - Judgment
      - New Creation
    """

    slug = models.SlugField(max_length=100, unique=True)

    # Names
    name_en = models.CharField(max_length=200)
    name_pt = models.CharField(max_length=200, blank=True)

    # Description
    description_en = models.TextField(blank=True)
    description_pt = models.TextField(blank=True)

    # Hierarchy
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )

    # UI
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=20, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "theme_category"
        verbose_name = "Theme Category"
        verbose_name_plural = "Theme Categories"
        ordering = ["display_order", "name_en"]

    def __str__(self):
        return self.name_en


class Theme(models.Model):
    """
    A biblical theme - a concept or topic that spans Scripture.

    Themes are different from:
    - Topics: Encyclopedia entries about specific subjects
    - Doctrines: Systematic theological formulations
    - Symbols: Visual/literary representations

    Themes are concepts like:
    - Faith
    - Redemption
    - Covenant
    - Kingdom of God
    - Grace
    - Love
    - Justice

    Each theme:
    - Has multilingual names and descriptions
    - Is classified by theological domain
    - Has anchor verses
    - Shows progression through Scripture
    - Can be related to other themes
    """

    # === IDENTIFICATION ===
    slug = models.SlugField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="URL-safe identifier (e.g., 'faith_and_obedience')",
    )

    # Multilingual names
    name_en = models.CharField(max_length=200)
    name_pt = models.CharField(max_length=200, blank=True)
    name_original = models.CharField(
        max_length=200,
        blank=True,
        help_text="Original Hebrew/Greek term if applicable",
    )

    # Normalized label (for matching from AI)
    label_normalized = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Normalized form for matching (e.g., 'faith_and_obedience')",
    )

    # === DESCRIPTIONS ===
    # Short description for cards
    description_short_en = models.TextField(
        blank=True,
        help_text="One-sentence description",
    )
    description_short_pt = models.TextField(blank=True)

    # Full description
    description_en = models.TextField(blank=True)
    description_pt = models.TextField(blank=True)

    # === THEOLOGICAL CLASSIFICATION ===
    # Link to theology domain
    theological_domain = models.ForeignKey(
        "theology.TheologicalDomain",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="themes",
        help_text="Primary theological domain",
    )

    # Link to specific doctrine if applicable
    primary_doctrine = models.ForeignKey(
        "theology.Doctrine",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="themes",
        help_text="Primary related doctrine",
    )

    # === CATEGORIZATION ===
    category = models.ForeignKey(
        ThemeCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="themes",
    )

    # Hierarchy
    parent_theme = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_themes",
        help_text="Parent theme for hierarchy",
    )

    # === SEMANTIC DATA ===
    semantic_keywords = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Keywords for semantic search (e.g., ['faith', 'trust', 'belief'])",
    )

    # === ANCHOR VERSES ===
    anchor_verses = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Key verses that define this theme",
    )

    class AnchorSource(models.TextChoices):
        AI_TRUSTED = "ai_trusted", "AI Trusted"
        AI_FALLBACK = "ai_fallback", "AI Fallback"
        MANUAL = "manual", "Manual/Curated"
        DERIVED = "derived", "Derived from Data"

    anchor_source = models.CharField(
        max_length=20,
        choices=AnchorSource.choices,
        default=AnchorSource.MANUAL,
    )

    # === ETYMOLOGY ===
    hebrew_term = models.CharField(max_length=100, blank=True)
    hebrew_transliteration = models.CharField(max_length=100, blank=True)
    greek_term = models.CharField(max_length=100, blank=True)
    greek_transliteration = models.CharField(max_length=100, blank=True)
    strongs_hebrew = ArrayField(
        models.CharField(max_length=20),
        default=list,
        blank=True,
        help_text="Related Strong's Hebrew numbers",
    )
    strongs_greek = ArrayField(
        models.CharField(max_length=20),
        default=list,
        blank=True,
        help_text="Related Strong's Greek numbers",
    )

    # === SEARCH & RANKING ===
    boost = models.FloatField(
        default=1.0,
        help_text="Search ranking boost",
    )
    priority = models.PositiveIntegerField(
        default=50,
        help_text="Display priority (1-100)",
    )

    # === STATUS ===
    status = models.CharField(
        max_length=20,
        choices=ThemeStatus.choices,
        default=ThemeStatus.DRAFT,
    )

    # === STUDY METRICS ===
    study_value = models.PositiveIntegerField(
        default=50,
        help_text="Educational value (1-100)",
    )
    difficulty_level = models.PositiveIntegerField(
        default=50,
        help_text="Complexity level (1-100)",
    )
    verse_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of verses associated with this theme",
    )
    topic_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of topics associated with this theme",
    )

    # === AI ENRICHMENT ===
    ai_enriched = models.BooleanField(default=False)
    ai_enriched_at = models.DateTimeField(null=True, blank=True)
    ai_summary = models.TextField(
        blank=True,
        help_text="AI-generated comprehensive summary",
    )
    ai_summary_pt = models.TextField(blank=True)
    ai_insights = models.TextField(
        blank=True,
        help_text="AI-generated theological insights",
    )
    ai_practical_application = models.TextField(
        blank=True,
        help_text="AI-generated practical applications",
    )

    # === UI/UX ===
    icon = models.CharField(max_length=50, blank=True)
    emoji = models.CharField(max_length=10, blank=True)
    color = models.CharField(max_length=20, blank=True)

    # === ENGAGEMENT ===
    view_count = models.PositiveIntegerField(default=0)
    bookmark_count = models.PositiveIntegerField(default=0)

    # === RESEARCH DATA ===
    evidence_score = models.FloatField(
        default=0.0,
        help_text="Evidence confidence score from multi-source validation (0-1)",
    )

    # === SOURCE TRACKING ===
    source_topics = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Topic keys that contributed to this theme",
    )

    # === METADATA ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "theme"
        verbose_name = "Theme"
        verbose_name_plural = "Themes"
        ordering = ["-priority", "name_en"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["theological_domain"]),
            models.Index(fields=["category"]),
            models.Index(fields=["label_normalized"]),
        ]

    def __str__(self):
        return f"{self.slug}: {self.name_en}"

    @property
    def all_progressions(self):
        """Get all progression stages for this theme."""
        return self.progressions.all().order_by("stage_order")


class ThemeRelatedTheme(models.Model):
    """
    Relationships between themes.

    Types of relationships:
    - SIMILAR: Themes with similar meaning
    - CONTRASTING: Themes that contrast each other
    - PREREQUISITE: Theme A should be understood before Theme B
    - DEVELOPS_INTO: Theme A develops into Theme B
    - FULFILLS: Theme A fulfills Theme B
    """

    class RelationType(models.TextChoices):
        SIMILAR = "similar", "Similar/Related"
        CONTRASTING = "contrasting", "Contrasting/Opposite"
        PREREQUISITE = "prerequisite", "Prerequisite For"
        DEVELOPS_INTO = "develops_into", "Develops Into"
        FULFILLS = "fulfills", "Fulfills"
        ASPECT_OF = "aspect_of", "Aspect Of"

    from_theme = models.ForeignKey(
        Theme,
        on_delete=models.CASCADE,
        related_name="outgoing_relations",
    )
    to_theme = models.ForeignKey(
        Theme,
        on_delete=models.CASCADE,
        related_name="incoming_relations",
    )
    relation_type = models.CharField(
        max_length=20,
        choices=RelationType.choices,
    )
    description = models.TextField(
        blank=True,
        help_text="Explanation of the relationship",
    )

    class Meta:
        db_table = "theme_related_theme"
        unique_together = ["from_theme", "to_theme", "relation_type"]

    def __str__(self):
        return f"{self.from_theme.slug} {self.relation_type} {self.to_theme.slug}"


class ThemeProgression(models.Model):
    """
    How a theme DEVELOPS through biblical narrative.

    This tracks the progressive revelation of a theme:
    - Covenant: Adamic → Noahic → Abrahamic → Mosaic → Davidic → New
    - Kingdom: Eden → Theocracy → Monarchy → Exile → Restoration → Christ's Kingdom → Eternal

    Similar to SymbolProgression but for themes.
    """

    theme = models.ForeignKey(
        Theme,
        on_delete=models.CASCADE,
        related_name="progressions",
    )

    # Stage identification
    stage_order = models.PositiveIntegerField(
        help_text="Order in the progression (1=earliest)",
    )
    stage_name_en = models.CharField(
        max_length=200,
        help_text="Name of this stage (e.g., 'Abrahamic Covenant')",
    )
    stage_name_pt = models.CharField(max_length=200, blank=True)

    # Description
    description_en = models.TextField(
        help_text="How the theme is understood at this stage",
    )
    description_pt = models.TextField(blank=True)

    # Biblical era/context
    biblical_era = models.CharField(
        max_length=100,
        blank=True,
        help_text="Era (e.g., 'Patriarchal', 'Exodus', 'Monarchy')",
    )
    primary_book = models.CharField(
        max_length=50,
        blank=True,
        help_text="Primary book for this stage",
    )
    key_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Key verse for this stage",
    )
    additional_references = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
    )

    # Testament focus
    class TestamentFocus(models.TextChoices):
        OLD = "old", "Old Testament"
        NEW = "new", "New Testament"
        INTERTESTAMENTAL = "intertestamental", "Intertestamental"

    testament_focus = models.CharField(
        max_length=20,
        choices=TestamentFocus.choices,
        default=TestamentFocus.OLD,
    )

    # Theological development
    theological_development_en = models.TextField(
        blank=True,
        help_text="What new understanding emerged at this stage",
    )
    theological_development_pt = models.TextField(blank=True)

    # Christological connection
    christological_connection_en = models.TextField(
        blank=True,
        help_text="How this stage points to Christ",
    )
    christological_connection_pt = models.TextField(blank=True)
    is_fulfilled_in_christ = models.BooleanField(
        default=False,
        help_text="Is this the stage where Christ fulfills the theme?",
    )

    # Eschatological dimension
    eschatological_note = models.TextField(
        blank=True,
        help_text="Future/eschatological implications",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "theme_progression"
        verbose_name = "Theme Progression"
        verbose_name_plural = "Theme Progressions"
        ordering = ["theme", "stage_order"]
        unique_together = ["theme", "stage_order"]

    def __str__(self):
        return f"{self.theme.slug} Stage {self.stage_order}: {self.stage_name_en}"


class ThemeVerseLink(models.Model):
    """
    Link between a theme and a verse with rich context.

    This is a more sophisticated version of VerseTheme that includes:
    - Relevance scoring
    - Context notes
    - How central the theme is to the verse
    - AI analysis
    """

    theme = models.ForeignKey(
        Theme,
        on_delete=models.CASCADE,
        related_name="verse_links",
    )
    verse = models.ForeignKey(
        "bible.Verse",
        on_delete=models.CASCADE,
        related_name="theme_links_rich",
    )

    # Relevance
    relevance_score = models.FloatField(
        default=1.0,
        help_text="How relevant is this theme to this verse (0-1)",
    )
    is_primary_theme = models.BooleanField(
        default=False,
        help_text="Is this the primary theme of the verse?",
    )

    # Context
    context_note_en = models.TextField(
        blank=True,
        help_text="How the theme appears in this verse",
    )
    context_note_pt = models.TextField(blank=True)

    # Which progression stage is this verse part of?
    progression_stage = models.ForeignKey(
        ThemeProgression,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verse_links",
        help_text="Which progression stage does this verse belong to?",
    )

    # Source
    class LinkSource(models.TextChoices):
        AI = "ai", "AI Generated"
        MANUAL = "manual", "Manual/Curated"
        IMPORTED = "imported", "Imported from Topic"
        CROSS_REF = "cross_ref", "Cross-Reference Based"

    source = models.CharField(
        max_length=20,
        choices=LinkSource.choices,
        default=LinkSource.AI,
    )

    # Grade (from graded relevance assessment)
    grade = models.PositiveSmallIntegerField(
        default=0,
        help_text="Quality grade: 3=primary (3+ sources), 2=secondary (2 sources), 1=supporting (1 source)",
    )

    # AI analysis
    ai_analysis = models.TextField(
        blank=True,
        help_text="AI analysis of how this theme appears in this verse",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "theme_verse_link"
        verbose_name = "Theme-Verse Link"
        verbose_name_plural = "Theme-Verse Links"
        unique_together = ["theme", "verse"]
        indexes = [
            models.Index(fields=["is_primary_theme"]),
            models.Index(fields=["relevance_score"]),
        ]

    def __str__(self):
        return f"{self.theme.slug} @ {self.verse}"
