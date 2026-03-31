"""
Query NLP Analysis Cache Model

Armazena análises NLP de queries para reutilização rápida,
evitando recálculos de tokenização, classificação e detecção de entidades.

Versão: 1.0.0
Data: Nov 2025
"""

from django.contrib.postgres.fields import ArrayField
from django.db import models


class QueryNLPCache(models.Model):
    """Cache de análises NLP de queries.

    Quando um usuário faz uma busca, o NLP Tool analisa a query:
    - Tokenização e remoção de stopwords
    - Classificação semântica (frase, conceito, entidade, etc.)
    - Detecção de entidades bíblicas via Gazetteer
    - Cálculo de estratégia de boost

    Esses resultados são cacheados para acesso instantâneo em buscas futuras.

    Exemplo:
        query_normalized: "paz na terra"
        semantic_type: "phrase"
        tokens_clean: ["paz", "terra"]
        stopwords_removed: ["na"]
        entities: [{"text": "...", "type": "...", "boost": ...}]
        boost_strategy: {"alpha": 0.6, "expand": false, ...}
        tsquery_optimized: "(paz <2> terra)"
    """

    # Query normalizada (lowercase, sem acentos)
    query_normalized = models.CharField(
        max_length=500,
        unique=True,
        db_index=True,
        help_text="Query normalizada para lookup rápido",
    )

    # Query original
    query_original = models.CharField(
        max_length=500,
        help_text="Query original como digitada pelo usuário",
    )

    # Classificação semântica
    semantic_type = models.CharField(
        max_length=50,
        choices=[
            ("phrase", "Frase exata"),
            ("concept", "Conceito abstrato"),
            ("reference", "Referência bíblica"),
            ("entity", "Entidade (pessoa, lugar, etc.)"),
            ("keyword", "Palavra-chave única"),
            ("question", "Pergunta"),
        ],
        help_text="Tipo semântico da query",
    )

    semantic_confidence = models.FloatField(
        default=0.0,
        help_text="Confiança na classificação semântica (0.0-1.0)",
    )

    # Tokens processados
    tokens_raw = ArrayField(
        models.CharField(max_length=100),
        default=list,
        help_text="Tokens brutos da query",
    )

    tokens_clean = ArrayField(
        models.CharField(max_length=100),
        default=list,
        help_text="Tokens após remoção de stopwords",
    )

    tokens_lemma = ArrayField(
        models.CharField(max_length=100),
        default=list,
        help_text="Lemas dos tokens",
    )

    stopwords_removed = ArrayField(
        models.CharField(max_length=50),
        default=list,
        help_text="Stopwords removidas da query",
    )

    # Entidades detectadas (JSON)
    entities = models.JSONField(
        default=list,
        help_text="Entidades detectadas via Gazetteer",
    )

    # Estratégia de boost (JSON)
    boost_strategy = models.JSONField(
        default=dict,
        help_text="Estratégia de boost calculada (alpha, expand, entity_boost, etc.)",
    )

    # TSQuery otimizado
    tsquery_optimized = models.CharField(
        max_length=1000,
        blank=True,
        default="",
        help_text="TSQuery otimizado com distância dinâmica",
    )

    # N-grams (para análise futura)
    bigrams = ArrayField(
        models.CharField(max_length=100),
        default=list,
        help_text="Bigramas da query",
    )

    trigrams = ArrayField(
        models.CharField(max_length=150),
        default=list,
        help_text="Trigramas da query",
    )

    # Flags
    is_known_phrase = models.BooleanField(
        default=False,
        help_text="Se a query é uma frase conhecida/comum",
    )

    # Estatísticas de uso
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text="Quantidade de vezes que esta análise foi usada",
    )

    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Última vez que esta análise foi usada",
    )

    # Processing time (para métricas)
    processing_time_ms = models.FloatField(
        default=0.0,
        help_text="Tempo de processamento original em ms",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "query_nlp_cache"
        verbose_name = "Query NLP Cache"
        verbose_name_plural = "Query NLP Cache"
        indexes = [
            models.Index(fields=["query_normalized"]),
            models.Index(fields=["semantic_type"]),
            models.Index(fields=["usage_count"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        entity_count = len(self.entities) if self.entities else 0
        return f"NLPCache('{self.query_normalized}', type={self.semantic_type}, entities={entity_count})"

    def increment_usage(self):
        """Incrementa contador de uso."""
        from django.utils import timezone

        self.usage_count += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=["usage_count", "last_used_at"])

    def to_nlp_analysis(self):
        """Converte para NLPAnalysis dataclass."""
        from bible.ai.agents.tools.nlp_query_tool import NLPAnalysis, SemanticType

        return NLPAnalysis(
            query_original=self.query_original,
            query_normalized=self.query_normalized,
            tokens_raw=list(self.tokens_raw),
            tokens_clean=list(self.tokens_clean),
            tokens_lemma=list(self.tokens_lemma),
            stopwords_removed=list(self.stopwords_removed),
            pos_tags={},  # Não cacheamos POS tags por espaço
            entities=list(self.entities),
            semantic_type=SemanticType(self.semantic_type),
            semantic_confidence=self.semantic_confidence,
            bigrams=list(self.bigrams),
            trigrams=list(self.trigrams),
            is_known_phrase=self.is_known_phrase,
            boost_strategy=dict(self.boost_strategy),
            from_cache=True,
            processing_time_ms=0.0,  # Instantâneo do cache
        )

    @classmethod
    def from_nlp_analysis(cls, analysis) -> "QueryNLPCache":
        """Cria instância a partir de NLPAnalysis."""
        return cls(
            query_normalized=analysis.query_normalized,
            query_original=analysis.query_original,
            semantic_type=analysis.semantic_type.value,
            semantic_confidence=analysis.semantic_confidence,
            tokens_raw=analysis.tokens_raw,
            tokens_clean=analysis.tokens_clean,
            tokens_lemma=analysis.tokens_lemma,
            stopwords_removed=analysis.stopwords_removed,
            entities=analysis.entities,
            boost_strategy=analysis.boost_strategy,
            tsquery_optimized=analysis.to_tsquery(),
            bigrams=analysis.bigrams,
            trigrams=analysis.trigrams,
            is_known_phrase=analysis.is_known_phrase,
            processing_time_ms=analysis.processing_time_ms,
        )
