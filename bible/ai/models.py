"""AI analysis tracking models."""

from django.db import models


class ChapterAnalysis(models.Model):
    """Track which chapters have been AI-analyzed for entity/symbol context."""

    book = models.ForeignKey(
        "bible.CanonicalBook",
        on_delete=models.CASCADE,
        related_name="ai_analyses",
    )
    chapter = models.PositiveIntegerField()
    analyzed_at = models.DateTimeField(auto_now=True)
    model_used = models.CharField(max_length=50, default="gpt-4o-mini")
    entities_found = models.PositiveIntegerField(default=0)
    symbols_found = models.PositiveIntegerField(default=0)
    links_created = models.PositiveIntegerField(default=0)
    links_removed = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "ai_chapter_analysis"
        unique_together = ["book", "chapter"]

    def __str__(self):
        return f"{self.book.osis_code} {self.chapter} (analyzed {self.analyzed_at})"
