"""
Theology models - Systematic theology classification and doctrine management.

Key design decisions:
1. TheologicalDomain = The 10 loci of systematic theology (foundational classification)
2. Doctrine = Specific doctrines with multi-level explanations (beginner to advanced)
3. TheologicalPerspective = Different traditions for comparing viewpoints
4. DoctrinePerspectiveView = How each tradition interprets each doctrine
5. Confession = Historical creeds and confessions with parsed structure
6. TheologicalQuestion = FAQ system for theological inquiries
7. DoctrineVerseLink = Scripture proofs with support type classification

This domain is designed to:
- Power theological classification across the entire API
- Enable comparison of different theological traditions
- Support progressive learning (beginner → advanced)
- Connect doctrines to Scripture systematically
"""

from django.contrib.postgres.fields import ArrayField
from django.db import models


class TheologicalDomainSlug(models.TextChoices):
    """
    The 10 loci (areas) of systematic theology.
    These are the foundational categories for all theological content.
    """

    THEOLOGY_PROPER = "theology_proper", "Theology Proper (God)"
    CHRISTOLOGY = "christology", "Christology (Christ)"
    PNEUMATOLOGY = "pneumatology", "Pneumatology (Holy Spirit)"
    ANTHROPOLOGY = "anthropology", "Anthropology (Humanity)"
    HAMARTIOLOGY = "hamartiology", "Hamartiology (Sin)"
    SOTERIOLOGY = "soteriology", "Soteriology (Salvation)"
    ECCLESIOLOGY = "ecclesiology", "Ecclesiology (Church)"
    ESCHATOLOGY = "eschatology", "Eschatology (End Times)"
    BIBLIOLOGY = "bibliology", "Bibliology (Scripture)"
    ANGELOLOGY = "angelology", "Angelology (Angels/Demons)"
    ETHICS = "ethics", "Ethics & Morality"
    WORSHIP = "worship", "Worship & Liturgy"


class TheologicalDomain(models.Model):
    """
    The major areas/loci of systematic theology.

    These 10-12 domains organize ALL theological content:
    - Theology Proper: Study of God's nature and attributes
    - Christology: Study of Jesus Christ
    - Pneumatology: Study of the Holy Spirit
    - Anthropology: Study of humanity
    - Hamartiology: Study of sin
    - Soteriology: Study of salvation
    - Ecclesiology: Study of the church
    - Eschatology: Study of end times
    - Bibliology: Study of Scripture
    - Angelology: Study of angels and demons
    """

    # Identification
    slug = models.SlugField(
        max_length=50,
        unique=True,
        choices=TheologicalDomainSlug.choices,
        help_text="Unique identifier for this domain",
    )

    # Names (multilingual)
    name_en = models.CharField(max_length=100)
    name_pt = models.CharField(max_length=100)
    name_original = models.CharField(
        max_length=100,
        blank=True,
        help_text="Latin/Greek term (e.g., 'Soteriologia')",
    )

    # Descriptions
    description_en = models.TextField(blank=True)
    description_pt = models.TextField(blank=True)

    # Central question this domain answers
    central_question_en = models.CharField(
        max_length=200,
        blank=True,
        help_text="E.g., 'Who is God?' for Theology Proper",
    )
    central_question_pt = models.CharField(max_length=200, blank=True)

    # UI/UX
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Emoji or icon name (e.g., '✝️')",
    )
    color = models.CharField(
        max_length=20,
        blank=True,
        help_text="Hex color for UI (e.g., '#8B0000')",
    )

    # Study curriculum
    study_order = models.PositiveIntegerField(
        default=0,
        help_text="Recommended order for studying domains (1=first)",
    )
    prerequisite_domains = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="dependent_domains",
        help_text="Domains that should be studied before this one",
    )
    related_domains = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=True,
        help_text="Related domains for cross-reference",
    )

    # Metrics
    difficulty_level = models.PositiveIntegerField(
        default=50,
        help_text="Overall difficulty (1-100)",
    )
    estimated_study_hours = models.PositiveIntegerField(
        default=10,
        help_text="Estimated hours to study this domain",
    )

    # AI Enrichment
    ai_summary = models.TextField(blank=True)
    ai_summary_pt = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "theological_domain"
        verbose_name = "Theological Domain"
        verbose_name_plural = "Theological Domains"
        ordering = ["study_order", "name_en"]

    def __str__(self):
        return f"{self.slug}: {self.name_en}"

    @property
    def doctrine_count(self):
        return self.doctrines.count()


