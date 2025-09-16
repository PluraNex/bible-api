---
id: T-I18N05
title: "[docs] OpenAPI: documentar i18n — params lang e negociação"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/docs", "type/docs", "i18n"]
priority: medium
effort: S
risk: low
depends_on: ["T-I18N01", "T-I18N02", "T-I18N03", "T-I18N04"]
related: []
epic: "I18N — Suporte Multilíngue"
branch: "docs/openapi-i18n"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Schema deve mostrar `lang`, exemplos multilíngues e comportamento de fallback.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Adicionar `OpenApiParameter(lang)` nas views relevantes
- [ ] CA2 — Exemplos em `pt` e `en` nos endpoints principais
- [ ] CA3 — Descrever prioridade `lang` vs `Accept-Language`
