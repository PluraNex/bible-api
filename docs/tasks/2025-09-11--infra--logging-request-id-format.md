---
id: T-OB01
title: "[infra] Logging com request_id — formatter e ordem do middleware"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/infra", "observability", "type/chore"]
priority: high
effort: S
risk: low
depends_on: []
related: []
epic: "Observabilidade"
branch: "feat/logging-request-id"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Incluir `request_id` nos logs e garantir `RequestIDMiddleware` no topo da pilha.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Formatter inclui `{request_id}`
- [ ] CA2 — Middleware de request_id primeiro na lista
- [ ] CA3 — Logs mostram `X-Request-ID` correlacionável

## Escopo / Fora do Escopo
- Inclui: ajustes em settings e middleware
- Não inclui: tracing distribuído

## Impacto Técnico
**Contrato**: n/a | **Segurança**: n/a

## Plano de Testes
- Requisição qualquer e inspecionar log/headers

## Rollout & Rollback
- Config flags; rollback simples