class DoctrineImportance(models.TextChoices):
    """How essential is this doctrine to Christian faith?"""

    ESSENTIAL = "essential", "Essential (Creedal)"
    IMPORTANT = "important", "Important (Confessional)"
    SECONDARY = "secondary", "Secondary (Denominational)"
    TERTIARY = "tertiary", "Tertiary (Disputable)"
    SPECULATIVE = "speculative", "Speculative (Debated)"


class DoctrineConsensus(models.TextChoices):
    """Level of agreement across Christian traditions."""

    ECUMENICAL = "ecumenical", "Ecumenical (All Christians)"
    ORTHODOX = "orthodox", "Orthodox (Catholic/Protestant/Orthodox)"
    PROTESTANT = "protestant", "Protestant Consensus"
    EVANGELICAL = "evangelical", "Evangelical Consensus"
    REFORMED = "reformed", "Reformed Tradition"
    ARMINIAN = "arminian", "Arminian Tradition"
    DISPUTED = "disputed", "Disputed Across Traditions"


class DoctrineStatus(models.TextChoices):
    """Curation status of the doctrine."""

    DRAFT = "draft", "Draft"
    REVIEW = "review", "Under Review"
    APPROVED = "approved", "Approved"
    CANONICAL = "canonical", "Canonical"


