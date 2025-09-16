---
id: T-RAG04-xrefs-suggest-approve-feedback
title: "[rag+ai] Cross-Refs — suggest/approve/feedback (ranking híbrido)"
status: ready
created: 2025-09-13
updated: 2025-09-13
owner: "@iuryeng"
reviewers: ["@maintainer"]
labels: ["area/ai", "area/rag", "type/feat", "openapi"]
priority: high
effort: M
risk: medium
depends_on: ["T-RAG01-embeddings-pgvector", "T-RAG02-retriever-service-api"]
related: ["T-010-crossrefs-fix"]
epic: "RAG + Agents"
branch: "feat/T-RAG04-xrefs-suggest-approve-feedback"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Queremos sugerir cross-refs com RAG (recall+rerank), registrar candidates, permitir aprovação humana e feedback.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Modelos: `CrossReferenceCandidate` e `CrossReferenceFeedback` (status suggested/approved/rejected; score/confidence/source/explanation).
- [ ] CA2 — `POST /api/v1/bible/cross-references/suggest` (body: {ref, k, min_score?, strategy}) → lista candidates (sem persistir xref real).
- [ ] CA3 — `POST /api/v1/bible/cross-references/approve` → promove candidates aprovados para CrossReference (source="ai").
- [ ] CA4 — `POST /api/v1/bible/cross-references/feedback` → registra up/down/reject e reason.
- [ ] CA5 — Ranking híbrido (similaridade + coocorrência de temas + votos históricos + proximidade canônica) e thresholds.

## Escopo / Fora do Escopo
- Inclui: endpoints e ranking; logging/trace.
- Não inclui: explain (T-RAG05).

## Impacto Técnico
**DB**: novas tabelas candidates/feedback; **API**: novos endpoints com scopes (`ai-tools`, `write`).

## Plano de Testes
- 200/400/401/403; payloads mínimos válidos; limites e thresholds.

## Observabilidade
- `ai_xrefs_suggest_total`, `ai_xrefs_accept_rate`, latência.
