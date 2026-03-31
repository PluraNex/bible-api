"""
Query Expansion Cache Model

Armazena expansões de query geradas dinamicamente pelo LLM,
permitindo reutilização sem chamadas repetidas à API.

Versão: 1.0.0
Data: Nov 2025
"""

from django.contrib.postgres.fields import ArrayField
from django.db import models


class QueryExpansionCache(models.Model):
    """Cache de expansões de query geradas pelo LLM.

    Quando um usuário busca por um termo, o LLM gera sinônimos teológicos,
    variações morfológicas e conceitos relacionados. Essas expansões são
    armazenadas para reutilização futura.

    Exemplo:
        query_normalized: "perdão"
        theological_synonyms: ["remissão", "absolvição", "misericórdia"]
        morphological_variants: ["perdoar", "perdoado", "perdoando"]
        related_concepts: ["arrependimento", "graça", "reconciliação"]
    """

    # Query normalizada (lowercase, sem acentos extras)
    query_normalized = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Query normalizada (lowercase) para lookup rápido",
    )

    # Query original (como foi digitada)
    query_original = models.CharField(
        max_length=255,
        help_text="Query original como digitada pelo usuário",
    )

    # Expansões geradas pelo LLM
    theological_synonyms = ArrayField(
        models.CharField(max_length=100),
        default=list,
        help_text="Sinônimos teológicos: termos com significado similar no contexto bíblico",
    )

    morphological_variants = ArrayField(
        models.CharField(max_length=100),
        default=list,
        help_text="Variações morfológicas: diferentes formas da mesma palavra",
    )

    related_concepts = ArrayField(
        models.CharField(max_length=100),
        default=list,
        help_text="Conceitos relacionados: termos que frequentemente aparecem juntos",
    )

    # Metadados
    model_used = models.CharField(
        max_length=50,
        default="gpt-4o-mini",
        help_text="Modelo LLM usado para gerar a expansão",
    )

    prompt_version = models.CharField(
        max_length=20,
        default="v1",
        help_text="Versão do prompt usado para gerar a expansão",
    )

    confidence_score = models.FloatField(
        default=1.0,
        help_text="Score de confiança da expansão (0.0-1.0)",
    )

    # Estatísticas de uso
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text="Quantidade de vezes que esta expansão foi usada",
    )

    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Última vez que esta expansão foi usada",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "query_expansion_cache"
        verbose_name = "Query Expansion Cache"
        verbose_name_plural = "Query Expansion Cache"
        indexes = [
            models.Index(fields=["query_normalized"]),
            models.Index(fields=["usage_count"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        total_terms = (
            len(self.theological_synonyms or [])
            + len(self.morphological_variants or [])
            + len(self.related_concepts or [])
        )
        return f"QueryExpansion('{self.query_normalized}', {total_terms} terms)"

    def get_all_expansions(self) -> list[str]:
        """Retorna todas as expansões como uma lista única."""
        return (
            list(self.theological_synonyms or [])
            + list(self.morphological_variants or [])
            + list(self.related_concepts or [])
        )

    def to_tsquery(self) -> str:
        """Converte para formato tsquery do PostgreSQL."""
        terms = [self.query_normalized] + self.get_all_expansions()
        # Remove duplicatas mantendo ordem
        seen = set()
        unique = []
        for term in terms:
            if term.lower() not in seen:
                seen.add(term.lower())
                unique.append(term)
        return " | ".join(unique)

    def increment_usage(self):
        """Incrementa contador de uso."""
        from django.utils import timezone

        self.usage_count += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=["usage_count", "last_used_at"])
