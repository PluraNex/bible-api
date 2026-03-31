"""
AI Agent and Tool views for Bible API.
Skeleton implementation with auth and schema annotations.
"""

import json
import time

from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.observability.metrics import LATENCY, REQUESTS
from common.openapi import get_error_responses

from . import retrieval as rag_svc
from .serializers import (
    AgentRunApproveRequestSerializer,
    AgentRunCreateRequestSerializer,
    AgentRunResponseSerializer,
    ToolTestRequestSerializer,
    ToolTestResponseSerializer,
)


class AgentListView(generics.ListAPIView):
    """List available AI agents."""

    @extend_schema(
        summary="List AI agents",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "agents": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "enabled": {"type": "boolean"},
                                "status": {"type": "string"},
                            },
                        },
                    }
                },
            },
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        agents = [
            {
                "name": "themer",
                "description": "AI agent for theme analysis and tagging",
                "enabled": False,
                "status": "not_implemented",
            },
            {
                "name": "xrefs-suggester",
                "description": "AI agent for cross-reference suggestions",
                "enabled": False,
                "status": "not_implemented",
            },
        ]

        return Response(
            {
                "pagination": {
                    "count": len(agents),
                    "num_pages": 1,
                    "current_page": 1,
                    "page_size": 20,
                    "next": None,
                    "previous": None,
                },
                "results": agents,
            },
            status=status.HTTP_200_OK,
        )


class ToolListView(generics.ListAPIView):
    """List available AI tools."""

    @extend_schema(
        summary="List AI tools",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "tools": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "requires_approval": {"type": "boolean"},
                                "status": {"type": "string"},
                            },
                        },
                    }
                },
            },
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        tools = [
            {
                "name": "theological_review",
                "description": "Validate and correct theological data (entities, themes, anchors)",
                "requires_approval": True,
                "status": "active",
                "functions": [
                    "validate_topic",
                    "generate_corrections",
                    "approve_correction",
                    "apply_corrections",
                    "validate_batch",
                    "get_report",
                ],
            },
            {
                "name": "nlp_query",
                "description": "NLP analysis for search queries",
                "requires_approval": False,
                "status": "active",
            },
            {
                "name": "query_expansion",
                "description": "Expand search queries with synonyms",
                "requires_approval": False,
                "status": "active",
            },
            {
                "name": "apply_theme_tags",
                "description": "Apply theme tags to verses",
                "requires_approval": True,
                "status": "not_implemented",
            },
            {
                "name": "suggest_cross_references",
                "description": "Suggest cross references for verses",
                "requires_approval": True,
                "status": "not_implemented",
            },
        ]

        return Response(
            {
                "pagination": {
                    "count": len(tools),
                    "num_pages": 1,
                    "current_page": 1,
                    "page_size": 20,
                    "next": None,
                    "previous": None,
                },
                "results": tools,
            },
            status=status.HTTP_200_OK,
        )


