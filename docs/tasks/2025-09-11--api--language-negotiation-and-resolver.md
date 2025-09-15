---
id: T-I18N01
title: "[api] Negociação de idioma (Accept-Language/lang) + resolver central"
status: done
created: 2025-09-11
updated: 2025-09-13
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/api", "type/feat", "i18n"]
priority: high
effort: S
risk: low
depends_on: []
related: ["T-I18N02", "T-I18N03", "T-I18N04"]
epic: "I18N — Suporte Multilíngue"
branch: "feat/i18n-language-negotiation"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Precisamos suportar múltiplos idiomas usando `Accept-Language` e/ou query `lang`.
- Centralizar a resolução de idioma para ser usada por todas as views/serializers.
 - Alinha com `docs/API_STANDARDS.md §6 (i18n)`.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Implementar util `resolve_language(request)` com prioridade: `lang` param > `Accept-Language` > default (`en`)
- [ ] CA2 — Validar idioma contra tabela `Language` (fallback para `en` se desconhecido)
- [ ] CA3 — Tornar idioma resolvido acessível via `request.lang_code`
- [ ] CA4 — Documentar comportamento e exemplos

## Escopo / Fora do Escopo
- Inclui: util/middleware leve, integração básica nas views principais
- Não inclui: criação de modelos i18n (autores/comentários), será feito em tasks próprias

## Impacto Técnico
**Contrato**: novo query param `lang` (opcional) | **Segurança**: n/a | **Performance**: mínima

## Plano de Testes
- Requests com `lang=pt`, `Accept-Language: pt`, ambos, e inválidos

## Observabilidade
- Adicionar `Vary: Accept-Language` nos endpoints sensíveis a idioma

## Rollout & Rollback
- Rollout incremental em endpoints de leitura
- Rollback simples (remover util e referências)

## Checklist Operacional (Autor)
- [ ] `resolve_language` implementado e coberto por testes
- [ ] Endpoints principais usam `request.lang_code`
- [ ] OpenAPI com `OpenApiParameter(lang)`

## Checklist Operacional (Revisor)
- [ ] Precedência e fallback corretos
- [ ] Sem regressões nos endpoints existentes
