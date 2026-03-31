"""
Entities models - Biblical entities with temporal roles and relationships.

Key design decisions:
1. Entities have MULTIPLE ROLES over time (David: shepherd → warrior → king → prophet)
2. Jesus has dual nature tracked via roles (pre-existent Logos → incarnate human → risen Lord)
3. Multilingual support via EntityAlias with language codes
4. Timeline events for biographical/historical data
5. Verse links with role context (which role was active in that verse?)
6. Entity-to-entity relationships with temporal awareness
"""

from django.db import models

# NOTE: Using string references to avoid circular imports
# Language model is referenced as "books.Language" in ForeignKey


class EntityNamespace(models.TextChoices):
    """
    Namespace categories for entities.
    Based on gazetteer VALID_NAMESPACES.
    """

    PERSON = "PERSON", "Person"
    DEITY = "DEITY", "Deity"
    PLACE = "PLACE", "Place"
    ANGEL = "ANGEL", "Angel"
    CONCEPT = "CONCEPT", "Concept"
    OBJECT = "OBJECT", "Object"
    EVENT = "EVENT", "Event"
    LITERARY_WORK = "LITERARY_WORK", "Literary Work"
    GROUP = "GROUP", "Group/Nation/Tribe"
    CREATURE = "CREATURE", "Creature"
    PLANT = "PLANT", "Plant"
    RITUAL = "RITUAL", "Ritual/Ceremony"
    LITERARY_FORM = "LITERARY_FORM", "Literary Form"


class EntityStatus(models.TextChoices):
    """Entity curation status."""

    DRAFT = "draft", "Draft"
    REVIEW = "review", "Under Review"
    APPROVED = "approved", "Approved"
    CANONICAL = "canonical", "Canonical"


class RoleType(models.TextChoices):
    """
    Types of roles an entity can have.
    These represent functions/positions that can change over time.
    """

    # Person roles
    SHEPHERD = "shepherd", "Shepherd"
    FARMER = "farmer", "Farmer"
    FISHERMAN = "fisherman", "Fisherman"
    CARPENTER = "carpenter", "Carpenter"
    TENTMAKER = "tentmaker", "Tentmaker"
    SOLDIER = "soldier", "Soldier"
    WARRIOR = "warrior", "Warrior"
    KING = "king", "King"
    QUEEN = "queen", "Queen"
    PRINCE = "prince", "Prince"
    PRINCESS = "princess", "Princess"
    PRIEST = "priest", "Priest"
    HIGH_PRIEST = "high_priest", "High Priest"
    LEVITE = "levite", "Levite"
    PROPHET = "prophet", "Prophet"
    PROPHETESS = "prophetess", "Prophetess"
    JUDGE = "judge", "Judge"
    APOSTLE = "apostle", "Apostle"
    DISCIPLE = "disciple", "Disciple"
    TEACHER = "teacher", "Teacher/Rabbi"
    SCRIBE = "scribe", "Scribe"
    PHARISEE = "pharisee", "Pharisee"
    SADDUCEE = "sadducee", "Sadducee"
    ELDER = "elder", "Elder"
    DEACON = "deacon", "Deacon"
    EVANGELIST = "evangelist", "Evangelist"
    SERVANT = "servant", "Servant"
    SLAVE = "slave", "Slave"
    WIFE = "wife", "Wife"
    HUSBAND = "husband", "Husband"
    MOTHER = "mother", "Mother"
    FATHER = "father", "Father"
    CHILD = "child", "Child"
    WIDOW = "widow", "Widow"
    PATRIARCH = "patriarch", "Patriarch"
    MATRIARCH = "matriarch", "Matriarch"
    ANCESTOR = "ancestor", "Ancestor of Messiah"
    MUSICIAN = "musician", "Musician"
    PSALMIST = "psalmist", "Psalmist"
    CUPBEARER = "cupbearer", "Cupbearer"
    GOVERNOR = "governor", "Governor"
    TAX_COLLECTOR = "tax_collector", "Tax Collector"
    PHYSICIAN = "physician", "Physician"
    SORCERER = "sorcerer", "Sorcerer/Magician"

    # Deity/Divine roles (for Jesus, God)
    PRE_EXISTENT = "pre_existent", "Pre-existent (Logos)"
    CREATOR = "creator", "Creator"
    INCARNATE = "incarnate", "Incarnate/Human"
    MESSIAH = "messiah", "Messiah/Christ"
    LAMB = "lamb", "Sacrificial Lamb"
    RISEN = "risen", "Risen Lord"
    ASCENDED = "ascended", "Ascended King"
    INTERCESSOR = "intercessor", "Intercessor"
    JUDGE_DIVINE = "judge_divine", "Divine Judge"
    RETURNING = "returning", "Returning King"

    # Angel roles
    MESSENGER = "messenger", "Messenger"
    GUARDIAN = "guardian", "Guardian"
    WARRIOR_ANGEL = "warrior_angel", "Warrior Angel"
    SERAPH = "seraph", "Seraph"
    CHERUB = "cherub", "Cherub"
    ARCHANGEL = "archangel", "Archangel"

    # Place roles (places can change function too!)
    CAPITAL = "capital", "Capital City"
    TEMPLE_SITE = "temple_site", "Temple Site"
    BATTLEFIELD = "battlefield", "Battlefield"
    REFUGE = "refuge", "City of Refuge"
    SANCTUARY = "sanctuary", "Sanctuary"
    WILDERNESS = "wilderness", "Wilderness"
    PROMISED_LAND = "promised_land", "Promised Land"
    EXILE = "exile", "Place of Exile"

    # Generic
    OTHER = "other", "Other"


