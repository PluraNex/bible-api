---
id: T-007-verses-reference-range-compare
title: "[api] Verses — By Reference, Range e Compare"
status: done
created: 2025-09-13
updated: 2025-09-13
owner: "@iuryeng"
reviewers: ["@maintainer"]
labels: ["area/api", "type/feat", "i18n", "openapi"]
priority: high
effort: M
risk: medium
depends_on: ["T-006-references-parse-normalize", "T-004-core-functional"]
related: ["T-011-versions-i18n-and-defaults"]
epic: "Fase 2: UX & Discoverability"
branch: "feat/T-007-verses-reference-range-compare"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Clientes precisam obter versículos por referência textual (não apenas por id) e comparar traduções.
- Já existe `VersesByChapterView`; falta endpoints por referência livre, por intervalo e comparação de versões.

## Objetivo e Critérios de Aceite
- [x] CA1 — `GET /api/v1/bible/verses/by-reference?ref=<str>&version=<code|id>`: retorna 1..n versículos.
- [x] CA2 — `GET /api/v1/bible/verses/range?ref=<range>&version=<code|id>`: retorna intervalo contínuo (inclusive intercapítulo).
- [x] CA3 — `GET /api/v1/bible/verses/compare?ref=<str>&versions=KJV,NVI,ARA`: retorna lista de versões com textos lado a lado (máx 5 versões).
- [x] CA4 — i18n: `lang` apenas para metadados (nomes de livros), texto controlado por `version`.
- [x] CA5 — Autenticação e escopos: `Api-Key` (`read`).
- [x] CA6 — OpenAPI: parâmetros e exemplos; responses uniformes com paginação onde fizer sentido (ListAPIView usa paginação padrão).
- [x] CA7 — Performance: `select_related("book","version")`, sem N+1; limites (300 versos máx por chamada; 413 acima).

## Escopo / Fora do Escopo
- Inclui: resolução de ref → versos, comparação de versões, paginação opcional.
- Não inclui: busca full-text (task separada), features de áudio (task própria).

## Impacto Técnico
**Contrato**: 3 novos endpoints.
**DB/Migrations**: nenhuma.
**Throttle/Cache**: `throttle_scope = "read"`; cache curto para `compare`.
**Performance**: limitar fan-out por versões (ex.: máx 5 versões).

## Plano de Testes
- 200 (refs válidas), 400 (ref inválida), 401 (sem Api-Key), 404 (livro inexistente), 413 (payload muito grande), i18n.
- Contrato: checagem OpenAPI; exemplos PT/EN.

## Observabilidade
- `Vary: Accept-Language` nos metadados.
- Métricas por endpoint.

## Rollout & Rollback
- Simples, sem migração.

## Checklist Operacional (Autor)
- [x] OpenAPI gerado/commitado.
- [x] `make fmt lint test` ok; CI verde.

## Checklist Operacional (Revisor)
- [ ] Contrato claro; limites/documentados.
- [ ] Sem N+1; bons índices usados.
- [ ] Erros padronizados e i18n.
