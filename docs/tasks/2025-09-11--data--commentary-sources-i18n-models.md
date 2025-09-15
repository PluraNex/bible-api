---
id: T-I18N11
title: "[data] Fontes de comentário: i18n — nomes e descrições por idioma"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/data", "type/feat", "i18n"]
priority: medium
effort: S
risk: low
depends_on: []
related: ["T-I18N12"]
epic: "I18N — Suporte Multilíngue"
branch: "feat/i18n-commentary-sources-models"
pr: ""
github_issue: ""
due: null
---

## Contexto
- `CommentarySource` tem `name` e `description` em um idioma. Precisamos permitir traduções.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Criar `CommentarySourceText` (source, language, name, description)
- [ ] CA2 — Índices e constraint único por source+language
- [ ] CA3 — Migração populando `en` a partir dos campos atuais
