---
id: T-RAG03-version-policy
title: "[rag] Política de Versões — enabled_for_rag, ai_allowed, embedding_ready"
status: ready
created: 2025-09-13
updated: 2025-09-13
owner: "@iuryeng"
reviewers: ["@maintainer"]
labels: ["area/rag", "type/policy", "versions"]
priority: medium
effort: S
risk: low
depends_on: []
related: ["T-RAG01-embeddings-pgvector", "T-RAG02-retriever-service-api"]
epic: "RAG + Agents"
branch: "feat/T-RAG03-version-policy"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Precisamos controlar quais versões participam do RAG (licenças, readiness) sem migrar o schema agora.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Settings: `RAG_ALLOWED_VERSIONS`, `RAG_DEFAULT_VERSIONS`, `RAG_VERSION_FLAGS` (por code → {enabled_for_rag, ai_allowed, embedding_ready}).
- [ ] CA2 — Retriever respeita flags; endpoint `/rag/retrieve` valida e filtra.
- [ ] CA3 — Documentação dos flags em `docs/OBSERVABILITY.md` e `API_STANDARDS.md` seção RAG.

## Escopo / Fora do Escopo
- Inclui: política via settings; sem migração.
- Não inclui: campos novos em Version (pode vir depois).

## Impacto Técnico
**Segurança/Legal**: versões com ai_allowed=false ficam fora do índice RAG.

## Plano de Testes
- Unit do filtro de versões; integração simples via endpoint.
