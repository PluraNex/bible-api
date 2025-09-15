---
id: T-RAG07-simple-eval-endpoint
title: "[rag] Eval simples — endpoint de teste (retrieval-only)"
status: ready
created: 2025-09-14
updated: 2025-09-14
owner: "@iuryeng"
labels: ["area/rag", "type/feat", "openapi"]
priority: medium
effort: S
epic: "RAG + Agents"
depends_on: ["T-RAG01-embeddings-pgvector", "T-RAG02-retriever-service-api"]
---

## Contexto
Precisamos validar o RAG na prática com um endpoint simples, sem avaliação complexa. Deve receber uma lista de queries, executar retrieval e retornar hits + métricas básicas de latência e cobertura.

## Escopo
- POST /api/v1/bible/rag/eval-simple (Api-Key)
- Body: { queries: string[], k?: number, versions?: string[] }
- Resposta: { summary: {queries, k, coverage, latency_ms:{p50,p95}}, per_query: [{query, latency_ms, retrieved: [...]}] }
- Sem cache; medir o motor real.

## Critérios de Aceite
- [ ] Endpoint retorna 200 com queries válidas; 400 se vazio/inválido.
- [ ] Métricas de latência calculadas (p50, p95) e cobertura (>0 se houver dados).
- [ ] Suporta filtro por versions.
- [ ] Documentado no OpenAPI (via extend_schema) e no runbook de operações.

## Fora do Escopo
- Métricas avançadas (Recall@K, nDCG, MRR), citation accuracy, agentes.
- Rerank com embedding_large.

## Teste Rápido
curl -X POST http://localhost:8000/api/v1/bible/rag/eval-simple/ \
  -H "Authorization: Api-Key <SUA_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"queries":["amor de Deus","o Senhor é meu pastor"], "k": 5, "versions":["PT_NAA"]}'
