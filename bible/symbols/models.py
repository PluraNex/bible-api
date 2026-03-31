"""
Symbols models - Biblical symbols with hermeneutical depth.

Key design decisions:
1. Symbols have MULTIPLE MEANINGS that can coexist (water = purification + life + judgment)
2. Same symbol can mean different things in different contexts
3. Symbols PROGRESS through biblical narrative (lamb in Genesis → Exodus → Isaiah → Revelation)
4. Literal meaning vs symbolic meaning are tracked separately
5. Each occurrence in a verse can have its specific interpretation
"""

from django.db import models

# NOTE: Using string references for cross-app ForeignKeys to avoid circular imports


class SymbolNamespace(models.TextChoices):
    """
    Namespace categories for symbols.
    Based on biblical_symbols_gazetteer.json namespaces.
    """

    NATURAL = "NATURAL", "Natural Elements (water, fire, wind)"
    OBJECT = "OBJECT", "Objects (sword, crown, lamp)"
    ACTION = "ACTION", "Actions (washing, anointing, walking)"
    NUMBER = "NUMBER", "Numbers (7, 12, 40)"
    COLOR = "COLOR", "Colors (white, red, purple)"
    DIRECTION = "DIRECTION", "Directions (east, north, up)"
    PERSON_TYPE = "PERSON_TYPE", "Person Types (shepherd, bride, king)"
    ANIMAL = "ANIMAL", "Animals (lamb, lion, dove)"
    PLANT = "PLANT", "Plants (vine, olive, fig)"
    BODY = "BODY", "Body Parts (hand, eye, heart)"
    COSMIC = "COSMIC", "Cosmic (sun, moon, stars)"
    ARCHITECTURAL = "ARCHITECTURAL", "Architecture (temple, door, foundation)"
    TIME = "TIME", "Time (day, night, season)"


class SymbolStatus(models.TextChoices):
    """Symbol curation status."""

    DRAFT = "draft", "Draft"
    REVIEW = "review", "Under Review"
    APPROVED = "approved", "Approved"
    CANONICAL = "canonical", "Canonical"


