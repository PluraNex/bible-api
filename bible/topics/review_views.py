"""
Topic Review Views - Endpoints para revisão do Phase 0 dataset.

Estes endpoints trabalham diretamente com os arquivos JSON do topics_v3,
permitindo que o agente AI valide e corrija dados antes da importação.

Endpoints:
- GET /topics/review/ → Listar tópicos disponíveis para revisão
- GET /topics/review/{key}/ → Detalhes de um tópico (do JSON)
- GET /topics/review/{key}/entities/ → Listar entidades do tópico
- PATCH /topics/review/{key}/entities/ → Corrigir entidades
- GET /topics/review/{key}/themes/ → Listar temas do tópico  
- PATCH /topics/review/{key}/themes/ → Corrigir temas
- POST /topics/review/{key}/validate/ → Validar tópico
- POST /topics/review/batch-validate/ → Validar múltiplos tópicos
- POST /topics/review/{key}/approve/ → Aprovar correções

Autor: Bible API Team
Data: Dezembro 2025
"""

import json
import logging
from pathlib import Path
from typing import Any

from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from bible.auth.permissions import HasAPIScopes
from common.exceptions import build_error_response
from common.openapi import get_error_responses
from common.pagination import StandardResultsSetPagination

from .review_serializers import (
    TopicReviewListSerializer,
    TopicReviewDetailSerializer,
    TopicEntitySerializer,
    TopicThemeSerializer,
    EntityCorrectionSerializer,
    ThemeCorrectionSerializer,
    ValidationResultSerializer,
    BatchValidationRequestSerializer,
    BatchValidationResponseSerializer,
)

logger = logging.getLogger(__name__)

# Caminho base para os arquivos JSON do Phase 0
TOPICS_V3_PATH = Path(__file__).parent.parent.parent / "scripts/topical_pipeline/data/topics_v3"


def get_topic_file_path(topic_key: str) -> Path | None:
    """Retorna o caminho do arquivo JSON de um tópico."""
    if not topic_key:
        return None
    
    first_letter = topic_key[0].upper()
    topic_file = TOPICS_V3_PATH / first_letter / f"{topic_key}.json"
    
    if topic_file.exists():
        return topic_file
    return None


def load_topic_json(topic_key: str) -> dict | None:
    """Carrega dados de um tópico do arquivo JSON."""
    file_path = get_topic_file_path(topic_key)
    if not file_path:
        return None
    
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load topic {topic_key}: {e}")
        return None


def save_topic_json(topic_key: str, data: dict) -> bool:
    """Salva dados de um tópico no arquivo JSON."""
    file_path = get_topic_file_path(topic_key)
    if not file_path:
        # Criar novo arquivo
        first_letter = topic_key[0].upper()
        topic_dir = TOPICS_V3_PATH / first_letter
        topic_dir.mkdir(parents=True, exist_ok=True)
        file_path = topic_dir / f"{topic_key}.json"
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved topic: {topic_key}")
        return True
    except Exception as e:
        logger.error(f"Failed to save topic {topic_key}: {e}")
        return False


def list_available_topics(letter: str | None = None, limit: int = 100) -> list[dict]:
    """Lista tópicos disponíveis no topics_v3."""
    topics = []
    
    if letter:
        letter_dirs = [TOPICS_V3_PATH / letter.upper()]
    else:
        letter_dirs = sorted(TOPICS_V3_PATH.glob("[A-Z]"))
    
    for letter_dir in letter_dirs:
        if not letter_dir.is_dir():
            continue
        
        for topic_file in sorted(letter_dir.glob("*.json")):
            if limit and len(topics) >= limit:
                break
            
            topic_key = topic_file.stem
            try:
                with open(topic_file, encoding="utf-8") as f:
                    data = json.load(f)
                
                topics.append({
                    "key": topic_key,
                    "title": data.get("title", topic_key),
                    "sources": data.get("sources", []),
                    "has_enrichment": "ai_enrichment" in data,
                    "has_entities": bool(data.get("ai_entities")),
                    "has_themes": bool(data.get("ai_themes_normalized")),
                    "entity_count": len(data.get("ai_entities", [])),
                    "theme_count": len(data.get("ai_themes_normalized", [])),
                })
            except Exception as e:
                logger.warning(f"Failed to read {topic_file}: {e}")
        
        if limit and len(topics) >= limit:
            break
    
    return topics


