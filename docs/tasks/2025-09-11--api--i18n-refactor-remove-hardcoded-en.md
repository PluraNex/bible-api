---
id: T-I18N16
title: "[api] Refactor i18n — remover hardcodes 'en', usar request.lang_code e documentar lang"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/api", "type/refactor", "i18n"]
priority: high
effort: S
risk: low
depends_on: ["T-I18N01"]
related: ["T-I18N02", "T-I18N03", "T-I18N05"]
epic: "I18N — Suporte Multilíngue"
branch: "refactor/i18n-remove-hardcoded-en"
pr: ""
github_issue: ""
due: null
---

## Contexto
Após revisar o código, identificamos ocorrências de `"en"` hardcoded em serializers/views (Books/Themes), e pontos onde o serializer não recebe `context={'request': request}`. Isso viola os padrões i18n definidos.

Arquivos afetados:
- `bible/books/serializers.py: get_name/get_abbreviation`
- `bible/books/views.py: uso de get_book_display_name e instanciamento de serializers`
- `bible/themes/views.py: pontos que filtram por language__code="en"`
- `bible/verses/serializers.py: permitir override de nome do livro por lang`

## Objetivo e Critérios de Aceite
- [ ] CA1 — Remover hardcodes `"en"` e utilizar `request.lang_code` com fallback
- [ ] CA2 — Passar `context={'request': request}` em serializers instanciados manualmente
- [ ] CA3 — Adicionar `OpenApiParameter(name="lang")` nos endpoints Books/Themes/Verses
- [ ] CA4 — Adicionar header `Vary: Accept-Language` nas respostas sensíveis a idioma
- [ ] CA5 — Alinhar com `docs/API_STANDARDS.md §6`

## Escopo / Fora do Escopo
- Inclui: ajustes leves em views/serializers existentes
- Não inclui: criação de modelos i18n (autores/comentários), cobertos em outras tasks

## Impacto Técnico
**Contrato**: adiciona param opcional `lang` | **Performance**: mínima | **Segurança**: n/a

## Plano de Testes
- Exercitar Books/Themes/Verses com `lang=pt`, `lang=en`, e `Accept-Language`

## Observabilidade
- Verificar presença de `Vary: Accept-Language`

## Rollout & Rollback
- Rollout incremental por domínio; rollback revertendo diffs
