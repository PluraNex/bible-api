"""
Version models following complete blueprint architecture.
"""
from django.db import models

from .books import Language, License


class Version(models.Model):
    """
    Bible version/translation with full internationalization support.
    """

    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name="versions", null=True)
    code = models.CharField(max_length=40, db_index=True, default="EN_UNKNOWN")  # ex: 'PT-BR_ARA', 'EN_KJV'
    name = models.CharField(max_length=100)
    versification = models.CharField(max_length=40, default="KJV")  # 'KJV','Vulgate',...
    copyright = models.CharField(max_length=200, blank=True, default="")
    permissions = models.TextField(blank=True, default="")
    license = models.ForeignKey(License, on_delete=models.SET_NULL, null=True, blank=True, related_name="versions")
    source_url = models.URLField(blank=True, default="")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "versions"
        ordering = ["language_id", "code"]
        constraints = [
            models.UniqueConstraint(fields=["language", "code"], name="uniq_version_language_code"),
        ]
        indexes = [
            models.Index(fields=["language", "is_active"]),
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def abbreviation(self):
        """Generate abbreviation from code."""
        return self.code.split("_")[-1] if "_" in self.code else self.code
