---
id: T-I18N10
title: "[api] Autores: endpoints i18n — nomes/bio por lang e busca multilíngue"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/api", "type/feat", "i18n"]
priority: high
effort: M
risk: low
depends_on: ["T-I18N01", "T-I18N09"]
related: []
epic: "I18N — Suporte Multilíngue"
branch: "feat/i18n-authors-endpoints"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Expor autores com nome/bio no idioma solicitado e permitir busca em nomes/aliases por idioma.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Param `lang` em list/detail de autores; retorno com `name`, `short_name`, `also_known_as`, `biography_summary` no idioma
- [ ] CA2 — Busca (`search`) considera `AuthorName.name/short_name/also_known_as` no idioma resolvido
- [ ] CA3 — Fallback de idioma para `en` se tradução ausente

## Impacto Técnico
**Contrato**: novos campos i18n estáveis | **Performance**: índices em tables i18n

## Plano de Testes
- Autores com/sem tradução; buscas com `lang=pt` e fallback
