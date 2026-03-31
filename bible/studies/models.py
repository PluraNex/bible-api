"""
Studies models - User-authored biblical studies with rich block-based content.

Key design decisions:
1. Studies are authored by users (not system-generated)
2. Content stored as JSONField blocks array (narrative document format)
3. Blocks are validated at serializer layer, not DB (flexible schema)
4. Three visibility levels: private, public, community
5. Fork support for building on others' public studies
6. Source tracking for studies seeded from validation data or plans
"""

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.db import models


class StudyType(models.TextChoices):
    """Classification of study content."""

    EVENT = "event", "Biblical Event"
    TYPOLOGY = "typology", "Typology / Type-Antitype"
    DOCTRINE = "doctrine", "Doctrine / Theology"
    MYSTICAL = "mystical", "Mystical / Contemplative"
    CHARACTER = "character", "Character Study"
    THEMATIC = "thematic", "Thematic Study"
    BOOK = "book", "Book Study"
    PASSAGE = "passage", "Passage / Pericope"
    DEVOTIONAL = "devotional", "Devotional"
    FREEFORM = "freeform", "Free Form"


class DifficultyLevel(models.TextChoices):
    """Study depth / complexity level."""

    BASE = "base", "Baseline"
    MEDIUM = "medium", "Medium"
    MEDIUM_HARD = "medium_hard", "Medium-Hard"
    HARD = "hard", "Hard"
    EXTREME = "extreme", "Extreme"


class Visibility(models.TextChoices):
    """Who can see this study."""

    PRIVATE = "private", "Private"
    PUBLIC = "public", "Public"
    COMMUNITY = "community", "Community"


class Study(models.Model):
    """
    A user-authored biblical study with rich narrative content.

    The study is a document composed of ordered blocks (paragraphs, verse
    citations, commentary quotes, diagrams, etc.). It is an article, not a
    dashboard — the author's voice is the main content, and API data appears
    as inline citations and embeds.
    """

    # Identity
    slug = models.SlugField(max_length=200, unique=True, db_index=True)
    title = models.CharField(max_length=300)
    subtitle = models.CharField(max_length=500, blank=True, default="")

    # Authorship
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="studies",
    )

    # Classification
    study_type = models.CharField(
        max_length=20,
        choices=StudyType.choices,
        default=StudyType.FREEFORM,
    )
    difficulty = models.CharField(
        max_length=20,
        choices=DifficultyLevel.choices,
        blank=True,
        default="",
    )
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
    )

    # Document content — ordered array of narrative blocks
    # Each block: {id, type, order, data, meta}
    # See block_validator.py for the 15 block type schemas
    blocks = models.JSONField(
        default=list,
        help_text="Ordered array of content blocks [{id, type, order, data, meta}]",
    )

    # Metadata
    description = models.TextField(
        blank=True,
        default="",
        help_text="Short description for listings and previews",
    )
    cover_image_url = models.URLField(blank=True, default="")
    tags = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Tags for categorization and search",
    )
    language = models.CharField(max_length=10, default="pt-BR")

    # Origin tracking
    source_plan_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="ID of the study plan that originated this study",
    )
    source_topic = models.ForeignKey(
        "bible.Topic",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="derived_studies",
    )
    source_validation_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
        db_index=True,
        help_text="Original validation ID (e.g., v3_base_01) if seeded",
    )

    # Publishing
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    # Engagement
    view_count = models.PositiveIntegerField(default=0)
    fork_count = models.PositiveIntegerField(default=0)

    # Fork tracking
    forked_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="forks",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "studies"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["author", "visibility"], name="study_author_vis_idx"),
            models.Index(fields=["visibility", "is_published"], name="study_vis_pub_idx"),
            models.Index(fields=["study_type"], name="study_type_idx"),
            GinIndex(fields=["tags"], name="study_tags_gin"),
        ]

    def __str__(self):
        return f"{self.title} ({self.slug})"

    @property
    def block_count(self):
        """Number of content blocks in the study."""
        return len(self.blocks) if self.blocks else 0


class StudyBookmark(models.Model):
    """User bookmark on a study for quick access."""

    study = models.ForeignKey(
        Study,
        on_delete=models.CASCADE,
        related_name="bookmarks",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_bookmarks",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "study_bookmarks"
        unique_together = ["study", "user"]

    def __str__(self):
        return f"{self.user} -> {self.study.slug}"
