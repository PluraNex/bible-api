"""
Serializers para Topic Review API.

Serializers para validação e correção de tópicos do Phase 0.
"""

from rest_framework import serializers


class TopicReviewListSerializer(serializers.Serializer):
    """Serializer para listagem de tópicos."""
    
    key = serializers.CharField(help_text="Chave do tópico (slug)")
    title = serializers.CharField(help_text="Título do tópico")
    sources = serializers.ListField(child=serializers.CharField(), help_text="Fontes")
    has_enrichment = serializers.BooleanField(help_text="Tem enriquecimento AI")
    has_entities = serializers.BooleanField(help_text="Tem entidades")
    has_themes = serializers.BooleanField(help_text="Tem temas")
    entity_count = serializers.IntegerField(help_text="Número de entidades")
    theme_count = serializers.IntegerField(help_text="Número de temas")


class TopicReviewDetailSerializer(serializers.Serializer):
    """Serializer para detalhes do tópico."""
    
    key = serializers.CharField()
    title = serializers.CharField()
    sources = serializers.ListField(child=serializers.CharField())
    references = serializers.ListField(child=serializers.DictField())
    ai_enrichment = serializers.DictField(allow_null=True)
    ai_entities = serializers.ListField(child=serializers.DictField())
    ai_themes_normalized = serializers.ListField(child=serializers.DictField())
    ai_symbols = serializers.ListField(child=serializers.DictField())
    entity_links = serializers.ListField(child=serializers.DictField())
    metadata = serializers.DictField()


class TopicEntitySerializer(serializers.Serializer):
    """Serializer para entidade de tópico."""
    
    index = serializers.IntegerField(help_text="Índice da entidade")
    source = serializers.ChoiceField(
        choices=["ai_entities", "entity_links"],
        help_text="Fonte da entidade"
    )
    name = serializers.CharField(help_text="Nome da entidade")
    type = serializers.CharField(help_text="Namespace/tipo da entidade")
    canonical_id = serializers.CharField(allow_null=True, help_text="ID canônico")
    context = serializers.CharField(allow_blank=True, help_text="Contexto")


class TopicThemeSerializer(serializers.Serializer):
    """Serializer para tema de tópico."""
    
    index = serializers.IntegerField(help_text="Índice do tema")
    theme = serializers.CharField(help_text="Nome do tema")
    domain = serializers.CharField(help_text="Domínio teológico")
    anchor_verses = serializers.ListField(child=serializers.CharField())
    keywords = serializers.ListField(child=serializers.CharField())
    relevance = serializers.FloatField(help_text="Relevância (0-1)")


class EntityCorrectionItemSerializer(serializers.Serializer):
    """Item de correção de entidade."""
    
    index = serializers.IntegerField(help_text="Índice da entidade")
    source = serializers.ChoiceField(
        choices=["ai_entities", "entity_links"],
        default="ai_entities"
    )
    field = serializers.CharField(help_text="Campo a corrigir")
    old_value = serializers.CharField(allow_blank=True)
    new_value = serializers.CharField()


class EntityCorrectionSerializer(serializers.Serializer):
    """Serializer para correção de entidades."""
    
    corrections = EntityCorrectionItemSerializer(many=True)


class ThemeCorrectionItemSerializer(serializers.Serializer):
    """Item de correção de tema."""
    
    index = serializers.IntegerField()
    field = serializers.CharField()
    old_value = serializers.CharField(allow_blank=True, required=False)
    new_value = serializers.CharField()


class ThemeCorrectionSerializer(serializers.Serializer):
    """Serializer para correção de temas."""
    
    corrections = ThemeCorrectionItemSerializer(many=True)


class ValidationIssueSerializer(serializers.Serializer):
    """Serializer para issue de validação."""
    
    severity = serializers.ChoiceField(choices=["error", "warning", "info"])
    field = serializers.CharField()
    message = serializers.CharField()
    current_value = serializers.CharField(allow_null=True, required=False)
    suggested_value = serializers.CharField(allow_null=True, required=False)


class ValidationResultSerializer(serializers.Serializer):
    """Serializer para resultado de validação."""
    
    topic_key = serializers.CharField()
    valid = serializers.BooleanField()
    score = serializers.FloatField()
    issues = ValidationIssueSerializer(many=True)
    metadata = serializers.DictField()


class BatchValidationRequestSerializer(serializers.Serializer):
    """Request para validação em batch."""
    
    topic_keys = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Lista de chaves de tópicos"
    )
    letter = serializers.CharField(
        max_length=1,
        required=False,
        help_text="Letra para filtrar (A-Z)"
    )
    limit = serializers.IntegerField(
        default=50,
        min_value=1,
        max_value=500,
        help_text="Limite de tópicos"
    )


class BatchValidationResponseSerializer(serializers.Serializer):
    """Response da validação em batch."""
    
    results = ValidationResultSerializer(many=True)
    report = serializers.DictField()
    total = serializers.IntegerField()


class CorrectionApprovalItemSerializer(serializers.Serializer):
    """Item de aprovação de correção."""
    
    field = serializers.CharField()
    approved = serializers.BooleanField()


class ApproveCorrectionsSerializer(serializers.Serializer):
    """Serializer para aprovação de correções."""
    
    corrections = CorrectionApprovalItemSerializer(many=True, required=False)
    auto_approve_high_confidence = serializers.BooleanField(default=False)
