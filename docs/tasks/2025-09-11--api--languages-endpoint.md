---
id: T-I18N14
title: "[api] Endpoint de idiomas — listar e filtrar Languages"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/api", "type/feat", "i18n"]
priority: medium
effort: S
risk: low
depends_on: []
related: ["T-I18N15"]
epic: "I18N — Suporte Multilíngue"
branch: "feat/api-languages-endpoint"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Existe `Language` no modelo, com serializer, mas não há endpoint público padronizado.

## Objetivo e Critérios de Aceite
- [ ] CA1 — `GET /api/v1/bible/languages/` lista idiomas disponíveis
- [ ] CA2 — Filtros: `code` e (opcional) `is_active` se campo for adicionado depois
- [ ] CA3 — Documentar no OpenAPI com exemplos