class ToolTestView(APIView):
    """Test an AI tool (skeleton)."""

    @extend_schema(
        summary="Test an AI tool",
        request=ToolTestRequestSerializer,
        responses={
            200: ToolTestResponseSerializer,
            501: {
                "type": "object",
                "properties": {
                    "tool": {"type": "string"},
                    "status": {"type": "string"},
                    "message": {"type": "string"},
                },
            },
            **get_error_responses(),
        },
    )
    def post(self, request, tool, *args, **kwargs):
        return Response(
            {
                "tool": tool,
                "status": "test_not_implemented",
                "message": "AI tools testing not implemented in T-001",
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class AgentRunCreateView(APIView):
    """Create a new agent run (skeleton)."""

    @extend_schema(
        summary="Create agent run",
        request=AgentRunCreateRequestSerializer,
        responses={
            201: AgentRunResponseSerializer,
            501: {
                "type": "object",
                "properties": {
                    "agent": {"type": "string"},
                    "status": {"type": "string"},
                    "message": {"type": "string"},
                },
            },
            **get_error_responses(),
        },
    )
    def post(self, request, name, *args, **kwargs):
        return Response(
            {
                "agent": name,
                "status": "agent_runs_not_implemented",
                "message": "AI agent runs not implemented in T-001",
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class AgentRunDetailView(APIView):
    """Get details of an agent run (skeleton)."""

    @extend_schema(
        summary="Get agent run details",
        responses={
            200: AgentRunResponseSerializer,
            501: {
                "type": "object",
                "properties": {
                    "run_id": {"type": "integer"},
                    "status": {"type": "string"},
                    "message": {"type": "string"},
                },
            },
            **get_error_responses(),
        },
    )
    def get(self, request, run_id, *args, **kwargs):
        return Response(
            {
                "run_id": run_id,
                "status": "agent_runs_not_implemented",
                "message": "AI agent runs not implemented in T-001",
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class AgentRunApproveView(APIView):
    """Approve an agent run."""

    @extend_schema(
        summary="Approve agent run",
        request=AgentRunApproveRequestSerializer,
        responses={
            200: AgentRunResponseSerializer,
            501: {
                "type": "object",
                "properties": {
                    "run_id": {"type": "integer"},
                    "status": {"type": "string"},
                    "message": {"type": "string"},
                },
            },
            **get_error_responses(),
        },
    )
    def post(self, request, run_id, *args, **kwargs):
        return Response(
            {
                "run_id": run_id,
                "status": "approval_not_implemented",
                "message": "AI agent run approval not implemented in T-001",
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class AgentRunCancelView(APIView):
    """Cancel an agent run."""

    @extend_schema(
        summary="Cancel agent run",
        responses={
            200: AgentRunResponseSerializer,
            501: {
                "type": "object",
                "properties": {
                    "run_id": {"type": "integer"},
                    "status": {"type": "string"},
                    "message": {"type": "string"},
                },
            },
            **get_error_responses(),
        },
    )
    def delete(self, request, run_id, *args, **kwargs):
        return Response(
            {
                "run_id": run_id,
                "status": "cancellation_not_implemented",
                "message": "AI agent run cancellation not implemented in T-001",
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class RagRetrieveView(APIView):
    """RAG retrieve endpoint: GET /api/v1/ai/rag/retrieve"""

    @extend_schema(
        summary="RAG retrieve — top‑K versos",
        tags=["rag"],
        parameters=[
            OpenApiParameter(
                name="q",
                location=OpenApiParameter.QUERY,
                required=False,
                description="Texto da consulta (use se não enviar 'vector')",
                type=str,
                examples=[OpenApiExample("query_pt", value="amor de Deus")],
            ),
            OpenApiParameter(
                name="vector",
                location=OpenApiParameter.QUERY,
                required=False,
                description="Vetor JSON (lista de floats) — evita chamada ao OpenAI",
                type=str,
                examples=[OpenApiExample("vector_example", value="[0.01, -0.2, 0.3, ...]")],
            ),
            OpenApiParameter(
                name="versions",
                location=OpenApiParameter.QUERY,
                required=False,
                description="Códigos separados por vírgula (ex.: PT_NAA,EN_KJV). Se ausente, usa RAG_ALLOWED_VERSIONS do ambiente.",
                type=str,
            ),
            OpenApiParameter(name="book_id", location=OpenApiParameter.QUERY, required=False, type=int),
            OpenApiParameter(name="chapter", location=OpenApiParameter.QUERY, required=False, type=int),
            OpenApiParameter(name="chapter_end", location=OpenApiParameter.QUERY, required=False, type=int),
            OpenApiParameter(
                name="top_k", location=OpenApiParameter.QUERY, required=False, type=int, description="Padrão 10"
            ),
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "hits": {"type": "array"},
                    "timing": {"type": "object"},
                },
            },
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        q = (request.query_params.get("q") or "").strip()
        versions_csv = (request.query_params.get("versions") or "").strip()
        versions = [v.strip() for v in versions_csv.split(",") if v.strip()] or None
        book_id = request.query_params.get("book_id")
        chapter = request.query_params.get("chapter")
        chapter_end = request.query_params.get("chapter_end")
        top_k = int(request.query_params.get("top_k") or 10)

        # Optional: accept vector as JSON list
        vector = None
        if "vector" in request.query_params:
            try:
                import json

                vector = json.loads(request.query_params.get("vector"))
                if not isinstance(vector, list):
                    return Response({"detail": "'vector' deve ser lista de floats"}, status=400)
            except (json.JSONDecodeError, TypeError, ValueError):
                return Response({"detail": "'vector' inválido (JSON)"}, status=400)

        # Parse ints
        book_id = int(book_id) if book_id is not None else None
        chapter = int(chapter) if chapter is not None else None
        chapter_end = int(chapter_end) if chapter_end is not None else None

        # Validar presença de q ou vector antes de chamar o serviço
        if not q and vector is None:
            return Response({"detail": "Informe 'q' ou 'vector'."}, status=400)

        view_name = self.__class__.__name__
        try:
            t0 = time.time()
            result = rag_svc.retrieve(
                query=q if vector is None else None,
                vector=vector,
                top_k=top_k,
                versions=versions,
                book_id=book_id,
                chapter=chapter,
                chapter_end=chapter_end,
            )
            dur = time.time() - t0
            REQUESTS.labels(
                method="GET", status="200", view=view_name, lang=getattr(request, "lang_code", "-"), version="-"
            ).inc()
            LATENCY.labels(view=view_name, lang=getattr(request, "lang_code", "-"), version="-").observe(dur)
            return Response(result, status=200)
        except ValueError as e:
            REQUESTS.labels(
                method="GET", status="400", view=view_name, lang=getattr(request, "lang_code", "-"), version="-"
            ).inc()
            return Response({"detail": str(e)}, status=400)
        except Exception as e:
            REQUESTS.labels(
                method="GET", status="500", view=view_name, lang=getattr(request, "lang_code", "-"), version="-"
            ).inc()
            return Response({"detail": str(e)}, status=500)


# === RAG Views Refatoradas ===

from . import services as rag_service
from .serializers import (
    RagSearchRequestSerializer,
    RagSearchResponseSerializer,
    RagHitSerializer,
    RagSimilarRequestSerializer,
    RagHealthResponseSerializer,
    RagStatsResponseSerializer,
)


class RagSearchView(APIView):
    """
    Busca semântica (RAG) de versículos.
    
    GET /api/v1/ai/rag/search/?q=amor+divino&top_k=10
    
    Utiliza embeddings vetoriais para encontrar versículos
    semanticamente relacionados à query, mesmo que não
    contenham as palavras exatas.
    """

    @extend_schema(
        summary="Busca semântica de versículos",
        description="""
        Executa busca semântica usando RAG (Retrieval Augmented Generation).
        
        Diferente da busca textual, encontra versículos por significado,
        não apenas por palavras-chave. Ideal para:
        - Buscas conceituais ("amor divino", "salvação pela fé")
        - Encontrar passagens relacionadas tematicamente
        - Descobrir conexões não óbvias entre textos
        
        **Exemplos de queries:**
        - "amor de Deus pela humanidade"
        - "confiança em tempos difíceis"  
        - "promessas de Deus para os fiéis"
        """,
        tags=["rag"],
        parameters=[
            OpenApiParameter(
                name="q",
                location=OpenApiParameter.QUERY,
                required=True,
                description="Texto da consulta semântica (mínimo 3 caracteres)",
                type=str,
                examples=[
                    OpenApiExample("amor", value="amor de Deus"),
                    OpenApiExample("salvação", value="salvação pela graça"),
                    OpenApiExample("confiança", value="confiar no Senhor"),
                ],
            ),
            OpenApiParameter(
                name="top_k",
                location=OpenApiParameter.QUERY,
                required=False,
                description="Número máximo de resultados (1-50, default: 10)",
                type=int,
            ),
            OpenApiParameter(
                name="version",
                location=OpenApiParameter.QUERY,
                required=False,
                description="Código da versão bíblica (ex: 'ACF', 'NVI')",
                type=str,
            ),
            OpenApiParameter(
                name="min_score",
                location=OpenApiParameter.QUERY,
                required=False,
                description="Score mínimo de similaridade (0.0-1.0)",
                type=float,
            ),
        ],
        responses={
            200: RagSearchResponseSerializer,
            400: {"description": "Parâmetros inválidos"},
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        view_name = self.__class__.__name__
        lang = getattr(request, "lang_code", "-")
        
        # Validar parâmetros
        q = (request.query_params.get("q") or "").strip()
        if not q:
            return Response(
                {"detail": "Parâmetro 'q' é obrigatório", "code": "validation_error"},
                status=400,
            )
        
        if len(q) < 3:
            return Response(
                {"detail": "Query deve ter no mínimo 3 caracteres", "code": "validation_error"},
                status=400,
            )
        
        # Extrair parâmetros
        try:
            top_k = int(request.query_params.get("top_k") or 10)
            top_k = max(1, min(top_k, 50))
        except ValueError:
            top_k = 10
        
        version = request.query_params.get("version")
        versions = [version] if version else None
        
        min_score = None
        if request.query_params.get("min_score"):
            try:
                min_score = float(request.query_params.get("min_score"))
                min_score = max(0.0, min(min_score, 1.0))
            except ValueError:
                pass
        
        # Executar busca
        try:
            t0 = time.time()
            result = rag_service.search(
                query=q,
                top_k=top_k,
                versions=versions,
                min_score=min_score,
            )
            dur = time.time() - t0
            
            # Métricas
            REQUESTS.labels(method="GET", status="200", view=view_name, lang=lang, version=version or "-").inc()
            LATENCY.labels(view=view_name, lang=lang, version=version or "-").observe(dur)
            
            # Resposta
            response_data = {
                "hits": result.hits,
                "total": result.total,
                "timing": result.timing,
                "query": result.query,
            }
            
            return Response(response_data, status=200)
            
        except ValueError as e:
            return Response(
                {"detail": str(e), "code": "validation_error"},
                status=400,
            )
        except Exception as e:
            REQUESTS.labels(method="GET", status="500", view=view_name, lang=lang, version="-").inc()
            return Response(
                {"detail": f"Erro interno: {str(e)}", "code": "internal_error"},
                status=500,
            )


class RagSimilarView(APIView):
    """
    Encontra versículos semanticamente similares a um versículo específico.
    
    GET /api/v1/ai/rag/similar/?verse_id=12345&top_k=5
    
    Útil para sugestões de referências cruzadas baseadas em semântica.
    """

    @extend_schema(
        summary="Versículos similares",
        description="""
        Encontra versículos semanticamente similares a um versículo de referência.
        
        Útil para:
        - Descobrir passagens paralelas
        - Sugestões de referências cruzadas
        - Estudos comparativos de temas
        """,
        tags=["rag"],
        parameters=[
            OpenApiParameter(
                name="verse_id",
                location=OpenApiParameter.QUERY,
                required=True,
                description="ID do versículo de referência",
                type=int,
            ),
            OpenApiParameter(
                name="top_k",
                location=OpenApiParameter.QUERY,
                required=False,
                description="Número de resultados (1-20, default: 5)",
                type=int,
            ),
            OpenApiParameter(
                name="exclude_same_chapter",
                location=OpenApiParameter.QUERY,
                required=False,
                description="Excluir versículos do mesmo capítulo (default: true)",
                type=bool,
            ),
        ],
        responses={
            200: RagSearchResponseSerializer,
            400: {"description": "Parâmetros inválidos"},
            404: {"description": "Versículo não encontrado"},
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        view_name = self.__class__.__name__
        lang = getattr(request, "lang_code", "-")
        
        # Validar verse_id
        verse_id_str = request.query_params.get("verse_id")
        if not verse_id_str:
            return Response(
                {"detail": "Parâmetro 'verse_id' é obrigatório", "code": "validation_error"},
                status=400,
            )
        
        try:
            verse_id = int(verse_id_str)
        except ValueError:
            return Response(
                {"detail": "'verse_id' deve ser um número inteiro", "code": "validation_error"},
                status=400,
            )
        
        # Extrair parâmetros opcionais
        try:
            top_k = int(request.query_params.get("top_k") or 5)
            top_k = max(1, min(top_k, 20))
        except ValueError:
            top_k = 5
        
        exclude_same_chapter = request.query_params.get("exclude_same_chapter", "true").lower() != "false"
        
        # Executar busca
        try:
            t0 = time.time()
            result = rag_service.get_similar_verses(
                verse_id=verse_id,
                top_k=top_k,
                exclude_same_chapter=exclude_same_chapter,
            )
            dur = time.time() - t0
            
            REQUESTS.labels(method="GET", status="200", view=view_name, lang=lang, version="-").inc()
            LATENCY.labels(view=view_name, lang=lang, version="-").observe(dur)
            
            return Response({
                "hits": result.hits,
                "total": result.total,
                "timing": result.timing,
                "reference_verse_id": verse_id,
            }, status=200)
            
        except ValueError as e:
            error_msg = str(e)
            if "não encontrado" in error_msg:
                return Response(
                    {"detail": error_msg, "code": "not_found"},
                    status=404,
                )
            return Response(
                {"detail": error_msg, "code": "validation_error"},
                status=400,
            )
        except Exception as e:
            REQUESTS.labels(method="GET", status="500", view=view_name, lang=lang, version="-").inc()
            return Response(
                {"detail": f"Erro interno: {str(e)}", "code": "internal_error"},
                status=500,
            )


class RagHealthView(APIView):
    """
    Health check do sistema RAG.
    
    GET /api/v1/ai/rag/health/
    
    Verifica o status de todos os componentes do sistema RAG.
    """

    @extend_schema(
        summary="Health check do RAG",
        description="Verifica a saúde de todos os componentes do sistema RAG",
        tags=["rag"],
        responses={
            200: RagHealthResponseSerializer,
            503: {"description": "Sistema não saudável"},
        },
    )
    def get(self, request, *args, **kwargs):
        try:
            health = rag_service.health_check()
            
            status_code = 200
            if health["status"] == "unhealthy":
                status_code = 503
            
            return Response(health, status=status_code)
            
        except Exception as e:
            return Response({
                "status": "unhealthy",
                "error": str(e),
                "components": {},
            }, status=503)


class RagStatsView(APIView):
    """
    Estatísticas do cache de embeddings.
    
    GET /api/v1/ai/rag/stats/
    """

    @extend_schema(
        summary="Estatísticas do cache RAG",
        description="Retorna métricas de performance do cache de embeddings",
        tags=["rag"],
        responses={
            200: RagStatsResponseSerializer,
        },
    )
    def get(self, request, *args, **kwargs):
        try:
            stats = rag_service.get_cache_stats()
            return Response(stats, status=200)
        except Exception as e:
            return Response(
                {"detail": f"Erro ao obter estatísticas: {str(e)}"},
                status=500,
            )


class RagHybridSearchView(APIView):
    """
    Busca híbrida: combina BM25 (lexical) + Vetorial (semântica).
    
    GET /api/v1/ai/rag/hybrid/?q=ódio&alpha=0.5&expand=true
    
    A busca híbrida usa Reciprocal Rank Fusion (RRF) para combinar:
    - BM25: Excelente para termos exatos (ex: "ódio", "Melquisedeque")
    - Vetorial: Excelente para conceitos (ex: "amor divino", "salvação")
    - Query Expansion: Expande termos com sinônimos teológicos
    - Two-Stage Reranking: Reordena usando embeddings de alta dimensão
    - MMR Diversification: Maximiza diversidade dos resultados
    
    Embedding Sources:
    - verse: 529K embeddings (PT+EN, 17 versões) - mais abrangente
    - unified: 31K embeddings (apenas PT, 8 versões) - 11x mais rápido
    """

    @extend_schema(
        summary="Busca híbrida de versículos",
        description="""
        Combina busca lexical (BM25) com semântica (vetorial) usando RRF fusion.
        
        **Pipeline Completo:**
        1. Query Expansion (opcional) - Sinônimos teológicos
        2. BM25 Search - Matches lexicais exatos
        3. Vector Search - Similaridade semântica
        4. RRF Fusion - Combina rankings
        5. Two-Stage Reranking (opcional) - Reordena com embedding large
        6. MMR Diversification (opcional) - Maximiza diversidade
        
        **Parâmetro alpha:**
        - 0.0 = Apenas busca vetorial (semântica)
        - 0.5 = Balanceado (recomendado)
        - 1.0 = Apenas BM25 (lexical)
        
        **Parâmetro expand:**
        - true = Expande query com sinônimos teológicos
        - false = Busca apenas o termo original (default)
        
        **Parâmetro rerank:**
        - true = Reordena com embedding-large (3072 dim)
        - false = Mantém ranking original (default)
        
        **Parâmetro mmr_lambda:**
        - 0.0 = Máxima diversidade
        - 0.5 = Balanço (recomendado)
        - 1.0 = Máxima relevância (sem diversificação)
        
        **Parâmetro dedupe:**
        - true = Remove mesmo versículo de diferentes versões
        - false = Mantém todas as versões (default)
        
        **Parâmetro embedding_source:**
        - verse = Usa verse_embeddings (529K, PT+EN, 17 versões) - default
        - unified = Usa unified_verse_embeddings (31K, apenas PT, 8 versões) - 11x mais rápido
        
        **Exemplos:**
        - "ódio" com alpha=0.7 → prioriza matches exatos
        - "amor de Deus" com alpha=0.3 → prioriza conceitos
        - "perdão" com expand=true → também busca "remissão", "absolvição"
        - "amor de Deus" com mmr_lambda=0.5 → resultados diversificados
        """,
        tags=["rag"],
        parameters=[
            OpenApiParameter(
                name="q",
                location=OpenApiParameter.QUERY,
                required=True,
                description="Texto da consulta (mínimo 2 caracteres)",
                type=str,
                examples=[
                    OpenApiExample("termo_especifico", value="ódio"),
                    OpenApiExample("conceito", value="amor divino"),
                ],
            ),
            OpenApiParameter(
                name="top_k",
                location=OpenApiParameter.QUERY,
                required=False,
                description="Número máximo de resultados (1-50, default: 10)",
                type=int,
            ),
            OpenApiParameter(
                name="alpha",
                location=OpenApiParameter.QUERY,
                required=False,
                description="Peso BM25 vs Vetorial (0.0-1.0, default: 0.5)",
                type=float,
            ),
            OpenApiParameter(
                name="version",
                location=OpenApiParameter.QUERY,
                required=False,
                description="Código da versão bíblica (ex: 'ACF', 'NVI')",
                type=str,
            ),
            OpenApiParameter(
                name="expand",
                location=OpenApiParameter.QUERY,
                required=False,
                description="Expandir query com sinônimos teológicos (default: false)",
                type=bool,
            ),
            OpenApiParameter(
                name="rerank",
                location=OpenApiParameter.QUERY,
                required=False,
                description="Reordenar com embedding large 3072-dim (default: false)",
                type=bool,
            ),
            OpenApiParameter(
                name="mmr_lambda",
                location=OpenApiParameter.QUERY,
                required=False,
                description="MMR lambda: 0=diversidade, 1=relevância (default: não aplicar)",
                type=float,
            ),
            OpenApiParameter(
                name="dedupe",
                location=OpenApiParameter.QUERY,
                required=False,
                description="Deduplica versículos de diferentes versões (default: false)",
                type=bool,
            ),
            OpenApiParameter(
                name="embedding_source",
                location=OpenApiParameter.QUERY,
                required=False,
                description="Fonte de embeddings: 'verse' (529K, PT+EN) ou 'unified' (31K, apenas PT, 11x mais rápido). Default: 'verse'",
                type=str,
                enum=["verse", "unified"],
            ),
        ],
        responses={
            200: RagSearchResponseSerializer,
            400: {"description": "Parâmetros inválidos"},
            **get_error_responses(),
        },
    )
    def get(self, request, *args, **kwargs):
        view_name = self.__class__.__name__
        lang = getattr(request, "lang_code", "-")
        
        # Validar parâmetros
        q = (request.query_params.get("q") or "").strip()
        if not q:
            return Response(
                {"detail": "Parâmetro 'q' é obrigatório", "code": "validation_error"},
                status=400,
            )
        
        if len(q) < 2:
            return Response(
                {"detail": "Query deve ter no mínimo 2 caracteres", "code": "validation_error"},
                status=400,
            )
        
        # Extrair parâmetros
        try:
            top_k = int(request.query_params.get("top_k") or 10)
            top_k = max(1, min(top_k, 50))
        except ValueError:
            top_k = 10
        
        alpha = None
        if request.query_params.get("alpha"):
            try:
                alpha = float(request.query_params.get("alpha"))
                alpha = max(0.0, min(alpha, 1.0))
            except ValueError:
                pass
        
        version = request.query_params.get("version")
        versions = [version] if version else None
        
        # Query Expansion
        expand_query = request.query_params.get("expand", "").lower() in ("true", "1", "yes")
        expand_mode = request.query_params.get("expand_mode", "auto")
        if expand_mode not in ("static", "dynamic", "auto"):
            expand_mode = "auto"
        max_synonyms_raw = request.query_params.get("max_synonyms", "3")
        try:
            max_synonyms = max(1, min(int(max_synonyms_raw), 5))
        except ValueError:
            max_synonyms = 3
        
        # Reranking with large embeddings
        rerank = request.query_params.get("rerank", "").lower() in ("true", "1", "yes")
        
        # MMR Diversification
        mmr_lambda = None
        if request.query_params.get("mmr_lambda"):
            try:
                mmr_lambda = float(request.query_params.get("mmr_lambda"))
                mmr_lambda = max(0.0, min(mmr_lambda, 1.0))
            except ValueError:
                pass
        
        # Deduplicate versions
        dedupe = request.query_params.get("dedupe", "").lower() in ("true", "1", "yes")
        
        # Embedding source: verse (default, all versions) or unified (PT only, faster)
        embedding_source = request.query_params.get("embedding_source", "verse")

        # Embedding model: large (3072d, optimal per TCC Exp6) or small (1536d, faster)
        embedding_model = request.query_params.get("embedding_model", "large")
        if embedding_model not in ("small", "large"):
            embedding_model = "large"

        # Re-embed after expansion: generate new embedding with expanded terms
        reembed = request.query_params.get("reembed", "").lower() in ("true", "1", "yes")
        if embedding_source not in ("verse", "unified"):
            embedding_source = "verse"
        
        # Executar busca híbrida
        try:
            t0 = time.time()
            result = rag_service.search_hybrid(
                query=q,
                top_k=top_k,
                versions=versions,
                alpha=alpha,
                expand_query=expand_query,
                expand_mode=expand_mode,
                max_synonyms=max_synonyms,
                rerank=rerank,
                mmr_lambda=mmr_lambda,
                deduplicate_versions=dedupe,
                embedding_source=embedding_source,
                embedding_model=embedding_model,
                reembed_after_expansion=reembed,
            )
            dur = time.time() - t0
            
            REQUESTS.labels(method="GET", status="200", view=view_name, lang=lang, version=version or "-").inc()
            LATENCY.labels(view=view_name, lang=lang, version=version or "-").observe(dur)
            
            response_data = {
                "hits": result.hits,
                "total": result.total,
                "timing": result.timing,
                "query": result.query,
                "search_type": "hybrid",
                "embedding_source": embedding_source,
            }
            
            # Adicionar info de expansão se disponível
            if hasattr(result, "query_expansion") and result.query_expansion:
                response_data["query_expansion"] = result.query_expansion
            
            # Adicionar info de reranking se disponível
            if hasattr(result, "reranking") and result.reranking:
                response_data["reranking"] = result.reranking
            
            # Adicionar info de MMR se disponível
            if hasattr(result, "mmr_diversification") and result.mmr_diversification:
                response_data["mmr_diversification"] = result.mmr_diversification
            
            return Response(response_data, status=200)
            
        except ValueError as e:
            return Response(
                {"detail": str(e), "code": "validation_error"},
                status=400,
            )
        except Exception as e:
            # Log do erro para debug
            import logging
            logging.getLogger(__name__).error(f"Hybrid search error: {e}", exc_info=True)
            
            REQUESTS.labels(method="GET", status="500", view=view_name, lang=lang, version="-").inc()
            return Response(
                {"detail": f"Erro interno: {str(e)}", "code": "internal_error"},
                status=500,
            )
