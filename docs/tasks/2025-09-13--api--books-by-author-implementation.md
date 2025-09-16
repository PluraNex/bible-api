---
id: T-011-books-by-author
title: "[api] Books — Implementar filtro por autor"
status: ready
created: 2025-09-13
updated: 2025-09-13
owner: "@iuryeng"
reviewers: ["@maintainer"]
labels: ["area/api", "type/feat", "i18n", "openapi"]
priority: medium
effort: S
risk: low
depends_on: ["T-004-core-functional", "T-198-authors-i18n-models"]
related: ["T-009-books-i18n-endpoints"]
epic: "Fase 2: UX & Discoverability"
branch: "feat/T-011-books-by-author"
pr: ""
github_issue: ""
due: null
---

## Contexto
- `BooksByAuthorView` retorna 501. Precisamos implementar busca por autor (considerando i18n e aliases de autores, se existirem).

## Objetivo e Critérios de Aceite
- [ ] CA1 — `GET /api/v1/bible/books/by-author/<str:author_name>/`: retorna lista de livros (ordenados por `canonical_order`).
- [ ] CA2 — i18n: nomes de livros conforme `lang` e fallback; `Vary: Accept-Language`.
- [ ] CA3 — OpenAPI: documentar `author_name` e exemplos PT/EN.

## Escopo / Fora do Escopo
- Inclui: filtro por autor a partir de metadados existentes.
- Não inclui: modelagem avançada de autores (task própria se necessário).

## Impacto Técnico
**Contrato**: endpoint já existe na rota; muda de 501 → 200/404.
**DB/Migrations**: nenhuma.

## Plano de Testes
- 200 com autor conhecido; 404/200 vazio para autor inexistente (definir contrato); 401 sem Api-Key.

## Observabilidade
- Métricas simples por chamada.

## Rollout & Rollback
- Sem migrações; simples.

## Checklist Operacional (Autor)
- [ ] `make fmt lint test` ok.
- [ ] OpenAPI atualizado.

## Checklist Operacional (Revisor)
- [ ] i18n correto e sem N+1.
- [ ] Contrato consistente com o restante de books.
