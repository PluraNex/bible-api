"""
Biblical Images domain — religious art linked to Scripture.

Models:
- Artist: painters/creators (~1,892 unique from WikiArt)
- BiblicalImage: paintings with metadata (16,914 records)
- ImageTag: AI-generated tags from Gemini Vision (2,999 records)
- ImageVerseLink: normalized image→verse mapping for fast by-verse queries
"""

from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils.text import slugify


class Artist(models.Model):
    """
    Art creator — painter, engraver, icon writer.

    Separate aggregate from BiblicalImage. Does NOT link to Person hub
    (artists are painters, not biblical/theological figures).

    Top artists: Gustave Doré (301), Rubens (235), Orthodox Icons (211).
    """

    name = models.CharField(max_length=300, unique=True, db_index=True)
    slug = models.SlugField(max_length=150, unique=True)
    birth_date = models.CharField(max_length=30, blank=True, help_text="Raw date string (e.g., '1574-05-30')")
    death_date = models.CharField(max_length=30, blank=True)
    nations = models.JSONField(default=list, blank=True, help_text='Artist nationalities (e.g., ["Italians"])')
    movements = models.JSONField(default=list, blank=True, help_text='Art movements (e.g., ["Baroque", "Renaissance"])')
    image_count = models.PositiveIntegerField(default=0, help_text="Denormalized count, updated on import")
    source = models.CharField(max_length=50, default="wikiart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "image_artist"
        ordering = ["name"]
        indexes = [
            GinIndex(fields=["movements"], name="artist_movements_gin"),
            GinIndex(fields=["nations"], name="artist_nations_gin"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:140]
            slug = base
            counter = 1
            while Artist.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class BiblicalImage(models.Model):
    """
    A religious painting/artwork with metadata from WikiArt.

    Aggregate root for the image-tag-verselink cluster.
    Images are external URLs (WikiArt CDN) — no file storage.
    """

    key = models.CharField(max_length=20, unique=True, db_index=True, help_text="WikiArt image key (e.g., '0000004')")
    title = models.CharField(max_length=500)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="images")
    completion_year = models.IntegerField(null=True, blank=True, db_index=True)
    styles = models.JSONField(default=list, blank=True, help_text='Art styles (e.g., ["Baroque"])')
    genres = models.JSONField(default=list, blank=True, help_text='Genres (e.g., ["religious painting"])')
    media = models.JSONField(default=list, blank=True, help_text='Media (e.g., ["oil", "canvas"])')
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    image_url = models.URLField(max_length=500, help_text="Full resolution image URL (WikiArt CDN)")
    thumbnail_url = models.URLField(max_length=500, blank=True, help_text="Thumbnail URL (~300px)")
    is_tagged = models.BooleanField(default=False, db_index=True, help_text="Whether AI tags exist")
    source = models.CharField(max_length=50, default="wikiart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "biblical_image"
        ordering = ["-completion_year"]
        indexes = [
            GinIndex(fields=["styles"], name="img_styles_gin"),
            GinIndex(fields=["genres"], name="img_genres_gin"),
            GinIndex(fields=["media"], name="img_media_gin"),
        ]

    def __str__(self):
        year = f" ({self.completion_year})" if self.completion_year else ""
        return f"{self.title}{year} — {self.artist.name}"


class ImageTag(models.Model):
    """
    AI-generated tags for a biblical image (Gemini Vision output).

    OneToOne to BiblicalImage — only 18% of images are tagged.
    Contains characters, events, symbols, descriptions, and scripture refs.
    """

    image = models.OneToOneField(BiblicalImage, on_delete=models.CASCADE, related_name="tag")
    characters = models.JSONField(default=list, blank=True, help_text='[{"name": "Moses", "type": "PERSON"}]')
    event = models.CharField(max_length=500, blank=True, help_text="Biblical event depicted")
    tag_list = models.JSONField(default=list, blank=True, help_text='Free-form tags (e.g., ["martyrdom", "saints"])')
    symbols = models.JSONField(default=list, blank=True, help_text='Symbols with meanings (e.g., ["halo — sanctity"])')
    description = models.TextField(blank=True, help_text="Visual description (~600 chars)")
    theological_description = models.TextField(blank=True, help_text="Deep theological analysis (~1000 chars)")
    scripture_refs = models.JSONField(
        default=list, blank=True,
        help_text='Domain truth: [{"ref": "REV.12.11", "relevance": "typological", "reason": "..."}]',
    )
    scene_type = models.CharField(max_length=50, blank=True, help_text="narrative, liturgical, symbolic")
    moods = models.JSONField(default=list, blank=True, help_text='Mood tags (e.g., ["anguish", "serenity"])')
    period = models.CharField(max_length=100, blank=True, help_text="Biblical period (Gospel, Pentateuch, etc.)")
    tagging_model = models.CharField(max_length=100, blank=True, help_text="AI model used (e.g., 'gemini-2.5-flash')")
    tagged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "image_tag"
        indexes = [
            GinIndex(fields=["tag_list"], name="imgtag_tags_gin"),
            GinIndex(fields=["characters"], name="imgtag_chars_gin"),
            GinIndex(fields=["moods"], name="imgtag_moods_gin"),
        ]

    def __str__(self):
        return f"Tags for {self.image.key}: {self.event or 'unclassified'}"


class ImageVerseLink(models.Model):
    """
    Normalized image→verse mapping for fast by-verse queries.

    Derived from ImageTag.scripture_refs at import time.
    Query pattern: WHERE book=X AND chapter=Y AND verse_start <= Z AND verse_end >= Z
    """

    image = models.ForeignKey(BiblicalImage, on_delete=models.CASCADE, related_name="verse_links")
    book = models.ForeignKey("bible.CanonicalBook", on_delete=models.CASCADE, related_name="image_links")
    chapter = models.PositiveIntegerField()
    verse_start = models.PositiveIntegerField()
    verse_end = models.PositiveIntegerField(help_text="Same as verse_start for single verse")
    relevance_type = models.CharField(
        max_length=30,
        help_text="primary, allusion, typological",
    )
    reason = models.TextField(blank=True, help_text="AI explanation for this link")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "image_verse_link"
        unique_together = ["image", "book", "chapter", "verse_start"]
        indexes = [
            models.Index(fields=["book", "chapter"], name="imgverse_book_ch_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(verse_end__gte=models.F("verse_start")),
                name="imgverse_end_gte_start",
            ),
        ]

    def __str__(self):
        vs = f"{self.verse_start}" if self.verse_start == self.verse_end else f"{self.verse_start}-{self.verse_end}"
        return f"{self.book.osis_code} {self.chapter}:{vs} → {self.image.key}"