class TopicReviewListView(APIView):
    """Lista tópicos disponíveis para revisão no topics_v3."""
    
    permission_classes = [HasAPIScopes]
    required_scopes = ["ai-tools"]
    
    @extend_schema(
        summary="Listar tópicos para revisão",
        description="""
        Lista todos os tópicos disponíveis no dataset Phase 0 (topics_v3).
        
        Retorna informações básicas para cada tópico:
        - key: Chave do tópico (slug)
        - title: Título
        - has_enrichment: Se tem enriquecimento AI
        - entity_count: Número de entidades
        - theme_count: Número de temas
        """,
        tags=["topics-review"],
        parameters=[
            OpenApiParameter(
                name="letter",
                description="Filtrar por letra inicial (A-Z)",
                required=False,
            ),
            OpenApiParameter(
                name="limit",
                description="Limite de resultados (default: 100)",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="has_enrichment",
                description="Filtrar por status de enriquecimento (true/false)",
                required=False,
            ),
        ],
        responses={
            200: TopicReviewListSerializer(many=True),
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        letter = request.query_params.get("letter")
        limit = int(request.query_params.get("limit", 100))
        has_enrichment = request.query_params.get("has_enrichment")
        
        topics = list_available_topics(letter=letter, limit=limit * 2)  # Get more to filter
        
        # Filter by enrichment status
        if has_enrichment is not None:
            has_enrichment_bool = has_enrichment.lower() == "true"
            topics = [t for t in topics if t["has_enrichment"] == has_enrichment_bool]
        
        # Limit results
        topics = topics[:limit]
        
        return Response({
            "topics": topics,
            "total": len(topics),
            "letter": letter,
        })


class TopicReviewDetailView(APIView):
    """Detalhes completos de um tópico para revisão."""
    
    permission_classes = [HasAPIScopes]
    required_scopes = ["ai-tools"]
    
    @extend_schema(
        summary="Detalhes do tópico para revisão",
        description="Retorna todos os dados do tópico incluindo entidades, temas e enriquecimento AI.",
        tags=["topics-review"],
        responses={
            200: TopicReviewDetailSerializer,
            404: {"description": "Tópico não encontrado"},
            **get_error_responses(),
        },
    )
    def get(self, request, topic_key, *args, **kwargs):
        data = load_topic_json(topic_key)
        if not data:
            return build_error_response(
                f'Topic "{topic_key}" not found in topics_v3.',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
            )
        
        # Formatar resposta
        response_data = {
            "key": topic_key,
            "title": data.get("title", topic_key),
            "sources": data.get("sources", []),
            "references": data.get("references", []),
            "ai_enrichment": data.get("ai_enrichment"),
            "ai_entities": data.get("ai_entities", []),
            "ai_themes_normalized": data.get("ai_themes_normalized", []),
            "ai_symbols": data.get("ai_symbols", []),
            "entity_links": data.get("entity_links", []),
            "metadata": {
                "has_enrichment": "ai_enrichment" in data,
                "entity_count": len(data.get("ai_entities", [])),
                "theme_count": len(data.get("ai_themes_normalized", [])),
                "symbol_count": len(data.get("ai_symbols", [])),
            },
        }
        
        return Response(response_data)


class TopicEntitiesView(APIView):
    """Gerenciar entidades de um tópico."""
    
    permission_classes = [HasAPIScopes]
    required_scopes = ["ai-tools"]
    
    @extend_schema(
        summary="Listar entidades do tópico",
        description="Retorna todas as entidades extraídas pelo AI para este tópico.",
        tags=["topics-review"],
        responses={
            200: TopicEntitySerializer(many=True),
            404: {"description": "Tópico não encontrado"},
            **get_error_responses(),
        },
    )
    def get(self, request, topic_key, *args, **kwargs):
        data = load_topic_json(topic_key)
        if not data:
            return build_error_response(
                f'Topic "{topic_key}" not found.',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
            )
        
        entities = data.get("ai_entities", [])
        entity_links = data.get("entity_links", [])
        
        # Combinar e indexar
        all_entities = []
        for i, entity in enumerate(entities):
            all_entities.append({
                "index": i,
                "source": "ai_entities",
                "name": entity.get("name", ""),
                "type": entity.get("type", entity.get("namespace", "")),
                "canonical_id": entity.get("canonical_id"),
                "context": entity.get("context", ""),
            })
        
        for i, entity in enumerate(entity_links):
            all_entities.append({
                "index": i,
                "source": "entity_links",
                "name": entity.get("entity", entity.get("name", "")),
                "type": entity.get("namespace", entity.get("type", "")),
                "canonical_id": entity.get("canonical_id"),
                "context": entity.get("context", ""),
            })
        
        return Response({
            "topic_key": topic_key,
            "entities": all_entities,
            "total": len(all_entities),
        })
    
    @extend_schema(
        summary="Corrigir entidades do tópico",
        description="""
        Aplica correções às entidades do tópico.
        
        Exemplo de payload:
        ```json
        {
            "corrections": [
                {
                    "index": 0,
                    "source": "ai_entities",
                    "field": "type",
                    "old_value": "EVENT",
                    "new_value": "CONCEPT"
                }
            ]
        }
        ```
        """,
        tags=["topics-review"],
        request=EntityCorrectionSerializer,
        responses={
            200: {"description": "Correções aplicadas"},
            404: {"description": "Tópico não encontrado"},
            **get_error_responses(),
        },
    )
    def patch(self, request, topic_key, *args, **kwargs):
        data = load_topic_json(topic_key)
        if not data:
            return build_error_response(
                f'Topic "{topic_key}" not found.',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
            )
        
        corrections = request.data.get("corrections", [])
        applied = 0
        errors = []
        
        for correction in corrections:
            source = correction.get("source", "ai_entities")
            index = correction.get("index")
            field = correction.get("field")
            new_value = correction.get("new_value")
            
            try:
                if source == "ai_entities":
                    entities = data.get("ai_entities", [])
                    if 0 <= index < len(entities):
                        # Mapear field para o campo correto
                        if field == "type":
                            entities[index]["type"] = new_value
                        elif field == "namespace":
                            entities[index]["namespace"] = new_value
                        else:
                            entities[index][field] = new_value
                        applied += 1
                    else:
                        errors.append(f"Invalid index {index} for ai_entities")
                
                elif source == "entity_links":
                    entities = data.get("entity_links", [])
                    if 0 <= index < len(entities):
                        if field == "type":
                            entities[index]["namespace"] = new_value
                        else:
                            entities[index][field] = new_value
                        applied += 1
                    else:
                        errors.append(f"Invalid index {index} for entity_links")
                        
            except Exception as e:
                errors.append(f"Error applying correction {index}: {e}")
        
        # Salvar se houve correções
        if applied > 0:
            save_topic_json(topic_key, data)
        
        return Response({
            "topic_key": topic_key,
            "applied": applied,
            "errors": errors,
            "success": len(errors) == 0,
        })


class TopicThemesView(APIView):
    """Gerenciar temas de um tópico."""
    
    permission_classes = [HasAPIScopes]
    required_scopes = ["ai-tools"]
    
    @extend_schema(
        summary="Listar temas do tópico",
        description="Retorna todos os temas normalizados do tópico.",
        tags=["topics-review"],
        responses={
            200: TopicThemeSerializer(many=True),
            404: {"description": "Tópico não encontrado"},
            **get_error_responses(),
        },
    )
    def get(self, request, topic_key, *args, **kwargs):
        data = load_topic_json(topic_key)
        if not data:
            return build_error_response(
                f'Topic "{topic_key}" not found.',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
            )
        
        themes = data.get("ai_themes_normalized", [])
        
        # Indexar temas
        indexed_themes = []
        for i, theme in enumerate(themes):
            indexed_themes.append({
                "index": i,
                "theme": theme.get("theme", ""),
                "domain": theme.get("domain", ""),
                "anchor_verses": theme.get("anchor_verses", []),
                "keywords": theme.get("keywords", []),
                "relevance": theme.get("relevance", 0.0),
            })
        
        return Response({
            "topic_key": topic_key,
            "themes": indexed_themes,
            "total": len(indexed_themes),
        })
    
    @extend_schema(
        summary="Corrigir temas do tópico",
        description="""
        Aplica correções aos temas do tópico.
        
        Exemplo:
        ```json
        {
            "corrections": [
                {
                    "index": 0,
                    "field": "domain",
                    "old_value": "soteriology",
                    "new_value": "christology"
                }
            ]
        }
        ```
        """,
        tags=["topics-review"],
        request=ThemeCorrectionSerializer,
        responses={
            200: {"description": "Correções aplicadas"},
            404: {"description": "Tópico não encontrado"},
            **get_error_responses(),
        },
    )
    def patch(self, request, topic_key, *args, **kwargs):
        data = load_topic_json(topic_key)
        if not data:
            return build_error_response(
                f'Topic "{topic_key}" not found.',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
            )
        
        corrections = request.data.get("corrections", [])
        themes = data.get("ai_themes_normalized", [])
        applied = 0
        errors = []
        
        for correction in corrections:
            index = correction.get("index")
            field = correction.get("field")
            new_value = correction.get("new_value")
            
            try:
                if 0 <= index < len(themes):
                    themes[index][field] = new_value
                    applied += 1
                else:
                    errors.append(f"Invalid index {index}")
            except Exception as e:
                errors.append(f"Error applying correction {index}: {e}")
        
        # Salvar se houve correções
        if applied > 0:
            save_topic_json(topic_key, data)
        
        return Response({
            "topic_key": topic_key,
            "applied": applied,
            "errors": errors,
            "success": len(errors) == 0,
        })


class TopicValidateView(APIView):
    """Validar um tópico usando o TheologicalReviewTool."""
    
    permission_classes = [HasAPIScopes]
    required_scopes = ["ai-tools"]
    
    @extend_schema(
        summary="Validar tópico",
        description="""
        Executa validação teológica completa do tópico.
        
        Verifica:
        - Entidades (namespace correto)
        - Temas (domínio teológico)
        - Anchor verses (formato)
        - Símbolos e outline
        """,
        tags=["topics-review"],
        responses={
            200: ValidationResultSerializer,
            404: {"description": "Tópico não encontrado"},
            **get_error_responses(),
        },
    )
    def post(self, request, topic_key, *args, **kwargs):
        # Importar o tool de validação
        from bible.ai.agents.tools.theological_review_tool import TheologicalReviewTool
        
        tool = TheologicalReviewTool(topics_dir=TOPICS_V3_PATH)
        result = tool.validate_topic(topic_key)
        
        if not result.metadata:
            return build_error_response(
                f'Topic "{topic_key}" not found.',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
            )
        
        return Response(result.to_dict())


class TopicBatchValidateView(APIView):
    """Validar múltiplos tópicos em batch."""
    
    permission_classes = [HasAPIScopes]
    required_scopes = ["ai-tools"]
    
    @extend_schema(
        summary="Validação em batch",
        description="""
        Valida múltiplos tópicos e retorna relatório consolidado.
        
        Pode especificar:
        - topic_keys: Lista de tópicos específicos
        - letter: Validar todos de uma letra
        - limit: Limite de tópicos
        """,
        tags=["topics-review"],
        request=BatchValidationRequestSerializer,
        responses={
            200: BatchValidationResponseSerializer,
            **get_error_responses(),
        },
    )
    def post(self, request, *args, **kwargs):
        from bible.ai.agents.tools.theological_review_tool import TheologicalReviewTool
        
        topic_keys = request.data.get("topic_keys", [])
        letter = request.data.get("letter")
        limit = request.data.get("limit", 50)
        
        tool = TheologicalReviewTool(topics_dir=TOPICS_V3_PATH)
        
        if topic_keys:
            results = [tool.validate_topic(key) for key in topic_keys]
        elif letter:
            results = tool.validate_batch(letter=letter, limit=limit)
        else:
            return build_error_response(
                "Provide topic_keys or letter",
                "validation_error",
                status.HTTP_400_BAD_REQUEST,
                request=request,
            )
        
        # Gerar relatório
        report = tool.generate_report(results)
        
        return Response({
            "results": [r.to_dict() for r in results],
            "report": report,
            "total": len(results),
        })


class TopicApproveCorrectionsView(APIView):
    """Aprovar e aplicar correções geradas pela validação."""
    
    permission_classes = [HasAPIScopes]
    required_scopes = ["ai-tools", "write"]
    
    @extend_schema(
        summary="Aprovar correções",
        description="""
        Aprova e aplica correções geradas pela validação.
        
        Payload:
        ```json
        {
            "corrections": [
                {
                    "field": "entity:adoption",
                    "approved": true
                }
            ],
            "auto_approve_high_confidence": false
        }
        ```
        """,
        tags=["topics-review"],
        responses={
            200: {"description": "Correções aplicadas"},
            404: {"description": "Tópico não encontrado"},
            **get_error_responses(),
        },
    )
    def post(self, request, topic_key, *args, **kwargs):
        from bible.ai.agents.tools.theological_review_tool import TheologicalReviewTool
        
        tool = TheologicalReviewTool(topics_dir=TOPICS_V3_PATH)
        
        # Validar primeiro
        result = tool.validate_topic(topic_key)
        if not result.metadata:
            return build_error_response(
                f'Topic "{topic_key}" not found.',
                "not_found",
                status.HTTP_404_NOT_FOUND,
                request=request,
            )
        
        # Gerar propostas
        proposals = tool.generate_corrections(result)
        
        # Processar aprovações do request
        corrections = request.data.get("corrections", [])
        auto_approve = request.data.get("auto_approve_high_confidence", False)
        
        approved_fields = {c["field"] for c in corrections if c.get("approved")}
        
        for proposal in proposals:
            if proposal.issue.field in approved_fields:
                proposal.approved = True
            elif auto_approve and proposal.confidence >= 0.85:
                proposal.approved = True
        
        # Aplicar correções aprovadas
        result_stats = tool.apply_corrections(proposals, auto_approve=False)
        
        return Response({
            "topic_key": topic_key,
            "proposals_total": len(proposals),
            "applied": result_stats["applied"],
            "skipped": result_stats["skipped"],
            "pending": result_stats["pending"],
        })


class TopicReviewReportView(APIView):
    """Relatório geral de revisão do dataset."""
    
    permission_classes = [HasAPIScopes]
    required_scopes = ["ai-tools"]
    
    @extend_schema(
        summary="Relatório de revisão",
        description="Gera relatório consolidado de validação do dataset.",
        tags=["topics-review"],
        parameters=[
            OpenApiParameter(
                name="letter",
                description="Filtrar por letra",
                required=False,
            ),
            OpenApiParameter(
                name="limit",
                description="Limite de tópicos (default: 100)",
                required=False,
                type=int,
            ),
        ],
        responses={
            200: {"description": "Relatório de validação"},
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        from bible.ai.agents.tools.theological_review_tool import TheologicalReviewTool
        
        letter = request.query_params.get("letter")
        limit = int(request.query_params.get("limit", 100))
        
        tool = TheologicalReviewTool(topics_dir=TOPICS_V3_PATH)
        results = tool.validate_batch(letter=letter, limit=limit)
        report = tool.generate_report(results)
        
        return Response(report)
