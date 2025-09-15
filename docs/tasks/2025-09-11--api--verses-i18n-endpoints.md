---
id: T-I18N03
title: "[api] Verses: suporte a i18n — display_name e seleção por versão/idioma"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/api", "type/feat", "i18n"]
priority: high
effort: M
risk: low
depends_on: ["T-I18N01", "T-I18N04"]
related: ["T-I18N04"]
epic: "I18N — Suporte Multilíngue"
branch: "feat/i18n-verses-endpoints"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Verses tem texto por `Version` (que possui `language`). Precisamos alinhar `lang` com `version` e nomes de livros.

## Objetivo e Critérios de Aceite
- [ ] CA1 — `lang` afeta `display_name` do livro em responses de versículos
- [ ] CA2 — Se `version` não for passada, oferecer default por idioma (ex.: primeira versão ativa do idioma)
- [ ] CA3 — Validar coerência: se `version` com idioma ≠ `lang`, documentar preferência (ex.: `version` vence)
- [ ] CA4 — Serializers incluem `reference` e `book_name` no idioma resolvido

## Impacto Técnico
**Contrato**: campos i18n estáveis | **DB**: n/a

## Plano de Testes
- `lang` sem `version` → usa default por idioma
- `version` de idioma diferente de `lang` → comportamento documentado
