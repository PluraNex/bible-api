"""
Book-related models following the complete blueprint architecture.
"""
from django.db import models


class Language(models.Model):
    """Language for Bible versions and localization."""

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)  # ex: 'pt-BR', 'en'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "languages"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class License(models.Model):
    """License information for Bible versions."""

    code = models.CharField(max_length=50, unique=True)  # 'PD', 'CC-BY-SA-4.0'
    name = models.CharField(max_length=150)
    url = models.URLField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "licenses"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Testament(models.Model):
    """Biblical testaments (Old/New)."""

    name = models.CharField(max_length=45, blank=True, default="")  # AT/NT
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "testaments"
        ordering = ["id"]

    def __str__(self):
        return self.name or "Testament"


class CanonicalBook(models.Model):
    """
    Canonical biblical book, independent of language/version.
    One per book in the biblical canon.
    """

    osis_code = models.CharField(max_length=12, unique=True, default="Unknown")  # 'Gen','Exod','Ps','Matt',...
    canonical_order = models.PositiveIntegerField(unique=True, default=1)
    testament = models.ForeignKey(Testament, on_delete=models.CASCADE, related_name="canonical_books")
    is_deuterocanonical = models.BooleanField(default=False)
    chapter_count = models.PositiveIntegerField()
    outline_data = models.JSONField(null=True, blank=True, help_text="Structured outline data for the book")
    context_data = models.JSONField(
        null=True, blank=True, help_text="Historical and contextual information for the book"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "canonical_books"
        ordering = ["canonical_order"]
        constraints = [
            models.CheckConstraint(check=models.Q(canonical_order__gte=1), name="book_canonical_order_pos"),
        ]
        indexes = [
            models.Index(fields=["testament", "canonical_order"]),
            models.Index(fields=["osis_code"]),
        ]

    def __str__(self):
        return self.osis_code


class BookName(models.Model):
    """
    Book names/abbreviations by language and optionally by version.
    Allows different names for the same canonical book across languages/versions.
    """

    canonical_book = models.ForeignKey(CanonicalBook, on_delete=models.CASCADE, related_name="names")
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name="book_names")
    name = models.CharField(max_length=60)
    abbreviation = models.CharField(max_length=10, blank=True, default="")
    version = models.ForeignKey("Version", on_delete=models.CASCADE, null=True, blank=True, related_name="book_names")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "book_names"
        ordering = ["canonical_book_id", "language_id"]
        constraints = [
            # Generic by language (when version is NULL)
            models.UniqueConstraint(
                fields=["canonical_book", "language"],
                condition=models.Q(version__isnull=True),
                name="uniq_bookname_lang_when_version_null",
            ),
            # Specific by version
            models.UniqueConstraint(
                fields=["canonical_book", "language", "version"],
                condition=models.Q(version__isnull=False),
                name="uniq_bookname_lang_version_when_version_not_null",
            ),
        ]
        indexes = [
            models.Index(fields=["canonical_book", "language"], name="bookname_book_lang_idx"),
            models.Index(fields=["abbreviation"]),
        ]

    def __str__(self):
        suffix = f" ({self.version.code})" if self.version_id else ""
        return f"{self.name} [{self.language.code}]{suffix}"


# Keep old Book model as alias for backward compatibility during migration
class Book(CanonicalBook):
    """
    Legacy Book model - use CanonicalBook for new code.
    This will be deprecated after migration is complete.
    """

    class Meta:
        proxy = True

    @property
    def name(self):
        """Get default English name for backward compatibility."""
        book_name = self.names.filter(language__code="en", version__isnull=True).first()
        return book_name.name if book_name else self.osis_code

    @property
    def abbreviation(self):
        """Get default English abbreviation for backward compatibility."""
        book_name = self.names.filter(language__code="en", version__isnull=True).first()
        return book_name.abbreviation if book_name else self.osis_code[:3]

    @property
    def order(self):
        """Backward compatibility alias."""
        return self.canonical_order

    @property
    def testament_name(self):
        """Backward compatibility for testament string."""
        return "OLD" if self.testament_id == 1 else "NEW"
