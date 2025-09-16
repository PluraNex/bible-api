---
id: T-I18N07
title: "[infra] Cache e ETag variando por idioma — Vary: Accept-Language/lang"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/infra", "type/chore", "i18n", "performance"]
priority: medium
effort: S
risk: low
depends_on: ["T-P01", "T-I18N01"]
related: []
epic: "I18N — Suporte Multilíngue"
branch: "feat/cache-vary-language"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Quando resposta depende de idioma, o cache/ETag deve variar por `lang`/`Accept-Language`.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Adicionar header `Vary: Accept-Language` e considerar `lang` nos keys de cache
- [ ] CA2 — ETags diferentes por idioma
