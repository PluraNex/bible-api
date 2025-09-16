---
id: T-I18N15
title: "[data] Padronização de Language — ISO, seeds e validações"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/data", "type/chore", "i18n"]
priority: medium
effort: S
risk: low
depends_on: []
related: ["T-I18N08", "T-I18N14"]
epic: "I18N — Suporte Multilíngue"
branch: "chore/language-standardization"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Garantir que `Language.code` siga ISO (ex.: `en`, `pt`, `es`) e que o seed base esteja completo.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Validar formato de `code` (regex ISO 639-1; aceitar variantes com hífen se necessário)
- [ ] CA2 — Seed mínimo: `en`, `pt`, `es` com unicidade garantida
- [ ] CA3 — Admin/fixtures/documentação sobre adicionar novos idiomas
