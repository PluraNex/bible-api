---
id: T-RAG02-retriever-service-api
title: "[rag] Retriever Service + API (/rag/retrieve)"
status: ready
created: 2025-09-13
updated: 2025-09-13
owner: "@iuryeng"
reviewers: ["@maintainer"]
labels: ["area/rag", "type/feat", "openapi"]
priority: high
effort: M
risk: medium
depends_on: ["T-RAG01-embeddings-pgvector"]
related: ["T-RAG03-version-policy", "T-007-verses-reference-range-compare"]
epic: "RAG + Agents"
branch: "feat/T-RAG02-retriever-service-api"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Expor serviço de recuperação vetorial (com filtros e cache) para consumo direto por clientes e por agents/tools.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Serviço interno `rag.retrieve(query, filters)` com cache 5–15 min e métricas.
- [ ] CA2 — Endpoint `GET /api/v1/rag/retrieve` retornando {hits, timing, request_id}.
- [ ] CA3 — Suporte a filtros: versions, book(s), chapter range, lang.
- [ ] CA4 — OpenAPI com exemplos PT/EN; rate limit e throttle `search`.

## Escopo / Fora do Escopo
- Inclui: endpoint + serviço + cache + métricas Prometheus.
- Não inclui: batch-retrieve (TBD, se necessário).

## Impacto Técnico
**Cache**: chave por query+filtros; invalidação por versão/embedding_version.
**Segurança**: Api-Key (read), rate-limit.

## Plano de Testes
- 200 com query válida, 400 sem query, 401 sem Api-Key; timing presente; cache hit observado em logs/métricas.

## Observabilidade
- `rag_retrieve_total`, `rag_retrieve_latency_seconds_bucket`, `rag_cache_hits_total`.

## Rollout & Rollback
- Rota isolada; rollback simples.
