---
id: T-AI01
title: "[ai] Escopos e throttling em endpoints de AI"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/ai", "type/chore", "security"]
priority: medium
effort: S
risk: low
depends_on: ["T-T01"]
related: []
epic: "Confiabilidade e Segurança"
branch: "feat/ai-scopes-throttling"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Endpoints AI estão em skeleton e precisam de `required_scopes` e `throttle_scope`.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Adicionar `permission_classes=[HasAPIScopes]` nas views AI
- [ ] CA2 — Definir `required_scopes` por rota (ex.: `ai-run`, `ai-tools`)
- [ ] CA3 — Definir `throttle_scope` correspondente

## Escopo / Fora do Escopo
- Inclui: ajustes em `bible/ai/views.py` e docs
- Não inclui: implementação das features AI

## Impacto Técnico
**Segurança**: reforça controle de acesso | **Contrato**: n/a

## Plano de Testes
- 403 quando escopo ausente; 200/501 quando presente

## Observabilidade
- Logs de 403 por falta de escopo

## Rollout & Rollback
- Mudança segura e reversível
