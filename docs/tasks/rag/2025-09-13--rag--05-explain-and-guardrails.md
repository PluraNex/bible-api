---
id: T-RAG05-explain-guardrails
title: "[ai] Explain + Guardrails — prompts, limites e observabilidade"
status: ready
created: 2025-09-13
updated: 2025-09-13
owner: "@iuryeng"
reviewers: ["@maintainer"]
labels: ["area/ai", "type/feat", "observability"]
priority: medium
effort: S
risk: medium
depends_on: ["T-RAG02-retriever-service-api"]
related: ["T-RAG04-xrefs-suggest-approve-feedback"]
epic: "RAG + Agents"
branch: "feat/T-RAG05-explain-guardrails"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Precisamos de explicações curtas (LLM) com citações e guardrails para evitar alucinação.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Tool `explain_cross_reference(ref_from, ref_to)` com context pack (versos/hits) e prompt policy.
- [ ] CA2 — Limites: tokens, timeout, rate-limit por escopo `ai-run`.
- [ ] CA3 — Observabilidade: tokens usados, latência, sucesso/falha, trace_id.

## Escopo / Fora do Escopo
- Inclui: tool e endpoint (se necessário), logs e métricas.
- Não inclui: UI.

## Plano de Testes
- Smoke (mocks); validação de payloads e limites.
