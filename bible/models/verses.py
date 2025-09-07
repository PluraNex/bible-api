"""
Verse and Version models.
"""
from django.db import models

from .books import Book


class Version(models.Model):
    """
    Bible version/translation.
    """

    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=10, unique=True)
    language = models.CharField(max_length=10, default="en")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        db_table = "versions"
        indexes = [
            models.Index(fields=["language", "is_active"]),
            models.Index(fields=["abbreviation"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"


class Verse(models.Model):
    """
    Individual verse content.
    """

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="verses")
    version = models.ForeignKey(Version, on_delete=models.CASCADE, related_name="verses")
    chapter = models.PositiveIntegerField()
    number = models.PositiveIntegerField()
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["book__order", "chapter", "number"]
        unique_together = ["book", "version", "chapter", "number"]
        db_table = "verses"
        indexes = [
            models.Index(fields=["book", "chapter", "number"]),
            models.Index(fields=["version", "book"]),
        ]

    def __str__(self):
        return f"{self.book.abbreviation} {self.chapter}:{self.number} ({self.version.abbreviation})"

    @property
    def reference(self):
        """Human-readable verse reference."""
        return f"{self.book.name} {self.chapter}:{self.number}"