class BiblicalSymbol(models.Model):
    """
    A biblical symbol with its various meanings.

    Example: Water (NAT:water)
    - Literal meaning: H2O, essential for physical life
    - Symbolic meanings:
      - Purification (Levitical washings)
      - Holy Spirit (John 7:38-39)
      - Life/Salvation (John 4:14)
      - Judgment (Genesis flood)
      - Chaos (primordial waters in Genesis 1:2)
      - Nations/peoples (Revelation 17:15)
    """

    # Identification
    canonical_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique identifier like 'NAT:water', 'ANM:lamb'",
    )
    namespace = models.CharField(
        max_length=20,
        choices=SymbolNamespace.choices,
        db_index=True,
    )

    # Primary name
    primary_name = models.CharField(max_length=200)
    primary_name_pt = models.CharField(max_length=200, blank=True)
    primary_name_original = models.CharField(
        max_length=200,
        blank=True,
        help_text="Original Hebrew/Greek term",
    )

    # Aliases (alternative names)
    aliases = models.JSONField(
        default=list,
        blank=True,
        help_text="Alternative names for this symbol",
    )

    # Literal meaning (what it actually IS)
    literal_meaning = models.TextField(
        blank=True,
        help_text="Physical/literal meaning of the symbol",
    )
    literal_meaning_pt = models.TextField(blank=True)

    # Brief description
    description = models.TextField(blank=True)
    description_pt = models.TextField(blank=True)

    # Associated concepts (tags)
    associated_concepts = models.JSONField(
        default=list,
        blank=True,
        help_text="Related theological concepts",
    )

    # Classification & Search
    boost = models.FloatField(default=1.0)
    priority = models.PositiveIntegerField(default=50)

    # Status
    status = models.CharField(
        max_length=20,
        choices=SymbolStatus.choices,
        default=SymbolStatus.DRAFT,
    )

    # AI Enrichment
    ai_enriched = models.BooleanField(default=False)
    ai_enriched_at = models.DateTimeField(null=True, blank=True)
    ai_summary = models.TextField(
        blank=True,
        help_text="AI-generated comprehensive summary of symbol usage",
    )
    ai_summary_pt = models.TextField(blank=True)
    ai_hermeneutical_guide = models.TextField(
        blank=True,
        help_text="AI guide for interpreting this symbol",
    )

    # Etymology & Linguistics
    hebrew_word = models.CharField(max_length=100, blank=True)
    hebrew_transliteration = models.CharField(max_length=100, blank=True)
    greek_word = models.CharField(max_length=100, blank=True)
    greek_transliteration = models.CharField(max_length=100, blank=True)
    strongs_hebrew = models.CharField(max_length=20, blank=True)
    strongs_greek = models.CharField(max_length=20, blank=True)

    # Study metrics
    study_value = models.PositiveIntegerField(
        default=50,
        help_text="Value for Bible study (1-100)",
    )
    difficulty_level = models.PositiveIntegerField(
        default=50,
        help_text="Complexity of interpretation (1-100)",
    )
    frequency = models.PositiveIntegerField(
        default=0,
        help_text="Number of occurrences in Scripture",
    )

    # Visual representation
    emoji = models.CharField(
        max_length=10,
        blank=True,
        help_text="Emoji representation (💧 for water)",
    )
    icon_name = models.CharField(
        max_length=50,
        blank=True,
        help_text="Icon library name",
    )

    # Engagement
    view_count = models.PositiveIntegerField(default=0)
    bookmark_count = models.PositiveIntegerField(default=0)

    # Cross-references to other symbols
    related_symbols = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=True,
        help_text="Related symbols (fire ↔ light ↔ presence)",
    )

    # Antithetical symbol
    opposite_symbol = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="opposite_of",
        help_text="Opposite symbol (light vs darkness)",
    )

    # Source tracking
    source_gazetteer = models.CharField(max_length=100, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "biblical_symbol"
        verbose_name = "Biblical Symbol"
        verbose_name_plural = "Biblical Symbols"
        ordering = ["-priority", "primary_name"]
        indexes = [
            models.Index(fields=["namespace", "status"]),
            models.Index(fields=["boost"]),
        ]

    def __str__(self):
        return f"{self.canonical_id}: {self.primary_name}"

    @property
    def all_meanings(self):
        """Get all symbolic meanings for this symbol."""
        return self.meanings.all().order_by("-frequency")


class SymbolMeaning(models.Model):
    """
    A specific symbolic meaning of a symbol.

    One symbol can have MULTIPLE meanings:
    - Water = purification (Levitical)
    - Water = Holy Spirit (John 7)
    - Water = judgment (flood)
    - Water = chaos (Genesis 1)
    - Water = nations (Revelation)

    Each meaning has its own biblical basis and context.
    """

    symbol = models.ForeignKey(
        BiblicalSymbol,
        on_delete=models.CASCADE,
        related_name="meanings",
    )

    # The meaning itself
    meaning = models.CharField(
        max_length=200,
        help_text="The symbolic meaning (e.g., 'Purification')",
    )
    meaning_pt = models.CharField(max_length=200, blank=True)

    # Explanation
    explanation = models.TextField(
        blank=True,
        help_text="Full explanation of this meaning",
    )
    explanation_pt = models.TextField(blank=True)

    # Theological context
    class TheologicalContext(models.TextChoices):
        SALVIFIC = "salvific", "Salvation/Redemption"
        JUDGMENT = "judgment", "Judgment/Wrath"
        BLESSING = "blessing", "Blessing/Favor"
        COVENANT = "covenant", "Covenant"
        ESCHATOLOGICAL = "eschatological", "End Times"
        CHRISTOLOGICAL = "christological", "About Christ"
        PNEUMATOLOGICAL = "pneumatological", "About Holy Spirit"
        ECCLESIOLOGICAL = "ecclesiological", "About Church"
        MORAL = "moral", "Moral/Ethical"
        WORSHIP = "worship", "Worship/Liturgy"
        CREATION = "creation", "Creation"
        GENERAL = "general", "General"

    theological_context = models.CharField(
        max_length=30,
        choices=TheologicalContext.choices,
        default=TheologicalContext.GENERAL,
    )

    # Positive or negative symbolism
    class Valence(models.TextChoices):
        POSITIVE = "positive", "Positive"
        NEGATIVE = "negative", "Negative"
        NEUTRAL = "neutral", "Neutral"
        AMBIVALENT = "ambivalent", "Context-dependent"

    valence = models.CharField(
        max_length=20,
        choices=Valence.choices,
        default=Valence.POSITIVE,
    )

    # Primary biblical basis
    primary_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Key verse for this meaning",
    )
    supporting_references = models.JSONField(
        default=list,
        blank=True,
        help_text="Additional supporting verses",
    )

    # Frequency and importance
    frequency = models.PositiveIntegerField(
        default=0,
        help_text="How often this meaning appears",
    )
    is_primary_meaning = models.BooleanField(
        default=False,
        help_text="Is this the most common meaning?",
    )

    # Testament focus
    class TestamentFocus(models.TextChoices):
        OLD = "old", "Old Testament"
        NEW = "new", "New Testament"
        BOTH = "both", "Both Testaments"

    testament_focus = models.CharField(
        max_length=10,
        choices=TestamentFocus.choices,
        default=TestamentFocus.BOTH,
    )

    # AI enrichment
    ai_analysis = models.TextField(
        blank=True,
        help_text="AI analysis of this meaning",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "symbol_meaning"
        verbose_name = "Symbol Meaning"
        verbose_name_plural = "Symbol Meanings"
        ordering = ["symbol", "-is_primary_meaning", "-frequency"]
        indexes = [
            models.Index(fields=["theological_context"]),
            models.Index(fields=["valence"]),
        ]

    def __str__(self):
        return f"{self.symbol.canonical_id} → {self.meaning}"


class SymbolOccurrence(models.Model):
    """
    An occurrence of a symbol in a specific verse.

    This tracks HOW the symbol is used in each verse,
    including which specific meaning is in view.
    """

    symbol = models.ForeignKey(
        BiblicalSymbol,
        on_delete=models.CASCADE,
        related_name="occurrences",
    )
    verse = models.ForeignKey(
        "bible.Verse",
        on_delete=models.CASCADE,
        related_name="symbol_occurrences",
    )

    # Which meaning is active here?
    meaning = models.ForeignKey(
        SymbolMeaning,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="occurrences",
        help_text="Which meaning is in view in this verse?",
    )

    # Interpretation context
    class UsageType(models.TextChoices):
        LITERAL = "literal", "Literal Usage"
        SYMBOLIC = "symbolic", "Symbolic/Figurative"
        BOTH = "both", "Both Literal and Symbolic"
        UNCERTAIN = "uncertain", "Uncertain"

    usage_type = models.CharField(
        max_length=20,
        choices=UsageType.choices,
        default=UsageType.SYMBOLIC,
    )

    # Context note
    context_note = models.TextField(
        blank=True,
        help_text="How is the symbol used in this specific context?",
    )
    context_note_pt = models.TextField(blank=True)

    # Match words — the actual words in the verse text that reference this symbol
    match_words = models.JSONField(
        default=list,
        blank=True,
        help_text="Words in the verse text that reference this symbol (for inline highlighting)",
    )

    # Literary genre context
    class Genre(models.TextChoices):
        NARRATIVE = "narrative", "Narrative"
        POETRY = "poetry", "Poetry/Wisdom"
        PROPHECY = "prophecy", "Prophecy"
        APOCALYPTIC = "apocalyptic", "Apocalyptic"
        LAW = "law", "Law"
        EPISTLE = "epistle", "Epistle"
        GOSPEL = "gospel", "Gospel"
        PARABLE = "parable", "Parable"

    genre = models.CharField(
        max_length=20,
        choices=Genre.choices,
        blank=True,
    )

    # Certainty of interpretation
    class Certainty(models.TextChoices):
        CERTAIN = "certain", "Certain"
        PROBABLE = "probable", "Probable"
        POSSIBLE = "possible", "Possible"
        DEBATED = "debated", "Debated"

    interpretation_certainty = models.CharField(
        max_length=20,
        choices=Certainty.choices,
        default=Certainty.PROBABLE,
    )

    # AI analysis
    ai_analysis = models.TextField(
        blank=True,
        help_text="AI interpretation of symbol in this context",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "symbol_occurrence"
        verbose_name = "Symbol Occurrence"
        verbose_name_plural = "Symbol Occurrences"
        unique_together = ["symbol", "verse"]
        indexes = [
            models.Index(fields=["usage_type"]),
            models.Index(fields=["genre"]),
        ]

    def __str__(self):
        return f"{self.symbol.canonical_id} @ {self.verse}"


class SymbolProgression(models.Model):
    """
    How a symbol's meaning DEVELOPS through biblical narrative.

    This tracks the progressive revelation of symbol meaning:
    - Lamb: animal sacrifice (Gen) → Passover (Ex) → Suffering Servant (Isa) → Christ (John) → Revelation

    This is crucial for biblical theology and understanding
    how symbols gain richer meaning over time.
    """

    symbol = models.ForeignKey(
        BiblicalSymbol,
        on_delete=models.CASCADE,
        related_name="progressions",
    )

    # Stage identification
    stage_order = models.PositiveIntegerField(
        help_text="Order in the progression (1=earliest)",
    )
    stage_name = models.CharField(
        max_length=200,
        help_text="Name of this stage (e.g., 'Paschal Lamb')",
    )
    stage_name_pt = models.CharField(max_length=200, blank=True)

    # Description
    description = models.TextField(
        help_text="How the symbol is understood at this stage",
    )
    description_pt = models.TextField(blank=True)

    # Biblical era/book
    biblical_era = models.CharField(
        max_length=100,
        blank=True,
        help_text="Era (e.g., 'Patriarchal', 'Exodus', 'Prophetic')",
    )
    primary_book = models.CharField(
        max_length=50,
        blank=True,
        help_text="Primary book for this stage",
    )
    key_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Key verse for this stage",
    )

    # Which meaning emerged at this stage?
    meaning = models.ForeignKey(
        SymbolMeaning,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="progression_stages",
    )

    # Theological development
    theological_development = models.TextField(
        blank=True,
        help_text="What new theological understanding emerged?",
    )

    # Christological connection (if any)
    christological_connection = models.TextField(
        blank=True,
        help_text="How does this stage point to Christ?",
    )
    is_fulfilled_in_christ = models.BooleanField(
        default=False,
        help_text="Is this the stage where Christ fulfills the symbol?",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "symbol_progression"
        verbose_name = "Symbol Progression"
        verbose_name_plural = "Symbol Progressions"
        ordering = ["symbol", "stage_order"]
        unique_together = ["symbol", "stage_order"]

    def __str__(self):
        return f"{self.symbol.canonical_id} Stage {self.stage_order}: {self.stage_name}"


class SymbolCategory(models.Model):
    """
    Categories for organizing symbols.

    Examples:
    - "Nature Symbols"
    - "Animal Symbols"
    - "Numbers with Meaning"
    - "Colors in Scripture"
    """

    slug = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    name_pt = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    description_pt = models.TextField(blank=True)

    # Hierarchy
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )

    # Display
    icon = models.CharField(max_length=50, blank=True)
    emoji = models.CharField(max_length=10, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    # Link to symbols
    symbols = models.ManyToManyField(
        BiblicalSymbol,
        related_name="symbol_categories",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "symbol_category"
        verbose_name = "Symbol Category"
        verbose_name_plural = "Symbol Categories"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name
