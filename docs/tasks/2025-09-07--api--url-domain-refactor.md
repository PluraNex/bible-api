---
id: T-005-url-domain-refactor
title: "[refactor] URL Domain Organization — Move URLs to Domain Apps"
status: backlog            # backlog | ready | in_progress | pr_draft | in_review | merged | done
created: 2025-09-07
updated: 2025-09-07
owner: "@iuryeng"
reviewers: ["@maintainer"]
labels: ["area/api", "type/refactor"]
priority: medium
effort: S
risk: low
depends_on: ["T-004-core-functional"]
related: []
epic: "Fase 1: Core Funcional"
branch: "refactor/T-005-url-domain-refactor"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Atualmente `bible/urls.py` centraliza imports e definição de rotas de múltiplos domínios (books, verses, themes, crossrefs), o que dificulta a escalabilidade.
- A arquitetura base prevê organização por domínio, com `urls.py` específico em cada pacote.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Criar `bible/books/urls.py` com rotas do domínio Books.
- [ ] CA2 — Criar `bible/verses/urls.py` com rotas do domínio Verses.
- [ ] CA3 — Criar `bible/themes/urls.py` com rotas do domínio Themes.
- [ ] CA4 — Criar `bible/crossrefs/urls.py` com rotas do domínio Cross-References.
- [ ] CA5 — Refatorar `bible/urls.py` para apenas `overview/` e `include()` dos domínios.
- [ ] CA6 — Manter nomes de rotas e paths exatamente como no contrato atual (sem breaking change).
- [ ] CA7 — Atualizar testes para importarem views via URLs por domínio, mantendo os mesmos endpoints.
- [ ] CA8 — OpenAPI continua gerando o mesmo conjunto de paths; CI verde.

## Escopo / Fora do Escopo
- Inclui: movimentação de rotas para arquivos por domínio; atualização mínima de imports.
- Não inclui: criação de novos endpoints, alterações de contrato, mudanças em views/serializers.

## Impacto Técnico
- Contrato (OpenAPI): inalterado.
- DB/Migrations: nenhuma.
- CI: deve permanecer verde (lint/black/tests/schema).

## Plano de Implementação
1) Criar `urls.py` por domínio, movendo as rotas existentes.
2) Ajustar `bible/urls.py` para `include()` por domínio.
3) Rodar `make ready` (fmt, lint, test, schema).
4) Abrir PR em `refactor/T-005-url-domain-refactor`.

## Plano de Testes
- Smoke: acessar rotas antigas e verificar 200/401/404 conforme testes existentes.
- OpenAPI: verificar contagem de paths e nomes.

## Observabilidade
- Sem alterações.

## Rollout & Rollback
- Rollout: merge simples sem downtime.
- Rollback: revert commit (sem impacto em dados).

## Checklist Operacional (Autor)
- [ ] `make fmt lint test` ok
- [ ] OpenAPI gerado e válido
- [ ] PR com descrição do refactor

## Checklist Operacional (Revisor)
- [ ] Sem alteração de contrato ou nomes de rotas
- [ ] Testes continuam passando
- [ ] Estrutura por domínio conforme arquitetura
