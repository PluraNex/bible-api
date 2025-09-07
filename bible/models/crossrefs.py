"""
CrossReference model for Bible API.
"""
from django.db import models
from django.db.models import F, Q

from .verses import Verse


class CrossReference(models.Model):
    """
    Represents a cross-reference between two verses.
    Directional by default (from_verse -> to_verse), with optional relationship_type and source.
    """

    REL_TYPES = (
        ("parallel", "Parallel"),
        ("prophecy", "Prophecy"),
        ("quote", "Quote"),
        ("theme", "Theme Related"),
        ("other", "Other"),
    )

    from_verse = models.ForeignKey(Verse, on_delete=models.CASCADE, related_name="crossrefs_from")
    to_verse = models.ForeignKey(Verse, on_delete=models.CASCADE, related_name="crossrefs_to")
    relationship_type = models.CharField(max_length=20, choices=REL_TYPES, default="other")
    source = models.CharField(max_length=50, default="manual")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cross_references"
        ordering = ["from_verse_id", "to_verse_id"]
        indexes = [
            models.Index(fields=["from_verse"]),
            models.Index(fields=["to_verse"]),
            models.Index(fields=["relationship_type"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["from_verse", "to_verse", "source"], name="crossref_unique_from_to_source"
            ),
            models.CheckConstraint(
                check=~Q(from_verse=F("to_verse")), name="crossref_no_self_reference"
            ),
        ]

    def __str__(self):
        return f"{self.from_verse_id} -> {self.to_verse_id} ({self.relationship_type})"
