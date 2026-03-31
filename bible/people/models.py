"""
Person — Unified identity hub for all person-like entities.

This is the central identity model that links:
- Author (commentaries domain) — Church Fathers, Reformers, modern commentators
- CanonicalEntity (entities domain) — Biblical figures (PERSON/DEITY namespace)
- Future: Book authors, image subjects, etc.

Design principle: thin hub with ~10 fields. Rich metadata stays in domain-specific
extension models (Author, CanonicalEntity) linked via OneToOneField.
"""

from django.db import models
from django.utils.text import slugify


class PersonType(models.TextChoices):
    BIBLICAL = "biblical", "Biblical Figure"
    HISTORICAL = "historical", "Historical Figure"
    AUTHOR = "author", "Commentary Author"
    MIXED = "mixed", "Biblical + Historical Author"


class Person(models.Model):
    """
    Thin identity hub for people across all domains.

    Examples:
    - Paul the Apostle (MIXED): has author_profile (epistles) + biblical_profile (entity)
    - Augustine of Hippo (AUTHOR): has author_profile only
    - King David (BIBLICAL): has biblical_profile only
    - C.H. Spurgeon (AUTHOR): has author_profile only
    """

    # Identity
    canonical_name = models.CharField(
        max_length=200,
        help_text="Primary display name (e.g., 'Augustine of Hippo')",
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        db_index=True,
        help_text="URL-safe identifier (e.g., 'augustine-of-hippo')",
    )
    person_type = models.CharField(
        max_length=20,
        choices=PersonType.choices,
        help_text="Primary classification of this person",
    )

    # Minimal shared fields (duplicated intentionally for fast access without joins)
    birth_year = models.CharField(
        max_length=50,
        blank=True,
        help_text="Birth year, approximate allowed (e.g., '354', '~1040 BC')",
    )
    death_year = models.CharField(
        max_length=50,
        blank=True,
        help_text="Death year, approximate allowed (e.g., '430', '~970 BC')",
    )
    description = models.TextField(
        blank=True,
        help_text="Brief description (1-2 sentences)",
    )
    wikipedia_url = models.URLField(max_length=500, blank=True)
    portrait_image = models.URLField(max_length=500, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "people_person"
        ordering = ["canonical_name"]
        verbose_name = "Person"
        verbose_name_plural = "People"
        indexes = [
            models.Index(fields=["person_type"], name="people_type_idx"),
            models.Index(fields=["slug"], name="people_slug_idx"),
        ]

    def __str__(self):
        return self.canonical_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self) -> str:
        base = slugify(self.canonical_name)[:110]
        slug = base
        counter = 1
        while Person.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base}-{counter}"
            counter += 1
        return slug

    @property
    def has_author_profile(self) -> bool:
        return hasattr(self, "author_profile") and self.author_profile is not None

    @property
    def has_biblical_profile(self) -> bool:
        return hasattr(self, "biblical_profile") and self.biblical_profile is not None
