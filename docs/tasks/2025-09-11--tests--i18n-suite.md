---
id: T-I18N06
title: "[tests] Suíte de i18n — books/verses/versions com lang e Accept-Language"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/api", "type/test", "i18n"]
priority: high
effort: M
risk: low
depends_on: ["T-I18N01", "T-I18N02", "T-I18N03", "T-I18N04"]
related: []
epic: "I18N — Suporte Multilíngue"
branch: "test/i18n-suite"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Validar end-to-end o suporte multilíngue com headers e query params.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Tests para resolver idioma (`lang`, `Accept-Language`)
- [ ] CA2 — Books retornam nomes corretos por idioma com fallback
- [ ] CA3 — Verses respeitam idioma no `display_name` e default de versão por idioma
- [ ] CA4 — Versions filtram por idioma e endpoint de default funciona
