---
id: T-T01
title: "[api] Throttling por escopo — ScopedRateThrottle e mapeamento por rota"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/api", "type/feat", "performance"]
priority: high
effort: M
risk: low
depends_on: []
related: ["T-T02", "T-AI01"]
epic: "Confiabilidade e Segurança"
branch: "feat/api-scoped-throttling"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Limitar por escopo (read/write/search/ai-run/audio) melhora previsibilidade e proteção.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Trocar `DEFAULT_THROTTLE_CLASSES` para `ScopedRateThrottle`
- [ ] CA2 — **Reintroduzir** `throttle_scope` nas views Books/Verses (removido em T-I18N03 até implementação)
- [ ] CA3 — `DEFAULT_THROTTLE_RATES` por escopo configurados (`read`, `search`, `ai-run`, etc.)
- [ ] CA4 — 429 com `Retry-After` quando excedido

**Nota**: Views Books/Verses tiveram `throttle_scope` removido temporariamente (T-I18N03) para evitar configuração inconsistente. Reintroduzir após implementar configuração base.

## Escopo / Fora do Escopo
- Inclui: settings, views, doc dos escopos
- Não inclui: limites dinâmicos por chave (T-T02)

## Impacto Técnico
**Contrato**: n/a | **DB**: n/a | **Segurança**: mitigação de abuso

## Plano de Testes
- Exercitar cada escopo e verificar contagem/429

## Observabilidade
- Logs com escopo aplicado; métricas de 429

## Rollout & Rollback
- Alteração segura; rollback trocando classe padrão
