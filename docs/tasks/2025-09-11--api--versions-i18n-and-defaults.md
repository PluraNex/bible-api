---
id: T-I18N04
title: "[api] Versions: filtros por código/idioma e endpoint de default por idioma"
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
related: ["T-I18N03"]
epic: "I18N — Suporte Multilíngue"
branch: "feat/i18n-versions-defaults"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Versions já filtram por `language` id/código; precisamos padronizar `lang` e expor "default version" por idioma.

## Objetivo e Critérios de Aceite
- [ ] CA1 — `language` aceita alias `lang` (código ISO)
- [ ] CA2 — Novo endpoint: `versions/default/?lang=pt` retorna versão padrão ativa para o idioma
- [ ] CA3 — Documentar critério de escolha (prioridade/config)

## Impacto Técnico
**Contrato**: novo endpoint | **DB**: n/a

## Plano de Testes
- Defaults por idiomas com/sem dados; 404 quando não houver
