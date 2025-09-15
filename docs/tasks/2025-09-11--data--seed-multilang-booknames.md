---
id: T-I18N08
title: "[data] Garantir seed com BookName multilíngue e coerente com versions"
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
related: []
epic: "I18N — Suporte Multilíngue"
branch: "chore/seed-booknames-i18n"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Para i18n consistente, precisamos garantir `BookName` em `en` e `pt` (e outros necessários) para todos os `CanonicalBook`.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Script/command de seed que valida e popula nomes/abreviações por idioma
- [ ] CA2 — Garantir nomes default por idioma (version `null`) e opcionais por versão
- [ ] CA3 — Relatório de lacunas (livros sem nome em um idioma)
