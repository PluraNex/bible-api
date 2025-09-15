"""RAG-related models: verse embeddings storage."""
from django.db import models
from pgvector.django import VectorField

from .verses import Verse


class VerseEmbedding(models.Model):
    """Embeddings for a verse in a specific version.

    Stores both recall (small) and rerank (large) vectors.
    """

    verse = models.OneToOneField(Verse, on_delete=models.CASCADE, related_name="embedding")
    version_code = models.CharField(max_length=40, db_index=True)
    model_name_small = models.CharField(max_length=80)
    dim_small = models.PositiveIntegerField()
    embedding_small = VectorField(dimensions=None, null=True)
    model_name_large = models.CharField(max_length=80, blank=True, default="")
    dim_large = models.PositiveIntegerField(null=True, blank=True)
    embedding_large = VectorField(dimensions=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "verse_embeddings"
        indexes = [
            models.Index(fields=["version_code"]),
        ]

    def __str__(self):
        return f"Embedding({self.verse_id}, {self.version_code})"
