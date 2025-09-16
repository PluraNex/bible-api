"""
Verse models following complete blueprint architecture.
"""
from django.db import models

from .books import CanonicalBook
from .versions import Version


class Verse(models.Model):
    """
    Individual verse content with canonical book reference.
    """

    book = models.ForeignKey(CanonicalBook, on_delete=models.CASCADE, related_name="verses")
    version = models.ForeignKey(Version, on_delete=models.CASCADE, related_name="verses")
    chapter = models.PositiveIntegerField()
    number = models.PositiveIntegerField()
    text = models.TextField()
    themes = models.ManyToManyField("Theme", through="bible.VerseTheme", related_name="verses", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["book__canonical_order", "chapter", "number"]
        unique_together = ["book", "version", "chapter", "number"]
        db_table = "verses"
        indexes = [
            models.Index(fields=["book", "chapter", "number"]),
            models.Index(fields=["version", "book"]),
        ]

    def __str__(self):
        return f"{self.book.osis_code} {self.chapter}:{self.number} ({self.version.abbreviation})"

    @property
    def reference(self):
        """Human-readable verse reference using version's language."""
        book_name = self.book.names.filter(language=self.version.language, version=self.version).first()

        if not book_name:
            book_name = self.book.names.filter(language=self.version.language, version__isnull=True).first()

        display_name = book_name.name if book_name else self.book.osis_code
        return f"{display_name} {self.chapter}:{self.number}"
