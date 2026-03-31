"""
Commentary domain models - Biblical commentaries with AI enrichment.

This module provides comprehensive models for biblical commentaries including:
- Author: Universal author model (Church Fathers, modern scholars, etc.)
- CommentarySource: Commentary collections/sources
- CommentaryEntry: Individual commentary entries per verse/passage
- CommentaryTranslation: Multi-language translations of commentaries
- CommentaryEnrichment: AI-generated analysis and insights
- CommentaryReference: Cross-references between commentaries
- VerseComment: User personal comments on verses
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Author(models.Model):
    """
    Universal author model for biblical authors, Church Fathers, and modern commentators.
    
    Comprehensive metadata supporting:
    - Historical context (dates, locations, cultural context)
    - Ecclesiastical context (tradition, rank, theological school)
    - Academic context (specializations, major works, influence)
    - Visual representation (portraits, icons)
    
    Examples:
        - Church Father: Augustine of Hippo, John Chrysostom
        - Medieval: Thomas Aquinas, Cornelius a Lapide
        - Reformation: John Calvin, Matthew Henry
        - Modern: N.T. Wright, D.A. Carson
    """

    # ============================================================
    # PERSON HUB LINK
    # ============================================================
    person = models.OneToOneField(
        "people.Person",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="author_profile",
        help_text=_("Link to unified Person identity hub"),
    )

    # ============================================================
    # BASIC IDENTIFICATION
    # ============================================================
    name = models.CharField(
        max_length=200,
        help_text=_("Full canonical name (e.g., 'Augustine of Hippo')")
    )
    short_name = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Common short name or title (e.g., 'Augustine')")
    )
    latin_name = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Latin name if applicable (e.g., 'Aurelius Augustinus')")
    )
    hebrew_name = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Hebrew name if applicable")
    )
    greek_name = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Greek name if applicable")
    )
    also_known_as = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Alternative names and titles as JSON array")
    )

    # ============================================================
    # AUTHOR CATEGORIZATION
    # ============================================================
    AUTHOR_TYPE_CHOICES = [
        ("biblical", _("Biblical Author")),
        ("apostolic_father", _("Apostolic Father")),
        ("church_father", _("Church Father")),
        ("desert_father", _("Desert Father")),
        ("medieval", _("Medieval Theologian")),
        ("scholastic", _("Scholastic")),
        ("reformation", _("Reformation Era")),
        ("puritan", _("Puritan")),
        ("mystic", _("Mystic")),
        ("modern_commentator", _("Modern Commentator")),
        ("contemporary", _("Contemporary Scholar")),
        ("post_reformation", _("Post-Reformation")),
        ("anonymous_work", _("Anonymous Work")),
        ("collective_work", _("Collective Work")),
        ("liturgical_text", _("Liturgical Text")),
        ("legendary", _("Traditional/Legendary")),
    ]
    
    author_type = models.CharField(
        max_length=30,
        choices=AUTHOR_TYPE_CHOICES,
        help_text=_("Primary category of author")
    )
    sub_category = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("More specific categorization (e.g., 'Cappadocian Father')")
    )

    # ============================================================
    # HISTORICAL CONTEXT
    # ============================================================
    birth_year = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Approximate birth year (negative for BC)")
    )
    death_year = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Approximate death year (use 'AD' format, e.g., 430 for AD430)")
    )
    century = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("Primary century (e.g., '4th century', '1st century BC')")
    )
    period = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Historical period description (e.g., 'AD397', 'AD430')")
    )
    era = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Broader era (e.g., 'Patristic Era', 'Reformation')")
    )

    # ============================================================
    # GEOGRAPHICAL AND CULTURAL CONTEXT
    # ============================================================
    birthplace = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("City/region of birth")
    )
    death_location = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("City/region of death")
    )
    primary_location = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Where they primarily worked/taught")
    )
    cultural_context = models.TextField(
        blank=True,
        help_text=_("Cultural and political context of their work")
    )
    nationality = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Modern nationality equivalent or ancient region")
    )

    # ============================================================
    # ECCLESIASTICAL AND THEOLOGICAL CONTEXT
    # ============================================================
    tradition = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Theological/ecclesiastical tradition (e.g., 'Western Catholic', 'Eastern Orthodox', 'Reformed Baptist')")
    )
    
    theological_school = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Theological school or approach (e.g., 'Antiochene', 'Alexandrian', 'Cappadocian', 'Scholasticism')")
    )
    
    ECCLESIASTICAL_RANK_CHOICES = [
        ("pope", _("Pope")),
        ("patriarch", _("Patriarch")),
        ("archbishop", _("Archbishop")),
        ("bishop", _("Bishop")),
        ("presbyter", _("Presbyter/Priest")),
        ("deacon", _("Deacon")),
        ("monk", _("Monk")),
        ("abbot", _("Abbot")),
        ("professor", _("Professor")),
        ("pastor", _("Pastor")),
        ("layperson", _("Layperson")),
    ]
    
    ecclesiastical_rank = models.CharField(
        max_length=100,
        blank=True,
        choices=ECCLESIASTICAL_RANK_CHOICES,
        help_text=_("Church office or position")
    )
    feast_day = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("Liturgical feast day if saint (e.g., 'August 28')")
    )
    is_saint = models.BooleanField(
        default=False,
        help_text=_("Whether recognized as saint in any tradition")
    )
    is_doctor_of_church = models.BooleanField(
        default=False,
        help_text=_("Whether recognized as Doctor of the Church")
    )

    # ============================================================
    # ORTHODOXY AND RECOGNITION
    # ============================================================
    ORTHODOXY_CHOICES = [
        ("orthodox", _("Orthodox — universally accepted")),
        ("controversial", _("Controversial — debated across traditions")),
        ("condemned_partially", _("Condemned partially — some works condemned")),
        ("heterodox", _("Heterodox — rejected as heretical")),
    ]

    orthodoxy_status = models.CharField(
        max_length=30,
        blank=True,
        choices=ORTHODOXY_CHOICES,
        default="orthodox",
        help_text=_("Doctrinal status across Christian traditions")
    )
    recognized_by = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Traditions that recognize/venerate this author: ['catholic','orthodox','protestant','oriental_orthodox','church_of_east','anglican']")
    )
    councils = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Ecumenical councils associated with this author (e.g., ['nicaea_325','chalcedon_451'])")
    )

    # ============================================================
    # BIBLICAL AUTHORSHIP (for biblical authors)
    # ============================================================
    biblical_books_authored = models.ManyToManyField(
        "bible.CanonicalBook",
        blank=True,
        related_name="traditional_authors",
        help_text=_("Books traditionally attributed to this author")
    )
    biblical_role = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Role in biblical narrative (prophet, apostle, king, etc.)")
    )
    biblical_period = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Biblical historical period (United Kingdom, Exile, etc.)")
    )

    # ============================================================
    # ACADEMIC AND LITERARY CONTEXT
    # ============================================================
    specializations = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Areas of expertise as JSON array")
    )
    major_works = models.JSONField(
        default=list,
        blank=True,
        help_text=_("List of major works as JSON array")
    )
    influenced_by = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="influenced"
    )
    contemporary_with = models.ManyToManyField(
        "self",
        symmetrical=True,
        blank=True
    )

    # ============================================================
    # HERMENEUTICAL APPROACH
    # ============================================================
    primary_hermeneutic = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Primary interpretive approach (e.g., 'allegorical', 'literal_historical', 'mixed_antiochene', 'scholastic', 'devotional')")
    )
    hermeneutical_notes = models.TextField(
        blank=True,
        help_text=_("Notes on interpretive methodology")
    )

    # ============================================================
    # MODERN SCHOLARLY CONTEXT
    # ============================================================
    modern_significance = models.TextField(
        blank=True,
        help_text=_("Why this author matters today")
    )
    scholarly_consensus = models.TextField(
        blank=True,
        help_text=_("Current academic view of their work")
    )
    controversies = models.TextField(
        blank=True,
        help_text=_("Theological controversies associated with this author")
    )

    # ============================================================
    # BIOGRAPHY AND LEGACY
    # ============================================================
    biography_summary = models.TextField(
        blank=True,
        help_text=_("Concise biographical summary")
    )
    biography_pt = models.TextField(
        blank=True,
        help_text=_("Biographical summary in Portuguese")
    )
    theological_contributions = models.TextField(
        blank=True,
        help_text=_("Key theological contributions")
    )
    historical_impact = models.TextField(
        blank=True,
        help_text=_("Impact on church history")
    )
    famous_quotes = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Notable quotes as JSON array")
    )

    # ============================================================
    # TECHNICAL METADATA
    # ============================================================
    primary_language = models.ForeignKey(
        "bible.Language",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commentary_authors"
    )
    
    RELIABILITY_CHOICES = [
        ("excellent", _("Excellent - Well documented")),
        ("good", _("Good - Generally reliable")),
        ("fair", _("Fair - Some uncertainty")),
        ("poor", _("Poor - Limited information")),
        ("legendary", _("Legendary - Mostly traditional")),
    ]
    
    reliability_rating = models.CharField(
        max_length=20,
        choices=RELIABILITY_CHOICES,
        default="good"
    )

    # ============================================================
    # VISUAL REPRESENTATION
    # ============================================================
    portrait_image = models.URLField(
        max_length=500,
        blank=True,
        help_text=_("URL to author's portrait/icon")
    )
    portrait_description = models.CharField(
        max_length=300,
        blank=True,
        help_text=_("Alt text for portrait")
    )
    portrait_source = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Source/attribution for image")
    )
    portrait_license = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Image license (CC, Public Domain, etc)")
    )

    # ============================================================
    # HISTORICAL DOCUMENTATION
    # ============================================================
    episcopal_appointment = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Year of episcopal appointment")
    )
    presbyterial_appointment = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Year of presbyterial appointment")
    )
    papal_election = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Year of papal election")
    )
    historical_sources = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Historical sources and editions as JSON array")
    )

    # ============================================================
    # EXTERNAL REFERENCES
    # ============================================================
    wikipedia_url = models.URLField(max_length=500, blank=True)
    ccel_url = models.URLField(
        blank=True,
        help_text=_("Christian Classics Ethereal Library URL")
    )
    newadvent_url = models.URLField(
        blank=True,
        help_text=_("New Advent Catholic Encyclopedia URL")
    )
    external_links = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Additional reference links as JSON array")
    )
    bibliography = models.TextField(
        blank=True,
        help_text=_("Key academic sources")
    )

    # ============================================================
    # SYSTEM METADATA
    # ============================================================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "commentaries_author"
        ordering = ["name"]
        verbose_name = _("Author")
        verbose_name_plural = _("Authors")
        indexes = [
            models.Index(fields=["century"]),
            models.Index(fields=["tradition"]),
            models.Index(fields=["birth_year", "death_year"]),
            models.Index(fields=["author_type"], name="comm_author_type_idx"),
            models.Index(fields=["author_type", "tradition"], name="comm_type_tradition_idx"),
            models.Index(fields=["theological_school"], name="comm_theo_school_idx"),
            models.Index(fields=["is_saint"], name="comm_is_saint_idx"),
        ]

    def __str__(self):
        period_str = self.period or self.century or ""
        if period_str:
            return f"{self.name} ({period_str})"
        return self.name

    @property
    def lifespan(self):
        """Return formatted lifespan if dates available."""
        if self.birth_year and self.death_year:
            return f"{self.birth_year}-{self.death_year}"
        elif self.birth_year:
            return f"b. {self.birth_year}"
        elif self.death_year:
            return f"d. {self.death_year}"
        return self.century or "Unknown period"

    @property
    def display_title(self):
        """Return formal title for display (e.g., 'St. Augustine of Hippo')."""
        prefix = "St. " if self.is_saint else ""
        return f"{prefix}{self.name}"


class CommentarySource(models.Model):
    """
    Commentary collection/source metadata.
    
    Examples:
        - Catena Bible (Church Fathers collection)
        - Matthew Henry Complete Commentary
        - Treasury of Scripture Knowledge (TSK)
        - Barnes' Notes
        - Gill's Exposition
    """

    # ============================================================
    # BASIC IDENTIFICATION
    # ============================================================
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text=_("Full name (e.g., 'Matthew Henry Complete Commentary')")
    )
    short_code = models.CharField(
        max_length=40,
        unique=True,
        help_text=_("Unique identifier (e.g., 'MHCC', 'TSK', 'CATENA')")
    )
    subtitle = models.CharField(
        max_length=300,
        blank=True,
        help_text=_("Subtitle or additional description")
    )

    # ============================================================
    # SOURCE METADATA
    # ============================================================
    SOURCE_TYPE_CHOICES = [
        ("patristic", _("Patristic Commentary")),
        ("medieval", _("Medieval Commentary")),
        ("reformation", _("Reformation Commentary")),
        ("puritan", _("Puritan Commentary")),
        ("modern_devotional", _("Modern Devotional")),
        ("modern_academic", _("Modern Academic")),
        ("cross_reference", _("Cross-Reference System")),
        ("study_bible", _("Study Bible Notes")),
        ("catena", _("Catena (Chain) Commentary")),
        ("homily", _("Homiletical Collection")),
    ]
    
    source_type = models.CharField(
        max_length=50,
        choices=SOURCE_TYPE_CHOICES,
        default="modern_devotional",
        help_text=_("Type of commentary source")
    )
    
    license = models.ForeignKey(
        "bible.License",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commentary_sources"
    )
    language = models.ForeignKey(
        "bible.Language",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commentary_sources"
    )
    url = models.URLField(
        blank=True,
        default="",
        help_text=_("Primary URL for this source")
    )
    description = models.TextField(blank=True)
    description_pt = models.TextField(
        blank=True,
        help_text=_("Description in Portuguese")
    )

    # ============================================================
    # PUBLICATION METADATA
    # ============================================================
    publication_year = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Year of publication or primary edition")
    )
    original_publication_year = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Year of original publication (if different)")
    )
    publisher = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Publisher name")
    )
    editor = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Editor(s) name")
    )

    # ============================================================
    # COVERAGE AND SCOPE
    # ============================================================
    COVERAGE_CHOICES = [
        ("whole_bible", _("Whole Bible")),
        ("old_testament", _("Old Testament Only")),
        ("new_testament", _("New Testament Only")),
        ("pentateuch", _("Pentateuch")),
        ("gospels", _("Gospels")),
        ("pauline", _("Pauline Epistles")),
        ("specific_books", _("Specific Books")),
    ]
    
    coverage = models.CharField(
        max_length=50,
        choices=COVERAGE_CHOICES,
        default="whole_bible",
        help_text=_("Biblical coverage of this source")
    )
    covered_books = models.ManyToManyField(
        "bible.CanonicalBook",
        blank=True,
        related_name="commentary_source_coverage",
        help_text=_("Specific books covered (if not whole Bible)")
    )

    # ============================================================
    # AUTHORS
    # ============================================================
    primary_author = models.ForeignKey(
        Author,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authored_sources",
        help_text=_("Primary author (for single-author works)")
    )
    authors = models.ManyToManyField(
        Author,
        blank=True,
        related_name="contributed_sources",
        help_text=_("All authors (for multi-author works like Catena)")
    )
    author_type = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("Type of authors (e.g., 'Church Fathers', 'Reformation')")
    )

    # ============================================================
    # VISUAL & UI
    # ============================================================
    cover_image_url = models.URLField(
        blank=True,
        help_text=_("URL to cover image/icon for UI display")
    )
    icon_class = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("CSS icon class for UI (e.g., 'fa-book')")
    )
    theme_color = models.CharField(
        max_length=7,
        blank=True,
        help_text=_("Hex color for UI theming (e.g., '#8B4513')")
    )

    # ============================================================
    # STATUS FLAGS
    # ============================================================
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether available for use")
    )
    is_featured = models.BooleanField(
        default=False,
        help_text=_("Whether to feature prominently in UI")
    )
    is_free = models.BooleanField(
        default=True,
        help_text=_("Whether freely available")
    )
    requires_attribution = models.BooleanField(
        default=True,
        help_text=_("Whether attribution is required")
    )

    # ============================================================
    # STATISTICS
    # ============================================================
    entry_count = models.IntegerField(
        default=0,
        help_text=_("Number of commentary entries")
    )
    verse_coverage_percent = models.FloatField(
        null=True,
        blank=True,
        help_text=_("Percentage of Bible verses covered (0-100)")
    )
    average_entry_length = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Average word count per entry")
    )

    # ============================================================
    # SYSTEM METADATA
    # ============================================================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "commentaries_source"
        ordering = ["short_code"]
        verbose_name = _("Commentary Source")
        verbose_name_plural = _("Commentary Sources")
        indexes = [
            models.Index(fields=["language", "is_active"], name="commsrc_lang_active_idx"),
            models.Index(fields=["short_code"], name="commsrc_short_code_idx"),
            models.Index(fields=["source_type", "is_active"], name="commsrc_type_active_idx"),
            models.Index(fields=["is_featured"], name="commsrc_featured_idx"),
        ]

    def __str__(self):
        year = f" ({self.publication_year})" if self.publication_year else ""
        return f"{self.name}{year} [{self.short_code}]"


class CommentaryEntry(models.Model):
    """
    Individual commentary entry for a verse or passage.
    
    Supports:
    - Single verse or verse range (e.g., John 3:16 or John 3:14-16)
    - Original content with optional HTML formatting
    - Links to author and source
    - Quality tracking (completeness, confidence)
    """

    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    source = models.ForeignKey(
        CommentarySource,
        on_delete=models.CASCADE,
        related_name="entries"
    )
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="commentary_entries",
        null=True,
        blank=True,
        help_text=_("Specific author (for multi-author sources)")
    )
    book = models.ForeignKey(
        "bible.CanonicalBook",
        on_delete=models.CASCADE,
        related_name="commentary_entries"
    )

    # ============================================================
    # VERSE REFERENCE
    # ============================================================
    chapter = models.PositiveIntegerField()
    verse_start = models.PositiveIntegerField()
    verse_end = models.PositiveIntegerField()
    original_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Original reference format from source (e.g., 'JN 1:1')")
    )

    # ============================================================
    # CONTENT
    # ============================================================
    title = models.CharField(
        max_length=300,
        blank=True,
        help_text=_("Entry title if available")
    )
    body_text = models.TextField(
        help_text=_("Plain text content of commentary")
    )
    body_html = models.TextField(
        blank=True,
        default="",
        help_text=_("HTML formatted content")
    )
    
    # ============================================================
    # EXTRACTION METADATA
    # ============================================================
    EXTRACTION_METHOD_CHOICES = [
        ("beautifulsoup", _("BeautifulSoup scraping")),
        ("firecrawl", _("Firecrawl extraction")),
        ("api", _("API import")),
        ("manual", _("Manual entry")),
        ("ocr", _("OCR from scanned text")),
    ]
    
    extraction_method = models.CharField(
        max_length=50,
        blank=True,
        choices=EXTRACTION_METHOD_CHOICES,
        help_text=_("How this content was extracted")
    )
    source_url = models.URLField(
        blank=True,
        help_text=_("URL where this commentary was found")
    )
    full_content_url = models.URLField(
        blank=True,
        help_text=_("URL to full content if truncated")
    )
    
    CONTENT_TYPE_CHOICES = [
        ("full", _("Full content")),
        ("excerpt", _("Excerpt only")),
        ("summary", _("Summary")),
        ("reference", _("Reference/Cross-reference")),
    ]
    
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default="full",
        help_text=_("Type of content captured")
    )

    # ============================================================
    # QUALITY TRACKING
    # ============================================================
    is_complete = models.BooleanField(
        default=True,
        help_text=_("Whether this entry is complete (vs. excerpt/summary)")
    )
    original_language = models.CharField(
        max_length=20,
        blank=True,
        help_text=_("Original language of text (e.g., 'Latin', 'Greek', 'English')")
    )
    word_count = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Approximate word count")
    )
    reading_time = models.CharField(
        max_length=20,
        blank=True,
        help_text=_("Estimated reading time (e.g., '< 1 min', '5 mins')")
    )
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        help_text=_("Data quality/accuracy score (0.0-1.0)")
    )

    # ============================================================
    # DISPLAY METADATA
    # ============================================================
    commentary_number = models.CharField(
        max_length=20,
        blank=True,
        help_text=_("Position in source (e.g., '1/12' for first of 12)")
    )
    display_order = models.IntegerField(
        default=0,
        help_text=_("Order for display when multiple entries exist")
    )

    # ============================================================
    # SYSTEM METADATA
    # ============================================================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "commentaries_entry"
        ordering = ["source", "book__canonical_order", "chapter", "verse_start", "display_order"]
        verbose_name = _("Commentary Entry")
        verbose_name_plural = _("Commentary Entries")
        indexes = [
            models.Index(
                fields=["source", "book", "chapter", "verse_start", "verse_end"],
                name="commentry_ref_idx"
            ),
            models.Index(fields=["book", "chapter"], name="commentry_book_chapter_idx"),
            models.Index(fields=["author"], name="commentry_author_idx"),
            models.Index(
                fields=["book", "chapter", "is_complete"],
                name="commentry_complete_idx"
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "author", "book", "chapter", "verse_start", "verse_end"],
                name="uniq_commentry_source_ref",
            ),
            models.CheckConstraint(
                check=models.Q(verse_end__gte=models.F("verse_start")),
                name="commentry_end_gte_start"
            ),
            models.CheckConstraint(
                check=models.Q(chapter__gte=1),
                name="commentry_chapter_pos"
            ),
            models.CheckConstraint(
                check=models.Q(verse_start__gte=1),
                name="commentry_verse_start_pos"
            ),
            models.CheckConstraint(
                check=models.Q(verse_end__gte=1),
                name="commentry_verse_end_pos"
            ),
            models.CheckConstraint(
                check=models.Q(confidence_score__gte=0.0) & models.Q(confidence_score__lte=1.0),
                name="commentry_confidence_0_1"
            ),
        ]

    def __str__(self):
        verse_range = (
            f"{self.verse_start}" if self.verse_start == self.verse_end
            else f"{self.verse_start}-{self.verse_end}"
        )
        author_str = f" by {self.author.short_name or self.author.name}" if self.author else ""
        return f"{self.source.short_code}: {self.book.osis_code} {self.chapter}:{verse_range}{author_str}"

    @property
    def reference_display(self):
        """Human-readable reference."""
        verse_range = (
            f"{self.verse_start}" if self.verse_start == self.verse_end
            else f"{self.verse_start}-{self.verse_end}"
        )
        return f"{self.book.osis_code} {self.chapter}:{verse_range}"

    @property
    def length_category(self):
        """Categorize entry by length for UI."""
        if not self.word_count:
            return "unknown"
        if self.word_count < 100:
            return "brief"
        elif self.word_count < 500:
            return "medium"
        elif self.word_count < 2000:
            return "detailed"
        return "comprehensive"

    def covers_verse(self, chapter: int, verse: int) -> bool:
        """Check if this commentary entry covers a specific verse."""
        return self.chapter == chapter and self.verse_start <= verse <= self.verse_end


class CommentaryTranslation(models.Model):
    """
    Translation of a commentary entry into different languages.
    
    Supports multi-language content with translation metadata
    tracking the model used and translation timestamp.
    """

    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    entry = models.ForeignKey(
        CommentaryEntry,
        on_delete=models.CASCADE,
        related_name="translations"
    )
    language = models.ForeignKey(
        "bible.Language",
        on_delete=models.CASCADE,
        related_name="commentary_translations"
    )

    # ============================================================
    # TRANSLATED CONTENT
    # ============================================================
    content = models.TextField(
        help_text=_("Translated content")
    )
    content_html = models.TextField(
        blank=True,
        help_text=_("Translated content with HTML formatting")
    )
    title = models.CharField(
        max_length=300,
        blank=True,
        help_text=_("Translated title if available")
    )

    # ============================================================
    # TRANSLATION METADATA
    # ============================================================
    TRANSLATION_METHOD_CHOICES = [
        ("ai_gpt4", _("GPT-4")),
        ("ai_gpt4o", _("GPT-4o")),
        ("ai_gpt4o_mini", _("GPT-4o-mini")),
        ("ai_claude", _("Claude")),
        ("ai_gemini", _("Gemini")),
        ("human", _("Human translator")),
        ("existing", _("Pre-existing translation")),
    ]
    
    translation_method = models.CharField(
        max_length=50,
        choices=TRANSLATION_METHOD_CHOICES,
        default="ai_gpt4o_mini",
        help_text=_("How this translation was created")
    )
    translation_model = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Specific model used (e.g., 'gpt-4o-mini')")
    )
    translated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When translation was performed")
    )
    translator_notes = models.TextField(
        blank=True,
        help_text=_("Notes about translation choices or difficulties")
    )

    # ============================================================
    # QUALITY TRACKING
    # ============================================================
    is_reviewed = models.BooleanField(
        default=False,
        help_text=_("Whether translation has been human-reviewed")
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_translations"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    quality_score = models.FloatField(
        null=True,
        blank=True,
        help_text=_("Quality assessment (0.0-1.0)")
    )

    # ============================================================
    # SYSTEM METADATA
    # ============================================================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "commentaries_translation"
        ordering = ["entry", "language"]
        verbose_name = _("Commentary Translation")
        verbose_name_plural = _("Commentary Translations")
        indexes = [
            models.Index(fields=["entry", "language"], name="commtrans_entry_lang_idx"),
            models.Index(fields=["language", "is_reviewed"], name="commtrans_lang_rev_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["entry", "language"],
                name="uniq_commtrans_entry_lang"
            ),
        ]

    def __str__(self):
        return f"{self.entry} [{self.language.iso_code}]"


class CommentaryEnrichment(models.Model):
    """
    AI-generated enrichment and analysis for a commentary entry.
    
    Contains:
    - AI Summary (one-sentence, abstract, key points)
    - Argumentative Structure (thesis, arguments, conclusion)
    - Theological Analysis (doctrines, traditions, method)
    - Spiritual Insight (themes, practical reflection)
    """

    # ============================================================
    # RELATIONSHIP
    # ============================================================
    entry = models.OneToOneField(
        CommentaryEntry,
        on_delete=models.CASCADE,
        related_name="enrichment"
    )

    # ============================================================
    # AI SUMMARY
    # ============================================================
    summary_one_sentence = models.TextField(
        blank=True,
        help_text=_("One-sentence summary of the commentary")
    )
    summary_abstract = models.TextField(
        blank=True,
        help_text=_("Extended abstract/summary")
    )
    summary_key_points = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Key points as JSON array")
    )

    # Portuguese translations of summary
    summary_one_sentence_pt = models.TextField(blank=True)
    summary_abstract_pt = models.TextField(blank=True)
    summary_key_points_pt = models.JSONField(default=list, blank=True)

    # ============================================================
    # ARGUMENTATIVE STRUCTURE
    # ============================================================
    thesis = models.TextField(
        blank=True,
        help_text=_("Main thesis/argument of the commentary")
    )
    arguments = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Supporting arguments as JSON array")
    )
    objections = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Objections addressed as JSON array")
    )
    conclusion = models.TextField(
        blank=True,
        help_text=_("Conclusion of the argument")
    )

    # Portuguese translations
    thesis_pt = models.TextField(blank=True)
    arguments_pt = models.JSONField(default=list, blank=True)
    conclusion_pt = models.TextField(blank=True)

    # ============================================================
    # THEOLOGICAL ANALYSIS
    # ============================================================
    doctrines = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Doctrines discussed (e.g., ['Trinity', 'Christology'])")
    )
    traditions = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Theological traditions (e.g., ['Latin', 'Eastern'])")
    )
    church_fathers_referenced = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Church Fathers referenced in commentary")
    )
    scripture_references = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Scripture passages referenced")
    )
    
    THEOLOGICAL_METHOD_CHOICES = [
        ("literal", _("Literal/Historical")),
        ("allegorical", _("Allegorical")),
        ("typological", _("Typological")),
        ("moral", _("Moral/Tropological")),
        ("anagogical", _("Anagogical")),
        ("fourfold", _("Fourfold Sense")),
        ("mixed", _("Mixed Methods")),
    ]
    
    theological_method = models.CharField(
        max_length=50,
        blank=True,
        choices=THEOLOGICAL_METHOD_CHOICES,
        help_text=_("Primary interpretive method used")
    )
    controversies = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Theological controversies addressed")
    )

    # ============================================================
    # SPIRITUAL INSIGHT
    # ============================================================
    spiritual_theme = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Central spiritual theme")
    )
    spiritual_theme_pt = models.CharField(max_length=200, blank=True)
    practical_reflection = models.TextField(
        blank=True,
        help_text=_("Practical application for readers")
    )
    practical_reflection_pt = models.TextField(blank=True)
    devotional_value = models.TextField(
        blank=True,
        help_text=_("Devotional/prayer implications")
    )

    # ============================================================
    # CROSS-DOMAIN LINKS
    # ============================================================
    related_entities = models.ManyToManyField(
        "entities.CanonicalEntity",
        blank=True,
        related_name="commentary_enrichments",
        help_text=_("Biblical entities discussed in commentary")
    )
    related_symbols = models.ManyToManyField(
        "symbols.BiblicalSymbol",
        blank=True,
        related_name="commentary_enrichments",
        help_text=_("Symbols interpreted in commentary")
    )
    related_doctrines = models.ManyToManyField(
        "theology.Doctrine",
        blank=True,
        related_name="commentary_enrichments",
        help_text=_("Doctrines discussed in commentary")
    )
    related_themes = models.ManyToManyField(
        "themes.Theme",
        blank=True,
        related_name="commentary_enrichments",
        help_text=_("Themes addressed in commentary")
    )

    # ============================================================
    # ENRICHMENT METADATA
    # ============================================================
    enrichment_model = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("AI model used (e.g., 'gpt-4o-mini')")
    )
    enrichment_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When enrichment was generated")
    )
    
    ENRICHMENT_STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("in_progress", _("In Progress")),
        ("success", _("Success")),
        ("partial", _("Partial (some fields failed)")),
        ("failed", _("Failed")),
    ]
    
    enrichment_status = models.CharField(
        max_length=20,
        choices=ENRICHMENT_STATUS_CHOICES,
        default="pending"
    )
    enrichment_error = models.TextField(
        blank=True,
        help_text=_("Error message if enrichment failed")
    )
    enrichment_version = models.CharField(
        max_length=20,
        default="1.0",
        help_text=_("Version of enrichment pipeline used")
    )

    # ============================================================
    # QUALITY METRICS
    # ============================================================
    is_verified = models.BooleanField(
        default=False,
        help_text=_("Whether enrichment has been human-verified")
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_enrichments"
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    # ============================================================
    # SYSTEM METADATA
    # ============================================================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "commentaries_enrichment"
        verbose_name = _("Commentary Enrichment")
        verbose_name_plural = _("Commentary Enrichments")
        indexes = [
            models.Index(fields=["enrichment_status"], name="commenrich_status_idx"),
            models.Index(fields=["is_verified"], name="commenrich_verified_idx"),
            models.Index(fields=["theological_method"], name="commenrich_method_idx"),
        ]

    def __str__(self):
        return f"Enrichment for {self.entry}"

    @property
    def is_complete(self):
        """Check if all main enrichment fields are populated."""
        return bool(
            self.summary_one_sentence
            and self.thesis
            and self.doctrines
            and self.spiritual_theme
        )


class CommentaryReference(models.Model):
    """
    Cross-reference between commentary entries.
    
    Links commentaries that reference or respond to each other,
    enabling discovery of theological dialogues across centuries.
    """

    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    source_entry = models.ForeignKey(
        CommentaryEntry,
        on_delete=models.CASCADE,
        related_name="outgoing_references"
    )
    target_entry = models.ForeignKey(
        CommentaryEntry,
        on_delete=models.CASCADE,
        related_name="incoming_references"
    )

    # ============================================================
    # REFERENCE TYPE
    # ============================================================
    REFERENCE_TYPE_CHOICES = [
        ("quotes", _("Quotes directly")),
        ("paraphrases", _("Paraphrases")),
        ("responds_to", _("Responds to")),
        ("agrees_with", _("Agrees with")),
        ("disagrees_with", _("Disagrees with")),
        ("builds_upon", _("Builds upon")),
        ("parallel", _("Parallel interpretation")),
        ("contrasts", _("Contrasting interpretation")),
    ]
    
    reference_type = models.CharField(
        max_length=30,
        choices=REFERENCE_TYPE_CHOICES,
        help_text=_("Nature of the reference")
    )
    
    # ============================================================
    # DETAILS
    # ============================================================
    description = models.TextField(
        blank=True,
        help_text=_("Description of how entries are related")
    )
    confidence = models.FloatField(
        default=1.0,
        help_text=_("Confidence in this reference (0.0-1.0)")
    )
    is_explicit = models.BooleanField(
        default=True,
        help_text=_("Whether reference is explicit vs. inferred")
    )

    # ============================================================
    # METADATA
    # ============================================================
    detected_by = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("How reference was detected (manual, AI, etc.)")
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "commentaries_reference"
        verbose_name = _("Commentary Reference")
        verbose_name_plural = _("Commentary References")
        indexes = [
            models.Index(fields=["source_entry"], name="commref_source_idx"),
            models.Index(fields=["target_entry"], name="commref_target_idx"),
            models.Index(fields=["reference_type"], name="commref_type_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source_entry", "target_entry", "reference_type"],
                name="uniq_commref_src_tgt_type"
            ),
            models.CheckConstraint(
                check=~models.Q(source_entry=models.F("target_entry")),
                name="commref_no_self_ref"
            ),
        ]

    def __str__(self):
        return f"{self.source_entry} → {self.target_entry} ({self.reference_type})"


class VerseComment(models.Model):
    """
    User personal comment on a verse.
    
    Supports:
    - Personal reflections and study notes
    - Public sharing (optional)
    - Community interaction (likes, replies)
    - Categorization by type
    """

    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    verse = models.ForeignKey(
        "bible.Verse",
        related_name="user_comments",
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verse_comments"
    )

    # ============================================================
    # CONTENT
    # ============================================================
    comment = models.TextField()
    
    # ============================================================
    # VISIBILITY & STATUS
    # ============================================================
    is_public = models.BooleanField(
        default=False,
        help_text=_("Whether visible to other authenticated users")
    )
    is_favorite = models.BooleanField(
        default=False,
        help_text=_("User's favorite/starred comment")
    )
    is_pinned = models.BooleanField(
        default=False,
        help_text=_("Pinned to top of user's comments")
    )

    # ============================================================
    # INTERACTION METRICS
    # ============================================================
    like_count = models.IntegerField(
        default=0,
        help_text=_("Number of users who marked this helpful")
    )
    reply_count = models.IntegerField(
        default=0,
        help_text=_("Number of replies to this comment")
    )
    view_count = models.IntegerField(
        default=0,
        help_text=_("Number of times viewed (if public)")
    )

    # ============================================================
    # CATEGORIZATION
    # ============================================================
    CATEGORY_CHOICES = [
        ("reflection", _("Personal Reflection")),
        ("question", _("Question")),
        ("insight", _("Theological Insight")),
        ("study_note", _("Study Note")),
        ("prayer", _("Prayer Request")),
        ("application", _("Life Application")),
        ("cross_reference", _("Cross-Reference Note")),
        ("historical", _("Historical Context")),
        ("linguistic", _("Language/Translation Note")),
    ]
    
    category = models.CharField(
        max_length=50,
        blank=True,
        choices=CATEGORY_CHOICES,
        help_text=_("Type of comment")
    )
    
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text=_("User-defined tags as JSON array")
    )

    # ============================================================
    # THREADING (for replies)
    # ============================================================
    parent_comment = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        help_text=_("Parent comment if this is a reply")
    )

    # ============================================================
    # SYSTEM METADATA
    # ============================================================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "commentaries_verse_comment"
        ordering = ["-created_at"]
        verbose_name = _("Verse Comment")
        verbose_name_plural = _("Verse Comments")
        indexes = [
            models.Index(fields=["user", "created_at"], name="vcomm_user_created_idx"),
            models.Index(fields=["verse", "is_public"], name="vcomm_verse_public_idx"),
            models.Index(fields=["user", "is_favorite"], name="vcomm_user_favorite_idx"),
            models.Index(fields=["verse", "category"], name="vcomm_verse_category_idx"),
            models.Index(fields=["parent_comment"], name="vcomm_parent_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["verse", "user"],
                condition=models.Q(parent_comment__isnull=True),
                name="uniq_verse_user_main_comment",
                violation_error_message="User can only have one main comment per verse",
            ),
        ]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.verse}"

    @property
    def preview(self):
        """Short preview of comment for listings."""
        return self.comment[:100] + "..." if len(self.comment) > 100 else self.comment

    @property
    def is_reply(self):
        """Check if this is a reply to another comment."""
        return self.parent_comment is not None
