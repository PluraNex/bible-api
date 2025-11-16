"""RAG-related models: verse embeddings storage."""
from django.db import models
from django.contrib.postgres.fields import ArrayField
import pgvector.django

from .verses import Verse


class VerseEmbedding(models.Model):
    """Embeddings for a verse in a specific version.

    Stores both recall (small) and rerank (large) vectors.
    Uses JSONField for universal compatibility across CI and production environments.
    """

    verse = models.OneToOneField(Verse, on_delete=models.CASCADE, related_name="embedding")
    version_code = models.CharField(max_length=40, db_index=True)
    model_name_small = models.CharField(max_length=80)
    dim_small = models.PositiveIntegerField()
    # Use JSONField for universal compatibility across CI and production
    embedding_small = models.JSONField(null=True, blank=True)
    model_name_large = models.CharField(max_length=80, blank=True, default="")
    dim_large = models.PositiveIntegerField(null=True, blank=True)
    embedding_large = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "verse_embeddings"
        indexes = [
            models.Index(fields=["version_code"]),
        ]

    def __str__(self):
        return f"Embedding({self.verse_id}, {self.version_code})"


class UnifiedVerseEmbedding(models.Model):
    """Unified embeddings for a canonical verse across multiple versions.

    Combines embeddings from multiple Bible versions (NAA, ARA, NVI) to create
    a more robust semantic representation that captures translation nuances.
    """

    canonical_verse_id = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Canonical reference like 'Gn.1.1', 'Mt.5.3'"
    )
    source_versions = ArrayField(
        models.CharField(max_length=10),
        help_text="List of version codes used in fusion: ['NAA', 'ARA', 'NVI']"
    )
    version_weights = models.JSONField(
        help_text="Weights used in fusion: {'NAA': 0.4, 'ARA': 0.35, 'NVI': 0.25}"
    )

    # Unified embeddings (fused from multiple versions)
    model_name_small = models.CharField(max_length=80, default="text-embedding-3-small")
    dim_small = models.PositiveIntegerField(default=1536)
    unified_embedding_small = pgvector.django.VectorField(
        dimensions=1536,
        null=True,
        blank=True,
        help_text="Unified small embedding for fast recall"
    )

    model_name_large = models.CharField(max_length=80, blank=True, default="text-embedding-3-large")
    dim_large = models.PositiveIntegerField(null=True, blank=True, default=3072)
    unified_embedding_large = pgvector.django.VectorField(
        dimensions=3072,
        null=True,
        blank=True,
        help_text="Unified large embedding for precise reranking"
    )

    # Fusion metadata
    fusion_strategy = models.CharField(
        max_length=30,
        default="weighted_average",
        help_text="Strategy used: weighted_average, max_pooling, concatenation"
    )
    quality_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Quality score of the unified embedding (0.0-1.0)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "unified_verse_embeddings"
        indexes = [
            models.Index(fields=["canonical_verse_id"]),
            models.Index(fields=["quality_score"]),
        ]

    def __str__(self):
        versions_str = ",".join(self.source_versions or [])
        return f"UnifiedEmbedding({self.canonical_verse_id}, [{versions_str}])"


class UnifiedThemeEmbedding(models.Model):
    """Unified embeddings for biblical themes derived from topics.

    Improves semantic similarity calculations in theme discovery and verse linking
    by combining embeddings from multiple sources for richer representations.
    """

    theme_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Unique theme identifier like 'graça_divina', 'amor_de_deus'"
    )
    theme_text = models.TextField(
        help_text="Human-readable theme text: 'Graça divina', 'Amor de Deus'"
    )
    source_topics = ArrayField(
        models.CharField(max_length=100),
        help_text="List of topic IDs that contributed to this theme: ['GOD', 'GRACE']"
    )

    # Unified embeddings (fused from multiple topic contexts)
    model_name_small = models.CharField(max_length=80, default="text-embedding-3-small")
    dim_small = models.PositiveIntegerField(default=1536)
    unified_embedding_small = pgvector.django.VectorField(
        dimensions=1536,
        null=True,
        blank=True,
        help_text="Unified small embedding for fast theme discovery"
    )

    model_name_large = models.CharField(max_length=80, default="text-embedding-3-large")
    dim_large = models.PositiveIntegerField(default=3072)
    unified_embedding_large = pgvector.django.VectorField(
        dimensions=3072,
        null=True,
        blank=True,
        help_text="Unified large embedding for precise semantic scoring"
    )

    # Fusion metadata
    fusion_strategy = models.CharField(
        max_length=30,
        default="weighted_average",
        help_text="Strategy used for combining topic embeddings"
    )
    quality_score = models.FloatField(
        default=0.0,
        help_text="Quality score of the unified theme embedding (0.0-1.0)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "unified_theme_embeddings"
        indexes = [
            models.Index(fields=["theme_id"]),
            models.Index(fields=["quality_score"]),
        ]

    def __str__(self):
        topic_count = len(self.source_topics or [])
        return f"UnifiedThemeEmbedding({self.theme_id}, {topic_count} topics)"
