from rest_framework import serializers

# --- Serializers para Views de AI ---


class ToolTestRequestSerializer(serializers.Serializer):
    """Serializer for testing an AI tool."""

    tool = serializers.CharField(help_text="Name of the tool to test.")
    params = serializers.JSONField(required=False, help_text="Parameters for the tool.")


class ToolTestResponseSerializer(serializers.Serializer):
    """Serializer for AI tool test response."""

    tool = serializers.CharField()
    status = serializers.CharField()
    message = serializers.CharField()


class AgentRunCreateRequestSerializer(serializers.Serializer):
    """Serializer for creating an AI agent run."""

    agent = serializers.CharField(help_text="Name of the agent to run.")
    input_payload = serializers.JSONField(help_text="Input data for the agent run.")


class AgentRunResponseSerializer(serializers.Serializer):
    """Serializer for AI agent run details and responses."""

    agent = serializers.CharField(required=False)
    run_id = serializers.IntegerField(required=False)
    status = serializers.CharField()
    message = serializers.CharField()


class AgentRunApproveRequestSerializer(serializers.Serializer):
    """Serializer for approving an AI agent run."""

    run_id = serializers.IntegerField(help_text="ID of the agent run to approve.")
    note = serializers.CharField(required=False, help_text="Optional note for approval.")


# --- Serializers para RAG ---


class RagSearchRequestSerializer(serializers.Serializer):
    """Serializer para validação de request de busca RAG."""

    q = serializers.CharField(
        min_length=3,
        max_length=500,
        help_text="Texto da consulta semântica (mínimo 3 caracteres)",
    )
    top_k = serializers.IntegerField(
        required=False,
        default=10,
        min_value=1,
        max_value=50,
        help_text="Número máximo de resultados (1-50, default: 10)",
    )
    version = serializers.CharField(
        required=False,
        help_text="Código da versão bíblica para filtrar (ex: 'ACF', 'NVI')",
    )
    versions = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Lista de códigos de versões para filtrar",
    )
    min_score = serializers.FloatField(
        required=False,
        min_value=0.0,
        max_value=1.0,
        help_text="Score mínimo de similaridade (0.0-1.0)",
    )


class RagHitSerializer(serializers.Serializer):
    """Serializer para um hit de busca RAG."""

    id = serializers.IntegerField(help_text="ID único do versículo")
    reference = serializers.CharField(help_text="Referência formatada (ex: 'João 3:16')")
    text = serializers.CharField(help_text="Texto do versículo")
    book_osis = serializers.CharField(help_text="Código OSIS do livro (ex: 'John')")
    book_name = serializers.CharField(help_text="Nome do livro localizado")
    chapter = serializers.IntegerField(help_text="Número do capítulo")
    verse = serializers.IntegerField(help_text="Número do versículo")
    version_code = serializers.CharField(
        required=False, allow_null=True, help_text="Código da versão bíblica"
    )
    score = serializers.FloatField(help_text="Score de similaridade (0-1)")


class RagTimingSerializer(serializers.Serializer):
    """Serializer para métricas de timing."""

    total_ms = serializers.FloatField(help_text="Tempo total em ms")
    embedding_ms = serializers.FloatField(
        required=False, help_text="Tempo de geração de embedding"
    )
    search_ms = serializers.FloatField(required=False, help_text="Tempo de busca vetorial")


class RagSearchResponseSerializer(serializers.Serializer):
    """Serializer para resposta de busca RAG."""

    hits = RagHitSerializer(many=True, help_text="Lista de versículos encontrados")
    total = serializers.IntegerField(help_text="Total de resultados retornados")
    timing = RagTimingSerializer(help_text="Métricas de performance")
    query = serializers.CharField(help_text="Query executada")


class RagSimilarRequestSerializer(serializers.Serializer):
    """Serializer para request de versículos similares."""

    verse_id = serializers.IntegerField(help_text="ID do versículo de referência")
    top_k = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=20,
        help_text="Número de versículos similares (1-20)",
    )
    exclude_same_chapter = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Excluir versículos do mesmo capítulo",
    )


class RagHealthComponentSerializer(serializers.Serializer):
    """Serializer para status de um componente."""

    status = serializers.ChoiceField(choices=["healthy", "unhealthy", "degraded"])
    error = serializers.CharField(required=False, allow_null=True)
    stats = serializers.DictField(required=False)
    book_count = serializers.IntegerField(required=False)


class RagHealthResponseSerializer(serializers.Serializer):
    """Serializer para resposta de health check."""

    status = serializers.ChoiceField(choices=["healthy", "unhealthy", "degraded"])
    components = serializers.DictField(
        child=RagHealthComponentSerializer(),
        help_text="Status de cada componente do sistema RAG",
    )


class RagStatsResponseSerializer(serializers.Serializer):
    """Serializer para estatísticas do cache."""

    cache_size = serializers.IntegerField(help_text="Número de embeddings em cache")
    hit_rate = serializers.FloatField(help_text="Taxa de acerto do cache (0-1)")
    memory_usage_mb = serializers.FloatField(
        required=False, help_text="Uso de memória em MB"
    )