class RelationshipType(models.TextChoices):
    """
    Types of relationships between entities.
    Based on relationships_gazetteer.json types.
    """

    # Family relationships
    PARENT_OF = "parent_of", "Parent of"
    CHILD_OF = "child_of", "Child of"
    SIBLING = "sibling", "Sibling"
    SPOUSE_OF = "spouse_of", "Spouse of"
    ANCESTOR_OF = "ancestor_of", "Ancestor of"
    DESCENDANT_OF = "descendant_of", "Descendant of"

    # Social/Political relationships
    KING_OF = "king_of", "King of"
    SUBJECT_OF = "subject_of", "Subject of"
    SERVANT_OF = "servant_of", "Servant of"
    MASTER_OF = "master_of", "Master of"
    LEADER_OF = "leader_of", "Leader of"
    MEMBER_OF = "member_of", "Member of"

    # Spiritual relationships
    DISCIPLE_OF = "disciple_of", "Disciple of"
    TEACHER_OF = "teacher_of", "Teacher of"
    SUCCESSOR_OF = "successor_of", "Successor of"
    PREDECESSOR_OF = "predecessor_of", "Predecessor of"
    ANOINTED_BY = "anointed_by", "Anointed by"

    # Conflict relationships
    ENEMY_OF = "enemy_of", "Enemy of"
    ALLY_OF = "ally_of", "Ally of"
    BETRAYED_BY = "betrayed_by", "Betrayed by"
    KILLED_BY = "killed_by", "Killed by"
    PERSECUTOR_OF = "persecutor_of", "Persecutor of"

    # Place relationships
    BORN_IN = "born_in", "Born in"
    DIED_IN = "died_in", "Died in"
    LIVED_IN = "lived_in", "Lived in"
    TRAVELED_TO = "traveled_to", "Traveled to"
    EXILED_TO = "exiled_to", "Exiled to"
    CONQUERED = "conquered", "Conquered"
    FOUNDED = "founded", "Founded"
    BUILT = "built", "Built"

    # Typological relationships
    TYPE_OF = "type_of", "Type/Shadow of"
    ANTITYPE_OF = "antitype_of", "Antitype/Fulfillment of"
    FORESHADOWS = "foreshadows", "Foreshadows"
    FULFILLS = "fulfills", "Fulfills"
    PARALLELS = "parallels", "Parallels"
    CONTRASTS = "contrasts", "Contrasts with"

    # Association
    ASSOCIATED_WITH = "associated_with", "Associated with"
    PART_OF = "part_of", "Part of"
    CONTEMPORARY_OF = "contemporary_of", "Contemporary of"

    OTHER = "other", "Other"