class Doctrine(models.Model):
    """
    A specific doctrine within a theological domain.

    Examples:
    - Trinity (Theology Proper)
    - Incarnation (Christology)
    - Justification by Faith (Soteriology)
    - Baptism (Ecclesiology)
    - Second Coming (Eschatology)

    Features:
    - Multi-level explanations (beginner → advanced)
    - Importance classification (essential → speculative)
    - Consensus level across traditions
    - Historical development tracking
    - Scripture proofs
    """

    # Identification
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="URL-safe identifier (e.g., 'incarnation')",
    )
    domain = models.ForeignKey(
        TheologicalDomain,
        on_delete=models.CASCADE,
        related_name="doctrines",
    )

    # Names (multilingual)
    name_en = models.CharField(max_length=200)
    name_pt = models.CharField(max_length=200)
    name_latin = models.CharField(
        max_length=200,
        blank=True,
        help_text="Latin theological term",
    )

    # === MULTI-LEVEL EXPLANATIONS (INNOVATIVE) ===
    # Concise definition for cards/previews
    definition_en = models.TextField(
        help_text="One-sentence definition",
    )
    definition_pt = models.TextField(blank=True)

    # Full explanation
    explanation_en = models.TextField(blank=True)
    explanation_pt = models.TextField(blank=True)

    # Beginner-friendly explanation
    explanation_beginner_en = models.TextField(
        blank=True,
        help_text="Simple explanation for new believers",
    )
    explanation_beginner_pt = models.TextField(blank=True)

    # Intermediate explanation
    explanation_intermediate_en = models.TextField(
        blank=True,
        help_text="Detailed explanation for growing Christians",
    )
    explanation_intermediate_pt = models.TextField(blank=True)

    # Advanced/academic explanation
    explanation_advanced_en = models.TextField(
        blank=True,
        help_text="Technical explanation for theology students",
    )
    explanation_advanced_pt = models.TextField(blank=True)

    # === HIERARCHY ===
    parent_doctrine = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_doctrines",
        help_text="Parent doctrine for hierarchy",
    )

    # === IMPORTANCE & CONSENSUS ===
    importance = models.CharField(
        max_length=20,
        choices=DoctrineImportance.choices,
        default=DoctrineImportance.IMPORTANT,
        help_text="How essential is this doctrine?",
    )
    consensus_level = models.CharField(
        max_length=20,
        choices=DoctrineConsensus.choices,
        default=DoctrineConsensus.EVANGELICAL,
        help_text="Level of agreement across traditions",
    )

    # === SCRIPTURE PROOFS ===
    anchor_verses = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Primary Scripture proofs (e.g., ['John 1:1', 'John 1:14'])",
    )
    supporting_verses = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Additional supporting verses",
    )

    # === HISTORICAL DEVELOPMENT ===
    historical_development_en = models.TextField(
        blank=True,
        help_text="How this doctrine developed through church history",
    )
    historical_development_pt = models.TextField(blank=True)

    key_councils = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Church councils that addressed this (e.g., ['Nicaea 325'])",
    )
    key_figures = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Key theologians (e.g., ['Athanasius', 'Augustine'])",
    )
    year_formulated = models.CharField(
        max_length=50,
        blank=True,
        help_text="When doctrine was formally articulated",
    )

    # === RELATIONSHIPS ===
    related_doctrines = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=True,
        related_name="+",
        help_text="Related doctrines",
    )
    contrasting_doctrines = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="contrasted_by",
        help_text="Opposing/heretical views",
    )
    prerequisite_doctrines = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="dependent_doctrines",
        help_text="Doctrines that should be understood first",
    )

    # === PRACTICAL APPLICATION ===
    practical_implications_en = models.TextField(
        blank=True,
        help_text="How this doctrine applies to daily life",
    )
    practical_implications_pt = models.TextField(blank=True)

    devotional_reflection_en = models.TextField(
        blank=True,
        help_text="Devotional/worship implications",
    )
    devotional_reflection_pt = models.TextField(blank=True)

    common_misunderstandings = ArrayField(
        models.CharField(max_length=300),
        default=list,
        blank=True,
        help_text="Common errors about this doctrine",
    )

    # === STUDY METRICS ===
    study_value = models.PositiveIntegerField(
        default=50,
        help_text="Educational value (1-100)",
    )
    difficulty_level = models.PositiveIntegerField(
        default=50,
        help_text="Complexity level (1-100)",
    )
    estimated_study_time = models.PositiveIntegerField(
        default=30,
        help_text="Estimated minutes to study",
    )

    # === UI/UX ===
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=20, blank=True)

    # === AI ENRICHMENT ===
    ai_enriched = models.BooleanField(default=False)
    ai_enriched_at = models.DateTimeField(null=True, blank=True)
    ai_summary = models.TextField(blank=True)
    ai_summary_pt = models.TextField(blank=True)

    # === STATUS ===
    status = models.CharField(
        max_length=20,
        choices=DoctrineStatus.choices,
        default=DoctrineStatus.DRAFT,
    )

    # === ENGAGEMENT ===
    view_count = models.PositiveIntegerField(default=0)
    bookmark_count = models.PositiveIntegerField(default=0)

    # === METADATA ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "doctrine"
        verbose_name = "Doctrine"
        verbose_name_plural = "Doctrines"
        ordering = ["domain", "importance", "name_en"]
        indexes = [
            models.Index(fields=["domain", "importance"]),
            models.Index(fields=["consensus_level"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.domain.slug}/{self.slug}: {self.name_en}"

    @property
    def is_essential(self):
        return self.importance == DoctrineImportance.ESSENTIAL

    @property
    def is_ecumenical(self):
        return self.consensus_level == DoctrineConsensus.ECUMENICAL


class TheologicalPerspective(models.Model):
    """
    Different theological traditions/perspectives.

    Examples:
    - Reformed (Calvinist)
    - Arminian (Wesleyan)
    - Lutheran
    - Baptist
    - Catholic
    - Orthodox
    - Pentecostal

    This allows comparing how different traditions view the same doctrine.
    """

    # Identification
    slug = models.SlugField(max_length=50, unique=True)

    # Names
    name_en = models.CharField(max_length=100)
    name_pt = models.CharField(max_length=100)

    # Description
    description_en = models.TextField(blank=True)
    description_pt = models.TextField(blank=True)

    # Historical origin
    origin_year = models.CharField(
        max_length=50,
        blank=True,
        help_text="When this tradition emerged",
    )
    origin_location = models.CharField(max_length=200, blank=True)
    founder = models.CharField(
        max_length=200,
        blank=True,
        help_text="Key founder (e.g., 'John Calvin')",
    )

    # Distinctive beliefs
    distinctives = ArrayField(
        models.CharField(max_length=200),
        default=list,
        blank=True,
        help_text="Key distinctives (e.g., ['Sola Scriptura', 'TULIP'])",
    )

    # Key figures
    key_figures = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Important theologians in this tradition",
    )

    # Relationships
    parent_perspective = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_perspectives",
        help_text="Parent tradition (e.g., Reformed → Calvinist)",
    )
    related_perspectives = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=True,
    )

    # Classification
    class TraditionType(models.TextChoices):
        CATHOLIC = "catholic", "Catholic"
        ORTHODOX = "orthodox", "Orthodox"
        PROTESTANT = "protestant", "Protestant"
        EVANGELICAL = "evangelical", "Evangelical"
        OTHER = "other", "Other"

    tradition_type = models.CharField(
        max_length=20,
        choices=TraditionType.choices,
        default=TraditionType.PROTESTANT,
    )

    # UI
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=20, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "theological_perspective"
        verbose_name = "Theological Perspective"
        verbose_name_plural = "Theological Perspectives"
        ordering = ["name_en"]

    def __str__(self):
        return self.name_en


