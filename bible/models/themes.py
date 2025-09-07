"""
Theme and VerseTheme models for Bible API (biblical themes, not UI styles).
"""
from django.db import models

from .verses import Verse


class Theme(models.Model):
    """Biblical theme or concept applied across verses/books."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "themes"
        ordering = ["name"]
        indexes = [models.Index(fields=["name"]) ]

    def __str__(self):
        return self.name


class VerseTheme(models.Model):
    """Association between a verse and a biblical theme."""

    verse = models.ForeignKey(Verse, on_delete=models.CASCADE, related_name="theme_links")
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name="verse_links")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "verse_themes"
        constraints = [
            models.UniqueConstraint(fields=["verse", "theme"], name="uniq_verse_theme"),
        ]
        indexes = [
            models.Index(fields=["theme"], name="vt_theme_idx"),
        ]

    def __str__(self):
        return f"{self.verse_id} ~ {self.theme.name}"
