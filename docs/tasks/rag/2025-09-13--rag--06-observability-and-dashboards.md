---
id: T-RAG06-observability-dashboards
title: "[rag+ai] Observabilidade — métricas e dashboards"
status: ready
created: 2025-09-13
updated: 2025-09-13
owner: "@iuryeng"
reviewers: ["@maintainer"]
labels: ["area/observability", "type/docs", "grafana", "prometheus"]
priority: medium
effort: S
risk: low
depends_on: ["T-RAG02-retriever-service-api"]
related: []
epic: "RAG + Agents"
branch: "feat/T-RAG06-observability-dashboards"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Consolidar métricas RAG/IA nos dashboards (Prometheus + Grafana) já provisionados.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Métricas: `rag_retrieve_total`, `rag_retrieve_latency_seconds_bucket`, `rag_cache_hits_total`.
- [ ] CA2 — Métricas IA: `ai_xrefs_suggest_total`, `ai_xrefs_accept_rate`, `ai_xrefs_explain_total`.
- [ ] CA3 — Painéis no dashboard: RAG latency/Hit@K (aprox), cache hit-rate; AI accept rate, distribuição de força.

## Escopo / Fora do Escopo
- Inclui: instrumentação e painéis.
- Não inclui: alertas (pode ser tarefa futura).

## Plano de Testes
- Verificar presença e atualização das séries; screenshots no PR.
