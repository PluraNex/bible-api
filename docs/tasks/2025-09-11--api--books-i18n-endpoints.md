---
id: T-I18N02
title: "[api] Books: suporte a i18n — param lang, serializers e busca por idioma"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/api", "type/feat", "i18n"]
priority: high
effort: M
risk: low
depends_on: ["T-I18N01", "T-I18N08"]
related: []
epic: "I18N — Suporte Multilíngue"
branch: "feat/i18n-books-endpoints"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Dataset possui `BookName` por idioma/versão. Endpoints devem expor nomes/abreviações no idioma solicitado.
 - Ajustar hardcodes "en" em serializers/views.
 - Alinhar com `docs/API_STANDARDS.md §6`.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Adicionar `lang` a todos os endpoints de books (list/info/outline/context/...)
- [ ] CA2 — Serializers retornam `name`, `abbreviation` e `display_name` no idioma resolvido
- [ ] CA3 — Busca (`search`) considera `names__name/abbreviation` filtrando por idioma quando `lang` informado
- [ ] CA4 — Fallback para nome em `en` quando não houver no idioma solicitado

## Escopo / Fora do Escopo
- Inclui: ajustes em views/serializers, documentação OpenAPI, testes
- Não inclui: modelos novos (já existem `BookName`/`Language`)

## Impacto Técnico
**Contrato**: novo param `lang` e campos i18n estáveis | **DB**: n/a

## Plano de Testes
- Casos: `lang=pt`, `lang=en`, idioma inexistente, fallback

## Observabilidade
- Respostas definem `Vary: Accept-Language`

## Rollout & Rollback
- Rollout por domínio `books` apenas; rollback revertendo mudanças nas views/serializers

## Checklist Operacional (Autor)
- [ ] `context={'request': request}` ao instanciar serializers nas views
- [ ] Remoção de hardcodes "en"
- [ ] OpenAPI com `OpenApiParameter(lang)` e exemplos

## Checklist Operacional (Revisor)
- [ ] Fallback para `en` bem documentado e testado
- [ ] Sem N+1; `select_related/prefetch_related` mantidos