class CanonicalEntity(models.Model):
    """
    A canonical biblical entity (person, place, concept, etc.).

    This is the "master record" for an entity. The entity's roles, names,
    and relationships are tracked separately to allow temporal variation.

    Example: David (PER:david)
    - Has roles: shepherd, warrior, king, prophet, psalmist
    - Has aliases: David, Davi, דָּוִד, Δαβίδ
    - Has relationships: son of Jesse, father of Solomon, type of Christ
    """

    # Person Hub Link (for PERSON/DEITY namespace only)
    person = models.OneToOneField(
        "people.Person",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="biblical_profile",
        help_text="Link to unified Person identity hub (PERSON/DEITY namespace only)",
    )

    # Identification
    canonical_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique identifier like 'PER:david', 'PLC:jerusalem'",
    )
    namespace = models.CharField(
        max_length=20,
        choices=EntityNamespace.choices,
        db_index=True,
        help_text="Primary namespace (PERSON, PLACE, DEITY, etc.)",
    )

    # Primary name (canonical form)
    primary_name = models.CharField(
        max_length=200,
        help_text="Primary canonical name in English",
    )
    primary_name_original = models.CharField(
        max_length=200,
        blank=True,
        help_text="Original language name (Hebrew/Greek/Aramaic)",
    )

    # Brief description
    description = models.TextField(
        blank=True,
        help_text="Brief description of the entity",
    )
    description_pt = models.TextField(
        blank=True,
        help_text="Description in Portuguese",
    )

    # Classification & Search
    boost = models.FloatField(
        default=1.0,
        help_text="Search ranking boost (higher = more important)",
    )
    priority = models.PositiveIntegerField(
        default=50,
        help_text="Display priority (1-100, higher = more prominent)",
    )
    categories = models.JSONField(
        default=list,
        blank=True,
        help_text="Category tags for filtering",
    )

    # Status & Curation
    status = models.CharField(
        max_length=20,
        choices=EntityStatus.choices,
        default=EntityStatus.DRAFT,
    )

    # AI Enrichment
    ai_enriched = models.BooleanField(default=False)
    ai_enriched_at = models.DateTimeField(null=True, blank=True)
    ai_summary = models.TextField(
        blank=True,
        help_text="AI-generated comprehensive summary",
    )
    ai_summary_pt = models.TextField(
        blank=True,
        help_text="AI-generated summary in Portuguese",
    )
    ai_theological_significance = models.TextField(
        blank=True,
        help_text="AI analysis of theological importance",
    )
    ai_historical_context = models.TextField(
        blank=True,
        help_text="AI-generated historical/archaeological context",
    )

    # Etymology & Linguistics
    etymology = models.TextField(
        blank=True,
        help_text="Name etymology and meaning",
    )
    hebrew_transliteration = models.CharField(max_length=200, blank=True)
    greek_transliteration = models.CharField(max_length=200, blank=True)
    strongs_hebrew = models.CharField(
        max_length=20,
        blank=True,
        help_text="Strong's Hebrew number if applicable",
    )
    strongs_greek = models.CharField(
        max_length=20,
        blank=True,
        help_text="Strong's Greek number if applicable",
    )

    # Timeline (approximate)
    birth_year = models.CharField(
        max_length=50,
        blank=True,
        help_text="Approximate birth year (e.g., '~1040 BC')",
    )
    death_year = models.CharField(
        max_length=50,
        blank=True,
        help_text="Approximate death year",
    )
    active_period = models.CharField(
        max_length=100,
        blank=True,
        help_text="Period of primary activity (e.g., '1010-970 BC')",
    )
    biblical_era = models.CharField(
        max_length=100,
        blank=True,
        help_text="Biblical era (e.g., 'United Monarchy', 'Exile')",
    )

    # Study metrics
    study_value = models.PositiveIntegerField(
        default=50,
        help_text="Value for Bible study (1-100)",
    )
    difficulty_level = models.PositiveIntegerField(
        default=50,
        help_text="Complexity level (1-100, 100=most complex)",
    )
    verse_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of verses mentioning this entity",
    )

    # Engagement tracking
    view_count = models.PositiveIntegerField(default=0)
    bookmark_count = models.PositiveIntegerField(default=0)

    # Typology (for people who are types of Christ)
    is_type_of_christ = models.BooleanField(
        default=False,
        help_text="Is this entity a type/shadow of Christ?",
    )
    typology_explanation = models.TextField(
        blank=True,
        help_text="How this entity prefigures Christ",
    )

    # External references
    wikidata_id = models.CharField(max_length=20, blank=True)
    wikipedia_url = models.URLField(blank=True)
    easton_bible_dict_url = models.URLField(blank=True)
    hitchcock_url = models.URLField(blank=True)

    # Source tracking
    source_topics = models.JSONField(
        default=list,
        blank=True,
        help_text="Original topic keys that referenced this entity",
    )
    source_gazetteer = models.CharField(
        max_length=100,
        blank=True,
        help_text="Source gazetteer file",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "canonical_entity"
        verbose_name = "Canonical Entity"
        verbose_name_plural = "Canonical Entities"
        ordering = ["-priority", "primary_name"]
        indexes = [
            models.Index(fields=["namespace", "status"]),
            models.Index(fields=["boost"]),
            models.Index(fields=["is_type_of_christ"]),
        ]

    def __str__(self):
        return f"{self.canonical_id}: {self.primary_name}"

    @property
    def current_roles(self):
        """Get all roles for this entity."""
        return self.roles.all().order_by("narrative_order")

    @property
    def is_person(self):
        return self.namespace == EntityNamespace.PERSON

    @property
    def is_deity(self):
        return self.namespace == EntityNamespace.DEITY

    @property
    def is_place(self):
        return self.namespace == EntityNamespace.PLACE


class EntityAlias(models.Model):
    """
    Alternative names for an entity in different languages.

    Example for David:
    - "David" (en)
    - "Davi" (pt)
    - "דָּוִד" (he)
    - "Δαβίδ" (el)
    - "Dawid" (transliteration)
    """

    entity = models.ForeignKey(
        CanonicalEntity,
        on_delete=models.CASCADE,
        related_name="aliases",
    )
    name = models.CharField(max_length=200)
    language = models.ForeignKey(
        "bible.Language",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Language of this alias",
    )
    language_code = models.CharField(
        max_length=10,
        blank=True,
        help_text="ISO language code (en, pt, he, el, etc.)",
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Is this the primary name in this language?",
    )
    is_transliteration = models.BooleanField(
        default=False,
        help_text="Is this a transliteration?",
    )
    usage_note = models.CharField(
        max_length=200,
        blank=True,
        help_text="Context where this name is used",
    )

    class Meta:
        db_table = "entity_alias"
        verbose_name = "Entity Alias"
        verbose_name_plural = "Entity Aliases"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["language_code"]),
        ]

    def __str__(self):
        lang = self.language_code or "?"
        return f"{self.entity.canonical_id}: {self.name} ({lang})"


