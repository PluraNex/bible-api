"""
Book-related models.
"""
from django.db import models


class Book(models.Model):
    """
    Biblical book (66 canonical books).
    """

    name = models.CharField(max_length=50, unique=True)
    abbreviation = models.CharField(max_length=10, unique=True)
    order = models.PositiveIntegerField(unique=True)
    testament = models.CharField(max_length=3, choices=[("OLD", "Old Testament"), ("NEW", "New Testament")])
    chapter_count = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        db_table = "books"
        indexes = [
            models.Index(fields=["testament", "order"]),
            models.Index(fields=["abbreviation"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"
