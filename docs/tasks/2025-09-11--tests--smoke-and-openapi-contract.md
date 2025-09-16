---
id: T-TS01
title: "[tests] Smoke tests + contrato OpenAPI"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/api", "type/test", "contract"]
priority: high
effort: M
risk: low
depends_on: []
related: ["T-S02"]
epic: "Qualidade e Confiabilidade"
branch: "test/smoke-and-contract"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Consolidar sanidade das rotas e aderência ao schema publicado.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Smoke: `/health/`, `/api/v1/bible/books/`, `/api/v1/bible/versions/` (com/sem auth)
- [ ] CA2 — Gerar schema via `SpectacularAPIView` e validar presença de `ApiKeyAuth`
- [ ] CA3 — Asserts de códigos (200/401/403) e chaves básicas do payload

## Escopo / Fora do Escopo
- Inclui: novos testes em `tests/api` e `tests/contract`
- Não inclui: testes de performance

## Impacto Técnico
**Contrato**: validado | **CI**: aumenta confiança

## Plano de Testes
- `pytest -q --quick` executa smoke e contrato

## Observabilidade
- n/a

## Rollout & Rollback
- Apenas testes; rollback não aplicável
