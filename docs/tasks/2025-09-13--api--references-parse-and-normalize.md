---
id: T-006-references-parse-normalize
title: "[api] Referências — Parse, Resolve e Normalize"
status: done            # backlog | ready | in_progress | pr_draft | in_review | merged | done
created: 2025-09-13
updated: 2025-09-13
owner: "@iuryeng"
reviewers: ["@maintainer"]
labels: ["area/api", "type/feat", "i18n", "openapi", "no-db"]
priority: high
effort: M
risk: medium
depends_on: ["T-004-core-functional", "T-005-url-domain-refactor", "T-197-language-negotiation-and-resolver"]
related: ["T-007-verses-reference-range-compare"]
epic: "Fase 2: UX & Discoverability"
branch: "feat/T-006-references-parse-normalize"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Clientes precisam enviar referências livres (ex.: "Jo 3:16-18; 1Co 13") e obter forma canônica consistente.
- Hoje não há endpoints dedicados para parse/normalize/resolve de referências multi-idioma.
- Valor: diminui erro do cliente, padroniza consumo e permite caching eficiente.

## Objetivo e Critérios de Aceite
- [x] CA1 — `GET /api/v1/bible/references/parse?q=<string>`: retorna tokens, ranges e eventuais warnings/erros.
- [x] CA2 — `POST /api/v1/bible/references/resolve` (lista de strings): retorna estrutura canônica (book, chapter, verse_start, verse_end) com identificação do livro e osis_code.
- [x] CA3 — `POST /api/v1/bible/references/normalize`: normaliza nomes/abreviações de livros, respeitando `lang`.
- [x] CA4 — i18n: respeitar `lang` (query) e fallback `Accept-Language`; `Vary: Accept-Language` quando aplicável.
- [x] CA5 — Autenticação: `Api-Key` obrigatória (escopo `read`), respostas 401 padronizadas.
- [x] CA6 — OpenAPI completo: parâmetros, exemplos PT/EN, erros padronizados.
- [x] CA7 — Performance: sem N+1; uso de caches em nível de normalização (apelidos de livros).

## Escopo / Fora do Escopo
- Inclui: normalização/parse/resolve sem acessar texto bíblico.
- Não inclui: busca de versículos ou comparação de versões (coberto em T-007).

## Impacto Técnico
**Contrato (OpenAPI)**: novos 3 endpoints; sem breaking.
**DB/Migrations**: nenhuma (usa metadados existentes `CanonicalBook`, `BookName`).
**Throttle/Cache**: `throttle_scope = "search"`; cache curto (ex.: 5–30 min) por input normalizado.
**Performance**: O(padrões) por referência; pré-carregar mapa de aliases por idioma.
**Segurança**: sem PII; validar tamanho do input e recusar payloads excessivos (413/400).

## Plano de Testes
**API**: 200 (inputs válidos), 400 (sintaxe inválida), 401 (sem Api-Key), 422 (inconsistências), i18n (pt,en).
**Contrato**: schema válido, exemplos PT/EN.
**Dados**: fixtures mínimas de `BookName` multi-idioma.

## Observabilidade
- Incluir `X-Request-ID` nos logs.
- Contadores por status-code e latência (aproveitar /metrics).

## Rollout & Rollback
- Ativação: deploy sem migrações; invalidar cache de aliases se existir.
- Sucesso: clientes conseguem converter referências de forma consistente.
- Reversão: remover rotas; sem impacto em dados.

## Checklist Operacional (Autor)
- [x] OpenAPI gerado/commitado.
- [x] make ready  # fmt, lint, test, schema
- [x] make api-test  # smoke dos principais endpoints
- [x] CI verde.

## Checklist Operacional (Revisor)
- [ ] Contrato claro, exemplos bons, i18n correto.
- [ ] Performance adequada e sem N+1.
- [ ] Erros no padrão `{detail, code, request_id}`.