class EntityRole(models.Model):
    """
    A role/function an entity has at a specific time or context.

    This solves the problem of entities changing over time:
    - David: shepherd (youth) → warrior (Goliath) → king (2 Sam 5) → prophet (Psalms)
    - Jesus: pre-existent Logos → incarnate human → risen Lord → returning King
    - Peter: fisherman → disciple → apostle → church leader

    Each role can be linked to a biblical time period and verses.
    """

    entity = models.ForeignKey(
        CanonicalEntity,
        on_delete=models.CASCADE,
        related_name="roles",
    )

    # Role identification
    role_type = models.CharField(
        max_length=50,
        choices=RoleType.choices,
        help_text="Type of role (king, prophet, shepherd, etc.)",
    )
    role_label = models.CharField(
        max_length=200,
        help_text="Human-readable label (e.g., 'King of Israel')",
    )
    role_label_pt = models.CharField(
        max_length=200,
        blank=True,
        help_text="Label in Portuguese",
    )

    # Temporal context
    period_start = models.CharField(
        max_length=100,
        blank=True,
        help_text="Approximate start (e.g., '~1010 BC')",
    )
    period_end = models.CharField(
        max_length=100,
        blank=True,
        help_text="Approximate end",
    )
    period_label = models.CharField(
        max_length=200,
        blank=True,
        help_text="Human-readable period (e.g., 'Reign of David')",
    )
    period_label_pt = models.CharField(
        max_length=200,
        blank=True,
        help_text="Period label in Portuguese",
    )

    # Biblical context
    start_reference = models.CharField(
        max_length=50,
        blank=True,
        help_text="First verse reference for this role (e.g., '2 Sam 5:3')",
    )
    end_reference = models.CharField(
        max_length=50,
        blank=True,
        help_text="Last verse reference for this role",
    )

    # Ordering (for display)
    narrative_order = models.PositiveIntegerField(
        default=0,
        help_text="Order in the biblical narrative (0=earliest)",
    )

    # Description
    description = models.TextField(
        blank=True,
        help_text="Description of this role",
    )
    description_pt = models.TextField(
        blank=True,
        help_text="Description in Portuguese",
    )

    # Theological significance
    theological_significance = models.TextField(
        blank=True,
        help_text="Why this role is theologically important",
    )
    is_typological = models.BooleanField(
        default=False,
        help_text="Does this role prefigure Christ or NT concept?",
    )
    typology_explanation = models.TextField(
        blank=True,
        help_text="How this role prefigures Christ",
    )

    # AI enrichment
    ai_enriched = models.BooleanField(default=False)
    ai_insights = models.TextField(
        blank=True,
        help_text="AI-generated insights about this role",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "entity_role"
        verbose_name = "Entity Role"
        verbose_name_plural = "Entity Roles"
        ordering = ["entity", "narrative_order"]
        indexes = [
            models.Index(fields=["role_type"]),
            models.Index(fields=["entity", "narrative_order"]),
        ]

    def __str__(self):
        return f"{self.entity.canonical_id}: {self.role_label}"


class EntityTimeline(models.Model):
    """
    A significant event in an entity's timeline.

    This tracks biographical/historical events for entities:
    - Birth, death, calling, anointing
    - Key achievements, failures, turning points
    - For places: founding, destruction, rebuilding
    """

    class EventType(models.TextChoices):
        BIRTH = "birth", "Birth"
        DEATH = "death", "Death"
        CALLING = "calling", "Divine Calling"
        CONVERSION = "conversion", "Conversion"
        ANOINTING = "anointing", "Anointing"
        MARRIAGE = "marriage", "Marriage"
        CORONATION = "coronation", "Coronation"
        EXILE = "exile", "Exile"
        RETURN = "return", "Return"
        MIRACLE = "miracle", "Miracle"
        PROPHECY = "prophecy", "Prophecy Given/Received"
        BATTLE = "battle", "Battle"
        TREATY = "treaty", "Treaty/Covenant"
        SIN = "sin", "Sin/Failure"
        REPENTANCE = "repentance", "Repentance"
        BLESSING = "blessing", "Blessing Received"
        JUDGMENT = "judgment", "Judgment"
        FOUNDING = "founding", "Founding (place)"
        DESTRUCTION = "destruction", "Destruction (place)"
        REBUILDING = "rebuilding", "Rebuilding (place)"
        OTHER = "other", "Other"

    entity = models.ForeignKey(
        CanonicalEntity,
        on_delete=models.CASCADE,
        related_name="timeline_events",
    )

    # Event identification
    event_type = models.CharField(
        max_length=30,
        choices=EventType.choices,
    )
    title = models.CharField(
        max_length=200,
        help_text="Event title (e.g., 'David anointed by Samuel')",
    )
    title_pt = models.CharField(
        max_length=200,
        blank=True,
    )
    description = models.TextField(blank=True)
    description_pt = models.TextField(blank=True)

    # Temporal data
    date_approximate = models.CharField(
        max_length=100,
        blank=True,
        help_text="Approximate date (e.g., '~1000 BC')",
    )
    year_start = models.IntegerField(
        null=True,
        blank=True,
        help_text="Start year (negative for BC)",
    )
    year_end = models.IntegerField(
        null=True,
        blank=True,
        help_text="End year if event spans time",
    )

    # Biblical reference
    primary_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Primary verse reference",
    )
    additional_references = models.JSONField(
        default=list,
        blank=True,
        help_text="Additional verse references",
    )

    # Location (if applicable)
    location = models.ForeignKey(
        CanonicalEntity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events_at_location",
        help_text="Where this event occurred",
    )
    location_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Location name (if entity not available)",
    )

    # Ordering
    chronological_order = models.PositiveIntegerField(
        default=0,
        help_text="Order in timeline (0=earliest)",
    )

    # Theological significance
    theological_significance = models.TextField(blank=True)
    is_turning_point = models.BooleanField(
        default=False,
        help_text="Is this a major turning point?",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "entity_timeline"
        verbose_name = "Entity Timeline Event"
        verbose_name_plural = "Entity Timeline Events"
        ordering = ["entity", "chronological_order"]

    def __str__(self):
        return f"{self.entity.canonical_id}: {self.title}"


class EntityCategory(models.Model):
    """
    Categories/tags for organizing entities.

    Examples:
    - "Old Testament Characters"
    - "New Testament Characters"
    - "Prophets"
    - "Kings of Israel"
    - "Kings of Judah"
    - "Women of the Bible"
    - "Miracles"
    """

    slug = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    name_pt = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    description_pt = models.TextField(blank=True)

    # Hierarchy (optional)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )

    # Display
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=20, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "entity_category"
        verbose_name = "Entity Category"
        verbose_name_plural = "Entity Categories"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class EntityCategoryLink(models.Model):
    """Link between entity and category."""

    entity = models.ForeignKey(
        CanonicalEntity,
        on_delete=models.CASCADE,
        related_name="category_links",
    )
    category = models.ForeignKey(
        EntityCategory,
        on_delete=models.CASCADE,
        related_name="entity_links",
    )
    relevance = models.FloatField(
        default=1.0,
        help_text="How relevant is this category (0-1)",
    )

    class Meta:
        db_table = "entity_category_link"
        unique_together = ["entity", "category"]


class EntityVerseLink(models.Model):
    """
    Link between an entity and a verse with context.

    This tracks WHICH ROLE the entity had when mentioned in a verse.
    For example:
    - David in 1 Sam 16:11 → role: shepherd
    - David in 2 Sam 5:3 → role: king
    """

    entity = models.ForeignKey(
        CanonicalEntity,
        on_delete=models.CASCADE,
        related_name="verse_links",
    )
    verse = models.ForeignKey(
        "bible.Verse",
        on_delete=models.CASCADE,
        related_name="entity_links",
    )

    # Which role was active in this verse?
    role = models.ForeignKey(
        EntityRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verse_links",
        help_text="Which role the entity had in this verse",
    )

    # Mention type
    class MentionType(models.TextChoices):
        EXPLICIT = "explicit", "Explicitly Named"
        IMPLICIT = "implicit", "Implicitly Referenced"
        TITLE = "title", "By Title Only"
        PRONOUN = "pronoun", "Pronoun Reference"
        TYPOLOGICAL = "typological", "Typological Reference"

    mention_type = models.CharField(
        max_length=20,
        choices=MentionType.choices,
        default=MentionType.EXPLICIT,
    )

    # Context
    context_note = models.TextField(
        blank=True,
        help_text="How is the entity mentioned in this verse?",
    )
    context_note_pt = models.TextField(blank=True)

    # Relevance
    relevance = models.FloatField(
        default=1.0,
        help_text="How central is this entity to the verse (0-1)",
    )
    is_primary_subject = models.BooleanField(
        default=False,
        help_text="Is this entity the primary subject of the verse?",
    )

    # AI analysis
    ai_analysis = models.TextField(
        blank=True,
        help_text="AI analysis of the entity in this verse context",
    )

    # Match words — the actual words in the verse text that reference this entity
    # E.g., entity "Nudez" in Gen 3:7 → match_words: ["nus"]
    # E.g., entity "Eva" in Gen 3:6 → match_words: ["mulher"]
    match_words = models.JSONField(
        default=list,
        blank=True,
        help_text="Words in the verse text that reference this entity (for inline highlighting)",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "entity_verse_link"
        verbose_name = "Entity-Verse Link"
        verbose_name_plural = "Entity-Verse Links"
        unique_together = ["entity", "verse"]
        indexes = [
            models.Index(fields=["mention_type"]),
            models.Index(fields=["is_primary_subject"]),
        ]

    def __str__(self):
        return f"{self.entity.canonical_id} @ {self.verse}"


class EntityRelationship(models.Model):
    """
    Relationship between two entities.

    Examples:
    - David PARENT_OF Solomon
    - David SPOUSE_OF Bathsheba
    - David TYPE_OF Jesus (typological)
    - Jerusalem CAPITAL_OF Israel
    - Moses LEADER_OF Israel

    Relationships can be temporal (with start/end periods).
    """

    # Entities involved
    source = models.ForeignKey(
        CanonicalEntity,
        on_delete=models.CASCADE,
        related_name="outgoing_relationships",
    )
    target = models.ForeignKey(
        CanonicalEntity,
        on_delete=models.CASCADE,
        related_name="incoming_relationships",
    )

    # Relationship type
    relationship_type = models.CharField(
        max_length=50,
        choices=RelationshipType.choices,
    )

    # Description
    description = models.TextField(
        blank=True,
        help_text="Description of this relationship",
    )
    description_pt = models.TextField(blank=True)

    # Temporal context (optional)
    period_start = models.CharField(max_length=100, blank=True)
    period_end = models.CharField(max_length=100, blank=True)

    # Biblical reference
    primary_reference = models.CharField(max_length=100, blank=True)
    additional_references = models.JSONField(default=list, blank=True)

    # Strength/certainty
    class Certainty(models.TextChoices):
        CERTAIN = "certain", "Certain"
        PROBABLE = "probable", "Probable"
        POSSIBLE = "possible", "Possible"
        DEBATED = "debated", "Debated"

    certainty = models.CharField(
        max_length=20,
        choices=Certainty.choices,
        default=Certainty.CERTAIN,
    )

    # Theological significance
    is_typological = models.BooleanField(
        default=False,
        help_text="Is this a typological relationship?",
    )
    theological_note = models.TextField(blank=True)

    # Source tracking
    source_topic = models.CharField(
        max_length=100,
        blank=True,
        help_text="Original topic where relationship was found",
    )

    # AI enrichment
    ai_enriched = models.BooleanField(default=False)
    ai_analysis = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "entity_relationship"
        verbose_name = "Entity Relationship"
        verbose_name_plural = "Entity Relationships"
        indexes = [
            models.Index(fields=["relationship_type"]),
            models.Index(fields=["source", "target"]),
            models.Index(fields=["is_typological"]),
        ]

    def __str__(self):
        return f"{self.source.canonical_id} {self.relationship_type} {self.target.canonical_id}"

    @property
    def inverse_type(self):
        """Get the inverse relationship type."""
        inverses = {
            RelationshipType.PARENT_OF: RelationshipType.CHILD_OF,
            RelationshipType.CHILD_OF: RelationshipType.PARENT_OF,
            RelationshipType.ANCESTOR_OF: RelationshipType.DESCENDANT_OF,
            RelationshipType.DESCENDANT_OF: RelationshipType.ANCESTOR_OF,
            RelationshipType.TEACHER_OF: RelationshipType.DISCIPLE_OF,
            RelationshipType.DISCIPLE_OF: RelationshipType.TEACHER_OF,
            RelationshipType.MASTER_OF: RelationshipType.SERVANT_OF,
            RelationshipType.SERVANT_OF: RelationshipType.MASTER_OF,
            RelationshipType.SUCCESSOR_OF: RelationshipType.PREDECESSOR_OF,
            RelationshipType.PREDECESSOR_OF: RelationshipType.SUCCESSOR_OF,
            RelationshipType.TYPE_OF: RelationshipType.ANTITYPE_OF,
            RelationshipType.ANTITYPE_OF: RelationshipType.TYPE_OF,
        }
        return inverses.get(self.relationship_type, self.relationship_type)
