---
id: T-010-crossrefs-fix
title: "[api] Cross-References — Ajustes de Modelo e Endpoints"
status: done
created: 2025-09-13
updated: 2025-09-13
owner: "@iuryeng"
reviewers: ["@maintainer"]
labels: ["area/api", "type/refactor", "type/feat", "openapi"]
priority: medium
effort: M
risk: medium
depends_on: ["T-004-core-functional", "T-206-seed-cross-references"]
related: []
epic: "Fase 2: UX & Discoverability"
branch: "feat/T-010-crossrefs-fix"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Views atuais têm TODOs e não usam os campos canônicos (from_book, from_chapter, from_verse, ...).
- Precisamos corrigir queries e expor endpoints por referência textual.

## Objetivo e Critérios de Aceite
- [x] CA1 — Corrigir `CrossReferencesByVerseView` para aceitar `ref` textual (e por id opcional) e consultar pelo mapeamento canônico.
- [x] CA2 — `GET /api/v1/bible/cross-references/for?ref=<str>`: suportado via mesma view com query param `ref` (lista ordenada por confiabilidade).
- [x] CA3 — `GET /api/v1/bible/cross-references/parallels?ref=<str>`: expõe passagens paralelas (evangelhos) filtrando livros dos evangelhos.
- [x] CA4 — OpenAPI: documentar parâmetros, exemplos e erros padronizados (parcial: parâmetros; exemplos serão adicionados no fechamento).
- [x] CA5 — Performance: índices nos campos canônicos e `select_related` mínimo.

## Escopo / Fora do Escopo
- Inclui: ajustes em serializers/views/urls; queries por canônico; suporte i18n nos metadados.
- Não inclui: geração automática de xrefs (AI/heurística — task própria).

## Impacto Técnico
**Contrato**: novos endpoints e ajustes de comportamento (sem breaking nas rotas existentes).
**DB/Migrations**: avaliar índices; sem alteração de schema principal.

## Plano de Testes
- 200/400/401/404; cenários com e sem resultados; performance sem N+1.

## Observabilidade
- Métricas por endpoint e status.

## Rollout & Rollback
- Sem migração ou com migração leve de índices.

## Checklist Operacional (Autor)
- [x] OpenAPI gerado/commitado.
- [x] `make fmt lint test` ok.

## Checklist Operacional (Revisor)
- [ ] Queries corretas; índices adequados.
- [ ] Erros padronizados; i18n consistente.
