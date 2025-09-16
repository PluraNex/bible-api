---
id: T-I18N12
title: "[api] Comentários: i18n — título/texto e fallback por idioma"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/api", "type/feat", "i18n"]
priority: medium
effort: M
risk: medium
depends_on: ["T-I18N01", "T-I18N11"]
related: []
epic: "I18N — Suporte Multilíngue"
branch: "feat/i18n-commentary-endpoints"
pr: ""
github_issue: ""
due: null
---

## Contexto
- `CommentaryEntry` tem `title/body_text` em um único idioma (o da fonte). Precisamos mecanismo de tradução opcional com fallback.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Adicionar `CommentaryEntryText` (entry, language, title, body_text/body_html)
- [ ] CA2 — Endpoints aceitam `lang` e retornam texto no idioma se houver, senão fallback para idioma da fonte
- [ ] CA3 — Documentar limitações (traduções podem não existir para todos)

## Impacto Técnico
**DB**: nova tabela | **Contrato**: campos i18n | **Performance**: considerar prefetch

## Plano de Testes
- Entradas com/sem tradução; fallback para idioma da fonte
