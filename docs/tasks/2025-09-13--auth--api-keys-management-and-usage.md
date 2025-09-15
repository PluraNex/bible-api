---
id: T-008-auth-api-keys
title: "[auth] API Keys — Gestão, Uso e Rate-Limits"
status: ready
created: 2025-09-13
updated: 2025-09-13
owner: "@iuryeng"
reviewers: ["@maintainer"]
labels: ["area/auth", "type/feat", "security", "openapi"]
priority: high
effort: M
risk: medium
depends_on: ["T-004-core-functional"]
related: ["T-152-dynamic-rate-limit-by-apikey", "T-990-logging-request-id-format", "T-105-prometheus-metrics-endpoint"]
epic: "Fase 2: Segurança & Governança"
branch: "feat/T-008-auth-api-keys"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Há endpoints de auth básicos; falta gestão de chaves via API (criar/listar/revogar) e visão de uso.
- API Standards exigem escopos, rate-limits e headers padronizados.

## Objetivo e Critérios de Aceite
- [ ] CA1 — `GET/POST /api/v1/auth/api-keys/`: listar/criar chaves (escopos, rate_limit por chave).
- [ ] CA2 — `DELETE /api/v1/auth/api-keys/<id>/`: revogar (ou rotacionar) chave.
- [ ] CA3 — `GET /api/v1/auth/usage/`: consumo da chave atual (janela diária/horária; contadores básicos).
- [ ] CA4 — `GET /api/v1/auth/admin/usage/`: visão agregada (protegida por escopo `admin`).
- [ ] CA5 — Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After` quando aplicável.
- [ ] CA6 — OpenAPI com exemplos curl/JS/Python; segurança `ApiKeyAuth` e escopos.

## Escopo / Fora do Escopo
- Inclui: endpoints REST; integração com throttling escopado quando task T-Scoped estiver ativa.
- Não inclui: faturamento/cobrança; UI.

## Impacto Técnico
**Contrato**: novos endpoints em `/auth/`.
**DB/Migrations**: opcional p/ armazenamento de uso (se não existente); hashing seguro.
**Throttle/Cache**: respeitar escopos e limites por chave.
**Segurança**: PII zero em logs; mascarar chaves.

## Plano de Testes
- 200/201/204/401/403/404/409/429 conforme casos.
- Contrato OpenAPI válido; exemplos coerentes.

## Observabilidade
- Contadores por chave e por escopo.
- Logs com `request_id`, sem vazamento de chaves.

## Rollout & Rollback
- Migração leve (se necessária); rollback trivial.

## Checklist Operacional (Autor)
- [ ] OpenAPI gerado/commitado.
- [ ] `make fmt lint test` ok; CI verde.

## Checklist Operacional (Revisor)
- [ ] Segurança e escopos corretos.
- [ ] Rate-limit coerente e headers presentes.
- [ ] Testes completos e determinísticos.
