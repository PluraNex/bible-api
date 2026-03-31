"""Simplified RAG evaluation endpoint (retrieval-only).

POST /api/v1/bible/rag/eval-simple
Auth: Api-Key
Body:
{
  "queries": ["amor de Deus", "o Senhor é meu pastor"],
  "k": 10,
  "versions": ["PT_NAA"]
}

Response: summary + per_query with hits and latência.
"""

from __future__ import annotations

import statistics
import time
from typing import Any

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from bible.ai import retrieval as rag_svc
from common.openapi import get_error_responses


class RagEvalSimpleView(APIView):
    """Execute simple retrieval for a list of queries and report latency/coverage."""

    @extend_schema(
        summary="RAG Eval (simples) — retrieval-only",
        request=inline_serializer(
            name="RagEvalSimpleRequest",
            fields={
                "queries": serializers.ListField(child=serializers.CharField()),
                "k": serializers.IntegerField(default=10, required=False),
                "versions": serializers.ListField(
                    child=serializers.CharField(), required=False
                ),
            },
        ),
        responses={
            200: inline_serializer(
                name="RagEvalSimpleResponse",
                fields={
                    "summary": serializers.DictField(),
                    "per_query": serializers.ListField(child=serializers.DictField()),
                },
            ),
            **get_error_responses(),
        },
        tags=["rag"],
    )
    def post(self, request, *args, **kwargs):
        payload = request.data or {}
        queries = payload.get("queries") or []
        if not isinstance(queries, list) or not queries:
            return Response({"detail": "'queries' deve ser lista não vazia"}, status=status.HTTP_400_BAD_REQUEST)
        k = int(payload.get("k") or 10)
        versions = payload.get("versions")
        if versions is not None and (not isinstance(versions, list) or not all(isinstance(v, str) for v in versions)):
            return Response({"detail": "'versions' deve ser lista de strings"}, status=status.HTTP_400_BAD_REQUEST)

        per_query: list[dict[str, Any]] = []
        latencies: list[float] = []
        hits_non_empty = 0

        for q in queries:
            q = (q or "").strip()
            t0 = time.time()
            try:
                result = rag_svc.retrieve(query=q, vector=None, top_k=k, versions=versions)
                dur_ms = (time.time() - t0) * 1000.0
                latencies.append(dur_ms)
                hits = result.get("hits", [])
                if hits:
                    hits_non_empty += 1
                per_query.append(
                    {
                        "query": q,
                        "latency_ms": round(dur_ms, 2),
                        "retrieved": [
                            {
                                "verse_id": h.get("verse_id"),
                                "version": h.get("version"),
                                "score": h.get("score"),
                                "text": h.get("text"),
                                "ref": f"{h.get('book_id')}:{h.get('chapter')}:{h.get('number')}",
                            }
                            for h in hits
                        ],
                    }
                )
            except Exception as e:
                dur_ms = (time.time() - t0) * 1000.0
                latencies.append(dur_ms)
                per_query.append(
                    {
                        "query": q,
                        "error": str(e),
                        "latency_ms": round(dur_ms, 2),
                        "retrieved": [],
                    }
                )

        coverage = hits_non_empty / max(len(queries), 1)
        p50 = statistics.median(latencies) if latencies else 0.0
        p95 = (
            statistics.quantiles(latencies, n=100)[94] if len(latencies) >= 20 else max(latencies) if latencies else 0.0
        )

        summary = {
            "queries": len(queries),
            "k": k,
            "coverage": round(coverage, 3),
            "latency_ms": {"p50": round(p50, 1), "p95": round(p95, 1)},
            "config": {"versions": versions},
        }

        return Response({"summary": summary, "per_query": per_query}, status=200)
