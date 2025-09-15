# Tasks Index

## Status Legend
- 🔴 **backlog** - Definida mas não refinada
- 🟡 **ready** - Refinada e pronta para desenvolvimento
- 🔵 **in_progress** - Em desenvolvimento ativo
- 🟣 **pr_draft** - PR aberto em draft
- 🟠 **in_review** - PR em revisão
- 🟢 **merged** - Mergeado em main
- ✅ **done** - Entregue e validado

## Active Tasks

| ID | Título | Status | Assignee | Epic | Priority | GitHub Issue | Created |
|---|---|---|---|---|---|---|---|
| [T-001](./2025-09-06--api--django-project-setup.md) | Setup Django Project Structure | 🟡 ready | @iuryeng | fase-0-boot | medium | [#TBD]() | 2025-09-06 |
| [T-004](./2025-09-07--api--core-functional-implementation.md) | Core Functional Implementation — Models + Basic Endpoints | 🟡 ready | @iuryeng | fase-0-boot | high | [#TBD]() | 2025-09-07 |
| [T-015](./2025-09-07--api--error-model-polish.md) | Error Model — Polish & Consistency | ✅ done | @iuryeng | Fundação da API | [#TBD]() | 2025-09-08 |
| [T-C03](./2025-09-11--data--scraper-firecrawl-env.md) | [data] Firecrawl por ENV + validação — chave e fallback | 🔴 backlog | @iuryeng | Fase 3: Scraping Avançado de Comentários | high |  | 2025-09-11 |
| [T-C04](./2025-09-11--data--scraper-robots-and-crawl-delay.md) | [data] Respeitar robots.txt e crawl-delay — Catena | 🔴 backlog | @iuryeng | Fase 3: Scraping Avançado de Comentários | medium |  | 2025-09-11 |
| [T-C05](./2025-09-11--data--scraper-idempotent-save-by-hash.md) | [data] Salvamento idempotente por hash de conteúdo — evitar regravações | 🔴 backlog | @iuryeng | Fase 3: Scraping Avançado de Comentários | medium |  | 2025-09-11 |
| [T-C06](./2025-09-11--data--scraper-parsers-refactor-and-tests.md) | [data] Extratores separáveis + testes unitários — BS4/cleaning | 🔴 backlog | @iuryeng | Fase 3: Scraping Avançado de Comentários | medium |  | 2025-09-11 |
| [T-C07](./2025-09-11--data--scraper-observability-logs-metrics.md) | [data] Observabilidade do scraper — logs estruturados + métricas | 🔴 backlog | @iuryeng | Fase 3: Scraping Avançado de Comentários | medium |  | 2025-09-11 |
| [T-S01](./2025-09-11--infra--prod-hardening.md) | [infra] Hardening de produção — segurança e consistência transacional | 🔴 backlog | @iuryeng | Confiabilidade e Segurança | high |  | 2025-09-11 |
| [T-S02](./2025-09-11--auth--apikey-hashing-migration.md) | [auth] Hash de API Keys + migração — segurança de credenciais | 🔴 backlog | @iuryeng | Confiabilidade e Segurança | high |  | 2025-09-11 |
| [T-T01](./2025-09-11--api--scoped-throttling.md) | [api] Throttling por escopo — ScopedRateThrottle e mapeamento por rota | 🔴 backlog | @iuryeng | Confiabilidade e Segurança | high |  | 2025-09-11 |
| [T-T02](./2025-09-11--auth--dynamic-rate-limit-by-apikey.md) | [auth] Rate limit dinâmico por API Key — throttle custom | 🔴 backlog | @iuryeng | Confiabilidade e Segurança | medium |  | 2025-09-11 |
| [T-OB01](./2025-09-11--infra--logging-request-id-format.md) | [infra] Logging com request_id — formatter e ordem do middleware | 🔴 backlog | @iuryeng | Observabilidade | high |  | 2025-09-11 |
| [T-OB02](./2025-09-11--infra--prometheus-metrics-endpoint.md) | [infra] Métricas Prometheus — endpoint /metrics | 🔴 backlog | @iuryeng | Observabilidade | medium |  | 2025-09-11 |
| [T-P01](./2025-09-11--api--etag-and-cache-control.md) | [api] ETag/Last-Modified + Cache-Control em endpoints de leitura | 🔴 backlog | @iuryeng | Performance em Leitura | medium |  | 2025-09-11 |
| [T-DB01](./2025-09-11--data--postgres-fulltext-verses.md) | [data] Full-text search Postgres em Verse.text | 🔴 backlog | @iuryeng | Performance em Leitura | low |  | 2025-09-11 |
| [T-ER01](./2025-09-11--api--exceptions-specific-verses.md) | [api] Tratamento de exceções específico em Verses — remover catch amplo | 🔴 backlog | @iuryeng | Qualidade de Erros | medium |  | 2025-09-11 |
| [T-DP01](./2025-09-11--infra--deploy-gunicorn-whitenoise.md) | [infra] Deploy com Gunicorn + Whitenoise — substituir runserver | 🔴 backlog | @iuryeng | Confiabilidade e Segurança | high |  | 2025-09-11 |
| [T-AI01](./2025-09-11--ai--scopes-and-throttling.md) | [ai] Escopos e throttling em endpoints de AI | 🔴 backlog | @iuryeng | Confiabilidade e Segurança | medium |  | 2025-09-11 |
| [T-TS01](./2025-09-11--tests--smoke-and-openapi-contract.md) | [tests] Smoke tests + contrato OpenAPI | 🔴 backlog | @iuryeng | Qualidade e Confiabilidade | high |  | 2025-09-11 |
| [T-TS02](./2025-09-11--tests--auth-hash-mode-updates.md) | [tests] Atualizar suite de auth para modo hash de API Keys | 🔴 backlog | @iuryeng | Qualidade e Confiabilidade | high |  | 2025-09-11 |
| [T-DX01](./2025-09-11--docs--auth-scopes-and-limits.md) | [docs] Atualizar README/OpenAPI — escopos, limites e exemplos | 🔴 backlog | @iuryeng | DX & Documentação | low |  | 2025-09-11 |
| [T-DOC01](./2025-09-11--docs--api-standards.md) | [docs] Padrões de API — guia oficial (versionamento, auth, erros, i18n, cache) | 🔴 backlog | @iuryeng | DX & Documentação | high |  | 2025-09-11 |
| [T-I18N01](./2025-09-11--api--language-negotiation-and-resolver.md) | [api] Negociação de idioma (Accept-Language/lang) + resolver central | 🟡 ready | @iuryeng | I18N — Suporte Multilíngue | high |  | 2025-09-11 |
| [T-I18N02](./2025-09-11--api--books-i18n-endpoints.md) | [api] Books: suporte a i18n — param lang, serializers e busca por idioma | 🔴 backlog | @iuryeng | I18N — Suporte Multilíngue | high |  | 2025-09-11 |
| [T-I18N03](./2025-09-11--api--verses-i18n-endpoints.md) | [api] Verses: suporte a i18n — display_name e seleção por versão/idioma | 🔴 backlog | @iuryeng | I18N — Suporte Multilíngue | high |  | 2025-09-11 |
| [T-I18N04](./2025-09-11--api--versions-i18n-and-defaults.md) | [api] Versions: filtros por código/idioma e endpoint de default por idioma | 🔴 backlog | @iuryeng | I18N — Suporte Multilíngue | medium |  | 2025-09-11 |
| [T-I18N05](./2025-09-11--docs--openapi-i18n-docs.md) | [docs] OpenAPI: documentar i18n — params lang e negociação | 🔴 backlog | @iuryeng | I18N — Suporte Multilíngue | medium |  | 2025-09-11 |
| [T-I18N06](./2025-09-11--tests--i18n-suite.md) | [tests] Suíte de i18n — books/verses/versions com lang e Accept-Language | 🔴 backlog | @iuryeng | I18N — Suporte Multilíngue | high |  | 2025-09-11 |
| [T-I18N07](./2025-09-11--infra--cache-vary-accept-language.md) | [infra] Cache e ETag variando por idioma — Vary: Accept-Language/lang | 🔴 backlog | @iuryeng | I18N — Suporte Multilíngue | medium |  | 2025-09-11 |
| [T-I18N08](./2025-09-11--data--seed-multilang-booknames.md) | [data] Garantir seed com BookName multilíngue e coerente com versions | 🔴 backlog | @iuryeng | I18N — Suporte Multilíngue | medium |  | 2025-09-11 |
| [T-I18N09](./2025-09-11--data--authors-i18n-models.md) | [data] Autores: modelos de tradução — nomes, apelidos e biografia | 🔴 backlog | @iuryeng | I18N — Suporte Multilíngue | high |  | 2025-09-11 |
| [T-I18N10](./2025-09-11--api--authors-i18n-endpoints.md) | [api] Autores: endpoints i18n — nomes/bio por lang e busca multilíngue | 🔴 backlog | @iuryeng | I18N — Suporte Multilíngue | high |  | 2025-09-11 |
| [T-I18N11](./2025-09-11--data--commentary-sources-i18n-models.md) | [data] Fontes de comentário: i18n — nomes e descrições por idioma | 🔴 backlog | @iuryeng | I18N — Suporte Multilíngue | medium |  | 2025-09-11 |
| [T-I18N12](./2025-09-11--api--commentary-i18n-endpoints.md) | [api] Comentários: i18n — título/texto e fallback por idioma | 🔴 backlog | @iuryeng | I18N — Suporte Multilíngue | medium |  | 2025-09-11 |
| [T-I18N13](./2025-09-11--tests--authors-and-commentary-i18n.md) | [tests] Autores e Comentários — testes de i18n (lang/fallback/busca) | 🔴 backlog | @iuryeng | I18N — Suporte Multilíngue | high |  | 2025-09-11 |
| [T-I18N14](./2025-09-11--api--languages-endpoint.md) | [api] Endpoint de idiomas — listar e filtrar Languages | 🔴 backlog | @iuryeng | I18N — Suporte Multilíngue | medium |  | 2025-09-11 |
| [T-I18N15](./2025-09-11--data--language-standardization.md) | [data] Padronização de Language — ISO, seeds e validações | 🔴 backlog | @iuryeng | I18N — Suporte Multilíngue | medium |  | 2025-09-11 |
| [T-I18N16](./2025-09-11--api--i18n-refactor-remove-hardcoded-en.md) | [api] Refactor i18n — remover hardcodes 'en', usar request.lang_code e documentar lang | 🔴 backlog | @iuryeng | I18N — Suporte Multilíngue | high |  | 2025-09-11 |
| [T-I18N17](./2025-09-12--data--i18n-expansion-readiness.md) | [data] I18N — Readiness para expansão de idiomas (bases ISO, defaults e checks) | 🔴 backlog | @iuryeng | I18N — Suporte Multilíngue | high |  | 2025-09-12 |
| [T-I18N18](./2025-09-12--data--i18n-defaults-audit-and-flags.md) | [data] I18N — Auditoria de defaults (pendências, JSON e flags) | 🔴 backlog | @iuryeng | I18N — Suporte Multilíngue | high |  | 2025-09-12 |
| [T-DATA-003](./2025-09-13--data--unified-cli-system-manifest-driven.md) | [data] CLI System — Sistema unificado com configuração por manifesto | 🟡 ready | @iuryeng | Pipeline de Dados | high |  | 2025-09-13 |
| [T-DATA-004](./2025-09-13--data--migration-system-dataset-reorganization.md) | [data] Migration System — Engine de reorganização de datasets | 🟡 ready | @iuryeng | Pipeline de Dados | high |  | 2025-09-13 |
| [T-DATA-005](./2025-09-13--data--observability-lineage-tracking-reporting.md) | [data] Observability — Lineage tracking e sistema de relatórios | 🟡 ready | @iuryeng | Pipeline de Dados | medium |  | 2025-09-13 |
| [T-DATA-006](./2025-09-13--data--automated-maintenance-integrity-verification.md) | [data] Maintenance — Sistema automatizado de integridade e limpeza | 🟡 ready | @iuryeng | Pipeline de Dados | medium |  | 2025-09-13 |
| [T-DATA-007](./2025-09-13--data--execution-complete-migration-validation.md) | [data] Execution — Migração completa e validação dos datasets | 🟡 ready | @iuryeng | Pipeline de Dados | high |  | 2025-09-13 |
<!-- T-ARCH removed: Architecture Alignment Refactor (task deprecated) -->
## Completed Tasks
| ID | Título | Status | Assignee | Epic | GitHub Issue | Completed |
|---|---|---|---|---|---|---|
| [T-000](./2025-09-06--infra--dev-environment-setup.md) | Setup Development Environment | ✅ done | @iuryeng | fase-0-boot | [#1](https://github.com/PluraNex/bible-api/issues/1) | 2025-09-06 |
| [T-002](./2025-09-06--infra--quality-tools-integration.md) | Quality Tools Integration | ✅ done | @iuryeng | fase-0-boot | [#3](https://github.com/PluraNex/bible-api/issues/3) / [PR#4](https://github.com/PluraNex/bible-api/pull/4) | 2025-09-06 |
| [T-003](./2025-09-07--ai--ai-module-scaffold-hardening.md) | AI module scaffold hardening — Auth, Docs, Tests | ✅ done | @iuryeng | fase-0-boot | medium | [#TBD]() | 2025-09-07 |
| T-007 | Versions API Implementation | ✅ done | @iuryeng | fundacao-api | [PR#15](https://github.com/PluraNex/bible-api/pull/15) | 2025-09-07 |
| T-012 | HasAPIScopes Permission System | ✅ done | @iuryeng | fundacao-api | [PR#15](https://github.com/PluraNex/bible-api/pull/15) | 2025-09-07 |
| [T-014](./2025-09-07--api--error-model-standardization.md) | Error Model Standardization | ✅ done | @iuryeng | Fundação da API | [PR#TBD]() | 2025-09-08 |
| [T-DATA-001](./2025-09-13--data--infrastructure-pipeline-directory-structure.md) | [data] Infrastructure — Estrutura de diretórios e utilitários de governança | ✅ done | @iuryeng | Pipeline de Dados | [#TBD]() | 2025-09-13 |
| [T-DATA-002](./2025-09-13--data--language-detection-multilingual-classification.md) | [data] Language Detection — Sistema de classificação multilíngue para Bíblias | ✅ done | @iuryeng | Pipeline de Dados | [#TBD]() | 2025-09-13 |

## Novas Tasks (2025-09-13)

| ID | Título | Status | Assignee | Epic | Priority | Created |
|---|---|---|---|---|---|---|
| [T-006](./2025-09-13--api--references-parse-and-normalize.md) | [api] Referências — Parse, Resolve e Normalize | ✅ done | @iuryeng | UX & Discoverability | high | 2025-09-13 |
| [T-007](./2025-09-13--api--verses-by-reference-range-compare.md) | [api] Verses — By Reference, Range e Compare | ✅ done | @iuryeng | UX & Discoverability | high | 2025-09-13 |
| [T-008](./2025-09-13--auth--api-keys-management-and-usage.md) | [auth] API Keys — Gestão, Uso e Rate-Limits | 🟡 ready | @iuryeng | Segurança & Governança | high | 2025-09-13 |
| [T-009](./2025-09-13--infra--health-readiness-and-metrics.md) | [infra] Health — Liveness, Readiness e Métricas | ✅ done | @iuryeng | Observabilidade | medium | 2025-09-13 |
| [T-010](./2025-09-13--api--crossrefs-model-and-endpoints-fix.md) | [api] Cross-References — Ajustes de Modelo e Endpoints | ✅ done | @iuryeng | UX & Discoverability | medium | 2025-09-13 |
| [T-011](./2025-09-13--api--books-by-author-implementation.md) | [api] Books — Implementar filtro por autor | 🟡 ready | @iuryeng | UX & Discoverability | medium | 2025-09-13 |

## Task Statistics
 - **Total**: 20
 - **Ready**: 11 (inclui T-RAG01..06)
 - **In Progress**: 0
 - **Completed**: 9

---
**Last Updated**: 2025-09-13

| [T-RAG07](./rag/2025-09-14--rag--07-simple-eval-endpoint.md) | [rag] Eval simples � endpoint de teste (retrieval-only) | ?? ready | @iuryeng | RAG + Agents | medium | 2025-09-14 |
| [T-RAG01](./rag/2025-09-13--rag--01-embeddings-and-pgvector.md) | [rag] Embeddings + pgvector — schema, índices e scripts | 🟡 ready | @iuryeng | RAG + Agents | high | 2025-09-13 |
| [T-RAG02](./rag/2025-09-13--rag--02-retriever-service-and-api.md) | [rag] Retriever Service + API (/rag/retrieve) | 🟡 ready | @iuryeng | RAG + Agents | high | 2025-09-13 |
| [T-RAG03](./rag/2025-09-13--rag--03-version-policy-and-governance.md) | [rag] Política de Versões — enabled_for_rag, ai_allowed, embedding_ready | 🟡 ready | @iuryeng | RAG + Agents | medium | 2025-09-13 |
| [T-RAG04](./rag/2025-09-13--rag--04-xrefs-suggest-approve-feedback.md) | [rag+ai] Cross-Refs — suggest/approve/feedback | 🟡 ready | @iuryeng | RAG + Agents | high | 2025-09-13 |
| [T-RAG05](./rag/2025-09-13--rag--05-explain-and-guardrails.md) | [ai] Explain + Guardrails — prompts, limites e observabilidade | 🟡 ready | @iuryeng | RAG + Agents | medium | 2025-09-13 |
| [T-RAG06](./rag/2025-09-13--rag--06-observability-and-dashboards.md) | [rag+ai] Observabilidade — métricas e dashboards | 🟡 ready | @iuryeng | RAG + Agents | medium | 2025-09-13 |