class DoctrinePerspectiveView(models.Model):
    """
    How a specific theological perspective views a specific doctrine.

    This enables powerful comparisons:
    - "What do Reformed Christians believe about predestination?"
    - "How do Arminians and Calvinists differ on free will?"
    - "Compare Catholic and Protestant views on justification"
    """

    doctrine = models.ForeignKey(
        Doctrine,
        on_delete=models.CASCADE,
        related_name="perspective_views",
    )
    perspective = models.ForeignKey(
        TheologicalPerspective,
        on_delete=models.CASCADE,
        related_name="doctrine_views",
    )

    # Position
    position_summary_en = models.TextField(
        help_text="Brief summary of this tradition's position",
    )
    position_summary_pt = models.TextField(blank=True)

    position_detailed_en = models.TextField(
        blank=True,
        help_text="Detailed explanation of the position",
    )
    position_detailed_pt = models.TextField(blank=True)

    # Scripture proofs used by this tradition
    supporting_verses = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Verses this tradition uses to support their view",
    )

    # Key arguments
    key_arguments = ArrayField(
        models.CharField(max_length=500),
        default=list,
        blank=True,
        help_text="Main arguments for this position",
    )

    # Historical figures who held this view
    notable_proponents = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
    )

    # Relationships with other views
    agrees_with = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=True,
        related_name="+",
        help_text="Other perspective views that agree",
    )
    disagrees_with = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=True,
        related_name="+",
        help_text="Other perspective views that disagree",
    )

    # Strength of argument (for educational ranking)
    argument_strength = models.PositiveIntegerField(
        default=50,
        help_text="Scholarly strength of arguments (1-100)",
    )

    # Is this the majority/official view of the tradition?
    is_official_position = models.BooleanField(
        default=True,
        help_text="Is this the official/majority position of this tradition?",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "doctrine_perspective_view"
        verbose_name = "Doctrine Perspective View"
        verbose_name_plural = "Doctrine Perspective Views"
        unique_together = ["doctrine", "perspective"]
        indexes = [
            models.Index(fields=["doctrine"]),
            models.Index(fields=["perspective"]),
        ]

    def __str__(self):
        return f"{self.doctrine.slug} ({self.perspective.slug})"


class ConfessionType(models.TextChoices):
    """Types of confessional documents."""

    CREED = "creed", "Creed (Short, Ecumenical)"
    CONFESSION = "confession", "Confession (Long, Denominational)"
    CATECHISM = "catechism", "Catechism (Q&A Format)"
    ARTICLES = "articles", "Articles of Faith"
    CANONS = "canons", "Canons/Decrees"


class Confession(models.Model):
    """
    Historical creeds and confessions of faith.

    Examples:
    - Apostles' Creed
    - Nicene Creed
    - Westminster Confession of Faith
    - Heidelberg Catechism
    - Augsburg Confession
    - Canons of Dort

    These documents represent the church's historical understanding of doctrine.
    """

    # Identification
    slug = models.SlugField(max_length=100, unique=True)

    # Names
    name_en = models.CharField(max_length=200)
    name_pt = models.CharField(max_length=200)
    name_original = models.CharField(
        max_length=200,
        blank=True,
        help_text="Original language name",
    )

    # Description
    description_en = models.TextField(blank=True)
    description_pt = models.TextField(blank=True)

    # Type
    confession_type = models.CharField(
        max_length=20,
        choices=ConfessionType.choices,
        default=ConfessionType.CONFESSION,
    )

    # Historical context
    year = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Year written/adopted",
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Where it was written (e.g., 'Westminster, England')",
    )
    authors = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Authors or assembly",
    )
    historical_context = models.TextField(
        blank=True,
        help_text="Why this confession was written",
    )

    # Theological tradition
    perspective = models.ForeignKey(
        TheologicalPerspective,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confessions",
    )

    # Full text
    full_text_en = models.TextField(
        blank=True,
        help_text="Complete text in English",
    )
    full_text_pt = models.TextField(blank=True)
    full_text_original = models.TextField(
        blank=True,
        help_text="Original language text",
    )
    original_language = models.CharField(
        max_length=20,
        blank=True,
        help_text="Original language code (en, la, de, etc.)",
    )

    # Ecumenical status
    class EcumenicalStatus(models.TextChoices):
        ECUMENICAL = "ecumenical", "Ecumenical (All Christians)"
        PROTESTANT = "protestant", "Protestant"
        REFORMED = "reformed", "Reformed"
        LUTHERAN = "lutheran", "Lutheran"
        ANGLICAN = "anglican", "Anglican"
        BAPTIST = "baptist", "Baptist"
        CATHOLIC = "catholic", "Catholic"
        ORTHODOX = "orthodox", "Orthodox"
        OTHER = "other", "Other"

    ecumenical_status = models.CharField(
        max_length=20,
        choices=EcumenicalStatus.choices,
        default=EcumenicalStatus.PROTESTANT,
    )

    # Adoption
    adopted_by = ArrayField(
        models.CharField(max_length=200),
        default=list,
        blank=True,
        help_text="Denominations that officially adopt this confession",
    )

    # Study metrics
    study_value = models.PositiveIntegerField(default=50)
    difficulty_level = models.PositiveIntegerField(default=50)

    # External links
    wikipedia_url = models.URLField(blank=True)
    source_url = models.URLField(
        blank=True,
        help_text="Link to authoritative source",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "confession"
        verbose_name = "Confession"
        verbose_name_plural = "Confessions"
        ordering = ["year", "name_en"]

    def __str__(self):
        year_str = f" ({self.year})" if self.year else ""
        return f"{self.name_en}{year_str}"


class ConfessionArticle(models.Model):
    """
    Individual articles/chapters of a confession.

    This allows:
    - Navigating confessions by chapter
    - Linking specific articles to doctrines
    - Searching within confessions
    """

    confession = models.ForeignKey(
        Confession,
        on_delete=models.CASCADE,
        related_name="articles",
    )

    # Identification
    chapter = models.PositiveIntegerField(help_text="Chapter number")
    section = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Section number within chapter",
    )
    question_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Question number (for catechisms)",
    )

    # Title
    title_en = models.CharField(max_length=300)
    title_pt = models.CharField(max_length=300, blank=True)

    # Content
    text_en = models.TextField()
    text_pt = models.TextField(blank=True)
    text_original = models.TextField(blank=True)

    # For catechisms: Question/Answer format
    question_en = models.TextField(
        blank=True,
        help_text="Question text (for catechisms)",
    )
    question_pt = models.TextField(blank=True)
    answer_en = models.TextField(
        blank=True,
        help_text="Answer text (for catechisms)",
    )
    answer_pt = models.TextField(blank=True)

    # Scripture proofs cited in the confession
    scripture_proofs = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Scripture references cited as proofs",
    )

    # Link to doctrines this article teaches
    doctrines = models.ManyToManyField(
        Doctrine,
        blank=True,
        related_name="confession_articles",
        help_text="Doctrines taught in this article",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "confession_article"
        verbose_name = "Confession Article"
        verbose_name_plural = "Confession Articles"
        ordering = ["confession", "chapter", "section"]
        unique_together = ["confession", "chapter", "section"]

    def __str__(self):
        section_str = f".{self.section}" if self.section else ""
        return f"{self.confession.slug} {self.chapter}{section_str}: {self.title_en}"


class QuestionDifficulty(models.TextChoices):
    """Difficulty level of theological questions."""

    BEGINNER = "beginner", "Beginner"
    INTERMEDIATE = "intermediate", "Intermediate"
    ADVANCED = "advanced", "Advanced"
    EXPERT = "expert", "Expert/Academic"


class TheologicalQuestion(models.Model):
    """
    Common theological questions people ask.

    This powers:
    - FAQ sections
    - Search suggestions
    - AI assistant training
    - Study guides

    Examples:
    - "Is Jesus God?"
    - "What happens after we die?"
    - "Why does God allow suffering?"
    - "What is the Trinity?"
    """

    # The question
    question_en = models.TextField()
    question_pt = models.TextField(blank=True)

    # Alternative phrasings (for search)
    alternate_phrasings = ArrayField(
        models.CharField(max_length=500),
        default=list,
        blank=True,
        help_text="Other ways people ask this question",
    )

    # Classification
    domain = models.ForeignKey(
        TheologicalDomain,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="questions",
    )
    doctrine = models.ForeignKey(
        Doctrine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="questions",
    )

    # Difficulty
    difficulty = models.CharField(
        max_length=20,
        choices=QuestionDifficulty.choices,
        default=QuestionDifficulty.BEGINNER,
    )

    # Consensus answer (if there is one)
    has_consensus = models.BooleanField(
        default=True,
        help_text="Is there consensus among Christians?",
    )
    consensus_answer_en = models.TextField(
        blank=True,
        help_text="The answer most Christians would agree on",
    )
    consensus_answer_pt = models.TextField(blank=True)

    # Short answer for quick display
    short_answer_en = models.CharField(
        max_length=500,
        blank=True,
        help_text="One-sentence answer",
    )
    short_answer_pt = models.CharField(max_length=500, blank=True)

    # Key verses that answer this question
    key_verses = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
    )

    # Search/discovery
    search_tags = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Tags for search (e.g., ['salvation', 'eternal life'])",
    )

    # Frequency/popularity
    frequency = models.PositiveIntegerField(
        default=0,
        help_text="How often this question is asked",
    )
    is_common = models.BooleanField(
        default=False,
        help_text="Is this a frequently asked question?",
    )

    # Related questions
    related_questions = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=True,
    )

    # Engagement
    view_count = models.PositiveIntegerField(default=0)
    helpful_count = models.PositiveIntegerField(default=0)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "theological_question"
        verbose_name = "Theological Question"
        verbose_name_plural = "Theological Questions"
        ordering = ["-frequency", "question_en"]
        indexes = [
            models.Index(fields=["domain"]),
            models.Index(fields=["difficulty"]),
            models.Index(fields=["is_common"]),
        ]

    def __str__(self):
        return self.question_en[:100]


