"""
Commentary and Comment models following complete blueprint architecture.
"""
from django.conf import settings
from django.db import models

from .books import CanonicalBook, Language, License
from .verses import Verse


class Author(models.Model):
    """
    Universal author model for biblical authors, Church Fathers, and modern commentators
    """

    # Basic identification
    name = models.CharField(max_length=200, help_text="Full canonical name")
    short_name = models.CharField(max_length=100, blank=True, help_text="Common short name or title")
    latin_name = models.CharField(max_length=200, blank=True, help_text="Latin name if applicable")
    hebrew_name = models.CharField(max_length=200, blank=True, help_text="Hebrew name if applicable")
    greek_name = models.CharField(max_length=200, blank=True, help_text="Greek name if applicable")
    also_known_as = models.JSONField(default=list, blank=True, help_text="Alternative names and titles")

    # Author categorization
    author_type = models.CharField(
        max_length=30,
        choices=[
            ("biblical", "Biblical Author"),
            ("church_father", "Church Father"),
            ("medieval", "Medieval Theologian"),
            ("reformation", "Reformation Era"),
            ("modern", "Modern Commentator"),
            ("contemporary", "Contemporary Scholar"),
            ("legendary", "Traditional/Legendary"),
        ],
        help_text="Primary category of author",
    )
    sub_category = models.CharField(max_length=100, blank=True, help_text="More specific categorization")

    # Historical context
    birth_year = models.IntegerField(null=True, blank=True, help_text="Approximate birth year")
    death_year = models.IntegerField(null=True, blank=True, help_text="Approximate death year")
    century = models.CharField(max_length=50, blank=True, help_text="Primary century (e.g., '4th century')")
    period = models.CharField(max_length=100, blank=True, help_text="Historical period description")

    # Geographical and cultural context
    birthplace = models.CharField(max_length=200, blank=True)
    primary_location = models.CharField(max_length=200, blank=True, help_text="Where they primarily worked/taught")
    cultural_context = models.TextField(blank=True, help_text="Cultural and political context")

    # Ecclesiastical and theological context
    tradition = models.CharField(max_length=100, blank=True, help_text="Eastern/Western, Orthodox/Catholic/etc")
    theological_school = models.CharField(max_length=200, blank=True, help_text="Antiochene, Alexandrian, etc")
    ecclesiastical_rank = models.CharField(max_length=100, blank=True, help_text="Bishop, Presbyter, Monk, etc")
    feast_day = models.CharField(max_length=50, blank=True, help_text="Liturgical feast day if saint")

    # Biblical authorship (for biblical authors)
    biblical_books_authored = models.ManyToManyField(
        CanonicalBook,
        blank=True,
        related_name="traditional_authors",
        help_text="Books traditionally attributed to this author",
    )
    biblical_role = models.CharField(
        max_length=100, blank=True, help_text="Role in biblical narrative (prophet, apostle, king, etc.)"
    )
    biblical_period = models.CharField(
        max_length=100, blank=True, help_text="Biblical historical period (United Kingdom, Exile, etc.)"
    )

    # Academic and literary context
    specializations = models.JSONField(default=list, blank=True, help_text="Areas of expertise")
    major_works = models.JSONField(
        default=list, blank=True, help_text="List of major works (biblical books, theological works, etc.)"
    )
    influenced_by = models.ManyToManyField("self", symmetrical=False, blank=True, related_name="influenced")
    contemporary_with = models.ManyToManyField("self", symmetrical=True, blank=True)

    # Modern scholarly context
    modern_significance = models.TextField(blank=True, help_text="Why this author matters today")
    scholarly_consensus = models.TextField(blank=True, help_text="Current academic view of their work")

    # Biography and legacy
    biography_summary = models.TextField(blank=True, help_text="Concise biographical summary")
    theological_contributions = models.TextField(blank=True, help_text="Key theological contributions")
    historical_impact = models.TextField(blank=True, help_text="Impact on church history")

    # Technical metadata
    primary_language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    reliability_rating = models.CharField(
        max_length=20,
        choices=[
            ("excellent", "Excellent - Well documented"),
            ("good", "Good - Generally reliable"),
            ("fair", "Fair - Some uncertainty"),
            ("poor", "Poor - Limited information"),
            ("legendary", "Legendary - Mostly traditional"),
        ],
        default="good",
    )

    # Visual representation
    portrait_image = models.URLField(blank=True, help_text="URL to author's portrait/icon")
    portrait_description = models.CharField(max_length=300, blank=True, help_text="Alt text for portrait")
    portrait_source = models.CharField(max_length=200, blank=True, help_text="Source/attribution for image")
    portrait_license = models.CharField(max_length=100, blank=True, help_text="Image license (CC, Public Domain, etc)")

    # Historical documentation
    episcopal_appointment = models.IntegerField(null=True, blank=True, help_text="Year of episcopal appointment")
    presbyterial_appointment = models.IntegerField(null=True, blank=True, help_text="Year of presbyterial appointment")
    papal_election = models.IntegerField(null=True, blank=True, help_text="Year of papal election")
    historical_sources = models.JSONField(default=list, blank=True, help_text="Historical sources and editions")

    # External references
    wikipedia_url = models.URLField(blank=True)
    external_links = models.JSONField(default=list, blank=True, help_text="Additional reference links")
    bibliography = models.TextField(blank=True, help_text="Key academic sources")

    # System metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "commentary_authors"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["century"]),
            models.Index(fields=["tradition"]),
            models.Index(fields=["birth_year", "death_year"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.century})"

    @property
    def lifespan(self):
        """Return formatted lifespan if dates available"""
        if self.birth_year and self.death_year:
            return f"{self.birth_year}-{self.death_year}"
        elif self.birth_year:
            return f"b. {self.birth_year}"
        elif self.death_year:
            return f"d. {self.death_year}"
        return self.century or "Unknown period"


