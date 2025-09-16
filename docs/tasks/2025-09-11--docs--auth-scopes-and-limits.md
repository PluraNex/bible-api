---
id: T-DX01
title: "[docs] Atualizar README/OpenAPI — escopos, limites e exemplos"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/docs", "type/docs"]
priority: low
effort: S
risk: low
depends_on: ["T-T01", "T-T02", "T-S02"]
related: []
epic: "DX & Documentação"
branch: "docs/auth-scopes-limits"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Documentar uso de `Api-Key`, escopos por rota, políticas de throttle e exemplos atualizados.

## Objetivo e Critérios de Aceite
- [ ] CA1 — README com tabela de escopos e limites por escopo
- [ ] CA2 — Exemplos (curl/JS/Python) alinhados ao novo fluxo
- [ ] CA3 — OpenAPI com descrições atualizadas (onde aplicável)

## Escopo / Fora do Escopo
- Inclui: README, snippets em views, comentários no settings
- Não inclui: site de docs separado

## Impacto Técnico
**Contrato**: documentação

## Plano de Testes
- Conferir `docs/openapi-v1.yaml` e UI do Swagger

## Observabilidade
- n/a

## Rollout & Rollback
- Apenas docs; rollback não aplicável