class VerseSupportType(models.TextChoices):
    """How strongly does a verse support a doctrine?"""

    PRIMARY = "primary", "Primary Proof (Direct)"
    SUPPORTING = "supporting", "Supporting (Secondary)"
    ILLUSTRATIVE = "illustrative", "Illustrative (Example)"
    IMPLICIT = "implicit", "Implicit (Inferred)"
    TYPOLOGICAL = "typological", "Typological (Type/Shadow)"
    DISPUTED = "disputed", "Disputed (Debated)"


class DoctrineVerseLink(models.Model):
    """
    Link between a doctrine and a supporting verse.

    This provides:
    - Scripture proofs for each doctrine
    - Context for how each verse supports the doctrine
    - Which traditions use which verses
    - Strength of the support
    """

    doctrine = models.ForeignKey(
        Doctrine,
        on_delete=models.CASCADE,
        related_name="verse_links",
    )
    verse = models.ForeignKey(
        "bible.Verse",
        on_delete=models.CASCADE,
        related_name="doctrine_links",
    )

    # Support type
    support_type = models.CharField(
        max_length=20,
        choices=VerseSupportType.choices,
        default=VerseSupportType.SUPPORTING,
    )

    # Explanation
    explanation_en = models.TextField(
        blank=True,
        help_text="How this verse supports the doctrine",
    )
    explanation_pt = models.TextField(blank=True)

    # Which traditions use this verse for this doctrine?
    perspectives_using = models.ManyToManyField(
        TheologicalPerspective,
        blank=True,
        related_name="doctrine_verse_usages",
        help_text="Which traditions cite this verse for this doctrine",
    )

    # Hermeneutical notes
    hermeneutical_notes = models.TextField(
        blank=True,
        help_text="Notes on interpretation of this verse",
    )

    # Strength/relevance
    relevance = models.FloatField(
        default=1.0,
        help_text="Relevance score (0-1)",
    )

    # Is this disputed?
    is_disputed = models.BooleanField(
        default=False,
        help_text="Is the use of this verse for this doctrine disputed?",
    )
    dispute_notes = models.TextField(
        blank=True,
        help_text="Notes on the dispute",
    )

    # AI analysis
    ai_analysis = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "doctrine_verse_link"
        verbose_name = "Doctrine-Verse Link"
        verbose_name_plural = "Doctrine-Verse Links"
        unique_together = ["doctrine", "verse"]
        indexes = [
            models.Index(fields=["support_type"]),
            models.Index(fields=["is_disputed"]),
        ]

    def __str__(self):
        return f"{self.doctrine.slug} ← {self.verse}"