class CommentarySource(models.Model):
    """
    Metadados do acervo de comentários (ex.: 'Matthew Henry', 'TSK', 'Barnes', 'Bíblia de Genebra').
    """

    name = models.CharField(max_length=120)
    short_code = models.CharField(max_length=40, unique=True)  # 'MHCC','TSK','BARNES'
    license = models.ForeignKey(
        License, on_delete=models.SET_NULL, null=True, blank=True, related_name="commentary_sources"
    )
    language = models.ForeignKey(
        Language, on_delete=models.SET_NULL, null=True, blank=True, related_name="commentary_sources"
    )
    url = models.URLField(blank=True, default="")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "commentary_sources"
        ordering = ["short_code"]
        indexes = [
            models.Index(fields=["language", "is_active"]),
            models.Index(fields=["short_code"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.short_code})"


class CommentaryEntry(models.Model):
    """
    Comentário acadêmico por referência canônica; pode cobrir um range (ex.: 3:14-16).
    """

    source = models.ForeignKey(CommentarySource, on_delete=models.CASCADE, related_name="entries")
    # TODO: Add author relationship after migration
    # author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="commentary_entries", null=True, blank=True)
    book = models.ForeignKey(CanonicalBook, on_delete=models.CASCADE, related_name="commentary_entries")
    chapter = models.PositiveIntegerField()
    verse_start = models.PositiveIntegerField()
    verse_end = models.PositiveIntegerField()
    title = models.CharField(max_length=200, blank=True)
    body_text = models.TextField()
    body_html = models.TextField(blank=True, default="")
    original_reference = models.CharField(max_length=100, blank=True, help_text="Original reference format from source")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "commentary_entries"
        ordering = ["source", "book__canonical_order", "chapter", "verse_start"]
        indexes = [
            models.Index(
                fields=["source", "book", "chapter", "verse_start", "verse_end"], name="commentary_entry_ref_idx"
            ),
            models.Index(fields=["book", "chapter"], name="commentary_book_chapter_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "book", "chapter", "verse_start", "verse_end"],
                name="uniq_commentary_source_ref",
            ),
            models.CheckConstraint(
                check=models.Q(verse_end__gte=models.F("verse_start")), name="commentary_end_gte_start"
            ),
            models.CheckConstraint(check=models.Q(chapter__gte=1), name="commentary_chapter_pos"),
            models.CheckConstraint(check=models.Q(verse_start__gte=1), name="commentary_verse_start_pos"),
            models.CheckConstraint(check=models.Q(verse_end__gte=1), name="commentary_verse_end_pos"),
        ]

    def __str__(self):
        verse_range = (
            f"{self.verse_start}" if self.verse_start == self.verse_end else f"{self.verse_start}-{self.verse_end}"
        )
        return f"{self.source.short_code}: {self.book.osis_code} {self.chapter}:{verse_range}"

    @property
    def reference_display(self):
        """Human-readable reference."""
        verse_range = (
            f"{self.verse_start}" if self.verse_start == self.verse_end else f"{self.verse_start}-{self.verse_end}"
        )
        return f"{self.book.osis_code} {self.chapter}:{verse_range}"

    def covers_verse(self, chapter, verse):
        """Check if this commentary entry covers a specific verse."""
        return self.chapter == chapter and self.verse_start <= verse <= self.verse_end


class VerseComment(models.Model):
    """
    Comentário pessoal do usuário em verses específicos.
    """

    verse = models.ForeignKey(Verse, related_name="user_comments", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="verse_comments")
    comment = models.TextField()
    is_public = models.BooleanField(default=False, help_text="Whether this comment is visible to other users")
    is_favorite = models.BooleanField(default=False, help_text="User's favorite/starred comment")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "verse_comments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"], name="vcomment_user_created_idx"),
            models.Index(fields=["verse", "is_public"], name="vcomment_verse_public_idx"),
            models.Index(fields=["user", "is_favorite"], name="vcomment_user_favorite_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["verse", "user"],
                name="uniq_verse_user_comment",
                violation_error_message="User can only have one comment per verse",
            ),
        ]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.verse}"

    @property
    def preview(self):
        """Short preview of comment for listings."""
        return self.comment[:100] + "..." if len(self.comment) > 100 else self.comment
