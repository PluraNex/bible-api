---
id: T-I18N09
title: "[data] Autores: modelos de tradução — nomes, apelidos e biografia"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/data", "type/feat", "i18n"]
priority: high
effort: M
risk: medium
depends_on: []
related: ["T-I18N10"]
epic: "I18N — Suporte Multilíngue"
branch: "feat/i18n-authors-models"
pr: ""
github_issue: ""
due: null
---

## Contexto
- O modelo `Author` possui campos textuais em um único idioma (geralmente inglês/latim). Precisamos suportar múltiplos idiomas.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Criar `AuthorName` (author, language, name, short_name, also_known_as JSON)
- [ ] CA2 — Criar `AuthorText` (author, language, biography_summary, theological_contributions, historical_impact)
- [ ] CA3 — Índices e constraints (únicos por autor+idioma)
- [ ] CA4 — Migração inicial sem perda de dados (popular `en` a partir dos campos atuais)

## Impacto Técnico
**DB**: novas tabelas e migração com dados | **Performance**: índices necessários

## Plano de Testes
- Criar autor com traduções em `en` e `pt`; consulta por idioma retorna valores corretos
