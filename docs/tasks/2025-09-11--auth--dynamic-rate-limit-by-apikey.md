---
id: T-T02
title: "[auth] Rate limit dinâmico por API Key — throttle custom"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/auth", "type/feat", "performance"]
priority: medium
effort: M
risk: medium
depends_on: ["T-T01"]
related: []
epic: "Confiabilidade e Segurança"
branch: "feat/auth-dynamic-rate-limit"
pr: ""
github_issue: ""
due: null
---

## Contexto
- `APIKey.rate_limit` deve controlar limites por chave, com multiplicadores por escopo.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Implementar throttle custom que lê `request.auth.rate_limit`
- [ ] CA2 — Suporte a multiplicadores por escopo (ex.: `ai-run` mais restrito)
- [ ] CA3 — Testes cobrindo limites distintos por chave

## Escopo / Fora do Escopo
- Inclui: throttle novo e integração DRF
- Não inclui: planos de billing/cotas (futuro)

## Impacto Técnico
**Contrato**: n/a | **DB**: n/a | **Performance**: controle fino de consumo

## Plano de Testes
- Simular chaves com `rate_limit` baixo/alto e validar 429

## Observabilidade
- Logs de limite atingido com `key_id` e escopo

## Rollout & Rollback
- Deploy gradual; fallback ao throttle padrão
