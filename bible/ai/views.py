"""
AI Agent and Tool views for Bible API.
Skeleton implementation with auth and schema annotations.
"""
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
            except Exception:
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


class RagSearchView(APIView):
    """RAG search (simples): GET /api/v1/ai/rag/search

    - Apenas parâmetros essenciais: q e top_k.
    - Usa RAG_ALLOWED_VERSIONS do ambiente por padrão.
    """

    @extend_schema(
        summary="RAG search — simples (q, top_k)",
        tags=["rag"],
        parameters=[
            OpenApiParameter(
                name="q",
                location=OpenApiParameter.QUERY,
                required=True,
                description="Texto da consulta",
                type=str,
                examples=[OpenApiExample("query_pt", value="amor de Deus")],
            ),
            OpenApiParameter(
                name="top_k",
                location=OpenApiParameter.QUERY,
                required=False,
                description="Quantidade de resultados (default 10)",
                type=int,
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
        if not q:
            return Response({"detail": "Informe 'q'."}, status=400)
        top_k = int(request.query_params.get("top_k") or 10)

        view_name = self.__class__.__name__
        try:
            t0 = time.time()
            result = rag_svc.retrieve(query=q, vector=None, top_k=top_k, versions=None)
            dur = time.time() - t0
            REQUESTS.labels(
                method="GET", status="200", view=view_name, lang=getattr(request, "lang_code", "-"), version="-"
            ).inc()
            LATENCY.labels(view=view_name, lang=getattr(request, "lang_code", "-"), version="-").observe(dur)
            return Response(result, status=200)
        except Exception as e:
            REQUESTS.labels(
                method="GET", status="500", view=view_name, lang=getattr(request, "lang_code", "-"), version="-"
            ).inc()
            return Response({"detail": str(e)}, status=500)
