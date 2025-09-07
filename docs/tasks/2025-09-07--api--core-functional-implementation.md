---
id: T-004-core-functional
title: "[api] Core Functional Implementation — Models + Basic Endpoints"
status: ready            # backlog | ready | in_progress | pr_draft | in_review | merged | done
created: 2025-09-07
updated: 2025-09-07
owner: "@iuryeng"
reviewers: ["@maintainer"]
labels: ["area/api", "type/feat", "type/model", "type/test", "needs-migration", "needs-schema"]
priority: high             # low | medium | high | urgent
effort: L                  # XS | S | M | L | XL
risk: medium               # low | medium | high
depends_on: ["T-003-ai-scaffold-hardening"]
related: []
epic: "Fase 1: Core Funcional"
branch: "feat/T-004-core-functional"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Models básicos existem (Book, Verse, Version) mas faltam modelos essenciais (Theme, CrossReference)
- Endpoints atuais: apenas overview (bible), auth status, AI scaffold endurecido (auth + docs + tests)
- Arquitetura prevê +50 endpoints, gap de 90% nos endpoints core
- Valor: criar base funcional mínima para consumo da API bíblica

## Objetivo e Critérios de Aceite
- [ ] CA1 — Models: implementar `Theme` e `CrossReference` com relacionamentos adequados
- [ ] CA2 — Migrations: criar migrações com constraints, indexes de performance e fixtures básicas
- [ ] CA3 — Endpoints books (sob /api/v1/bible/): `GET /books/`, `GET /books/<str:book_name>/chapters/`, `GET /books/<str:book_name>/info/`
- [ ] CA4 — Endpoints verses (sob /api/v1/bible/): `GET /verses/by-chapter/<str:book_name>/<int:chapter>/`, `GET /verses/{id}/`
- [ ] CA5 — Endpoints themes (sob /api/v1/bible/): `GET /themes/`, `GET /themes/<int:theme_id>/detail/`
- [ ] CA6 — Endpoints cross-references: `GET /cross-references/verse/<int:verse_id>/` (leitura básica)
- [ ] CA7 — Serializers: implementar com validação e campos otimizados (select_related/prefetch_related)
- [ ] CA8 — Documentação OpenAPI: todos endpoints com @extend_schema (summaries, responses, examples)
- [ ] CA9 — Autenticação: endpoints protegidos por API Key (401 sem credencial)
- [ ] CA10 — Testes API: cobertura de auth (401/200), validação de dados, performance (N+1 queries)
- [ ] CA11 — Fixtures: dados mínimos (3-5 livros, alguns versículos, temas básicos) para desenvolvimento
- [ ] CA12 — Schema OpenAPI: gerar e commitar docs/openapi-v1.yaml atualizado
- [ ] CA13 — Nomes de rotas seguem o padrão da arquitetura (ex.: `books_list`, `book_chapters`, `book_info`, `verses_by_chapter`, `theme_detail`, `themes_list`)

## Escopo / Fora do Escopo
- Inclui: models Theme/CrossReference, endpoints básicos de leitura (não CRUD), serializers otimizados, testes de contrato
- Não inclui: busca avançada, audio/TTS, recursos externos, funcionalidades AI específicas, endpoints complexos (statistics, tools), operações de escrita (conteúdo canônico)

## Impacto Técnico
- Contrato (OpenAPI): novos endpoints com responses padronizados, sem breaking changes
- DB/Migrations:
  - Novas tabelas `themes`, `cross_references` com FKs e índices
  - CrossReference constraints: unicidade por (`from_verse`, `to_verse`, `source`); proibir self-reference; se direção não importar, normalizar par (menor→maior)
  - Índices: por `from_verse`, `to_verse` e opcional por `relationship_type`
- Performance: queries otimizadas obrigatórias com select_related/prefetch_related
- Autenticação: manter padrão APIKey existente

## Plano de Implementação
1. **Models & DB**:
   - Implementar `Theme` (name, description, color, icon)
   - Implementar `CrossReference` (from_verse, to_verse, relationship_type)
   - Migrations com constraints e indexes
   - Fixtures básicas (Genesis 1:1-10, alguns temas como "Creation", "Love")

2. **Serializers**:
   - `BookSerializer`, `VerseSerializer`, `ThemeSerializer`
   - Otimizações de query (select_related/prefetch_related)
   - Campos calculados (verse_count, chapter_count)

3. **Views & URLs**:
   - Class-based views com `path()` e rotas explícitas conforme arquitetura
   - Apenas operações de leitura (sem CRUD — conteúdo canônico)
   - Nomes de rotas seguindo padrão: `books_list`, `book_chapters`, `book_info`, `verses_by_chapter`, `themes_list`, `theme_detail`
   - Filtros básicos (por livro, capítulo)
   - Paginação padrão

4. **Testes**:
   - Testes de modelo (validações, relacionamentos)
   - Testes API (auth, dados, performance)
   - Fixtures para testes

## Plano de Testes
- Models: validações de constraints, relacionamentos ForeignKey
- API: 
  - 401: todos endpoints sem `Api-Key`
  - 200: endpoints list/detail com dados válidos
  - 404: recursos não encontrados
  - Performance: verificar ausência de N+1 queries
- Contrato: schema OpenAPI válido
- Fixtures: dados carregados corretamente (para dev); testes usam fábricas/setup para determinismo

## Observabilidade
- Logs padrão para operações de leitura
- Métricas de performance (query count, response time)
- Responses determinísticas com IDs consistentes

## Rollout & Rollback
- Ativação: aplicar migrations, carregar fixtures, rodar testes
- Sucesso: endpoints funcionais, schema atualizado, CI verde
- Reversão: rollback migrations, sem impacto em dados existentes

## Checklist Operacional (Autor)
- [ ] Migrations aplicadas e testadas localmente
- [ ] Fixtures carregadas sem erros
- [ ] OpenAPI gerado/commitado em `docs/openapi-v1.yaml` (schema atualizado com novos endpoints)
- [ ] `make fmt lint test` ok local
- [ ] CI verde (lint, migrations-check, tests, schema-diff)
- [ ] Cobertura de testes adequada (>80% nos novos arquivos)

## Checklist Operacional (Revisor)
- [ ] Models seguem padrões Django (Meta, __str__, relacionamentos)
- [ ] Serializers otimizados (sem N+1 queries)
- [ ] Views seguem padrão DRF com class-based views + `path()` e rotas explícitas; permissions/pagination corretas
- [ ] Testes abrangentes e determinísticos
- [ ] OpenAPI bem documentado (summaries, examples)
- [ ] Performance adequada (queries otimizadas)
