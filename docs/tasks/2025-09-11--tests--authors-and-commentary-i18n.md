---
id: T-I18N13
title: "[tests] Autores e Comentários — testes de i18n (lang/fallback/busca)"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/api", "type/test", "i18n"]
priority: high
effort: M
risk: low
depends_on: ["T-I18N09", "T-I18N10", "T-I18N11", "T-I18N12"]
related: []
epic: "I18N — Suporte Multilíngue"
branch: "test/i18n-authors-commentary"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Validar multilíngue para autores e comentários.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Autores: retorno de nomes/bio por `lang` e fallback
- [ ] CA2 — Busca de autores respeita idioma e aliases
- [ ] CA3 — Comentários: título/texto por `lang`, fallback para idioma da fonte
