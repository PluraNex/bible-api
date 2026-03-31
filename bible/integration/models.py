"""
Cross-domain bridge tables for Image ↔ Entity linking.

Anti-Corruption Layer: connects Images domain with Entities domain
without either domain depending on the other directly.
"""

from django.db import models


class ImageEntityLink(models.Model):
    """
    Links a biblical image to a canonical entity (person, place, deity, etc.)
    or to a Person hub record (for post-biblical saints/authors).

    Populated by the matching pipeline, not real-time.
    """

    image = models.ForeignKey(
        "images.BiblicalImage",
        on_delete=models.CASCADE,
        related_name="entity_links",
    )

    # Target: either a CanonicalEntity OR a Person (one must be set)
    entity = models.ForeignKey(
        "entities.CanonicalEntity",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="image_links",
    )
    person = models.ForeignKey(
        "people.Person",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="image_links",
    )

    # Original tag data
    character_name = models.CharField(
        max_length=200,
        help_text="Original character name from image tag",
    )
    character_type = models.CharField(
        max_length=20,
        blank=True,
        help_text="Character type from tag: PERSON, DEITY, ANGEL, GROUP, OTHER",
    )

    # Match metadata
    match_method = models.CharField(
        max_length=20,
        choices=[
            ("exact", "Exact match on primary_name"),
            ("alias", "Match via EntityAlias"),
            ("fuzzy", "Fuzzy match (SequenceMatcher)"),
            ("tagger_index", "Match via tagger gazetteer index"),
            ("manual", "Manual curation"),
        ],
        help_text="How this match was made",
    )
    confidence = models.FloatField(
        default=1.0,
        help_text="Match confidence (0.0-1.0)",
    )
    verified = models.BooleanField(
        default=False,
        help_text="Has this match been manually verified?",
    )

    class Meta:
        db_table = "image_entity_link"
        verbose_name = "Image-Entity Link"
        indexes = [
            models.Index(fields=["image"]),
            models.Index(fields=["entity"]),
            models.Index(fields=["person"]),
            models.Index(fields=["match_method"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(entity__isnull=False, person__isnull=True)
                    | models.Q(entity__isnull=True, person__isnull=False)
                    | models.Q(entity__isnull=True, person__isnull=True)  # unmatched
                ),
                name="image_entity_link_one_target",
            ),
        ]

    def __str__(self):
        target = self.entity or self.person or "unmatched"
        return f"{self.character_name} → {target} ({self.match_method})"
