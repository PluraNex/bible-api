---
id: T-001-django-setup
title: "[api] Setup Django Project Structure — Core API Foundation"
status: ready
created: 2025-09-06
updated: 2025-09-06
owner: "@claude-agent"
reviewers: ["@maintainer"]
labels: ["area/api", "type/feat", "needs-schema"]
priority: medium
effort: M
risk: low
depends_on: ["T-000-dev-setup"]
related: []
epic: "fase-0-boot"
branch: "feat/django-project-setup"
pr: ""
due: null
---

## Contexto
- **Problema**: O projeto Bible API precisa de uma estrutura Django funcional para servir como base para toda a API
- **Valor**: Estabelece a fundação técnica que permitirá desenvolvimento incremental de todos os domínios (books, verses, themes, etc.)
- **Hipóteses**: Django REST Framework como escolha arquitetural definida; PostgreSQL como DB principal
- **Restrições**: Deve seguir a estrutura definida em `BIBLE_API_BASE_PROJECT.md`
## Objetivo e Critérios de Aceite
- [ ] CA1 — Django project criado com estrutura modular (config/, bible/, common/)
- [ ] CA2 — Apps principais configurados: bible, bible.ai, bible.apps.auth
- [ ] CA3 — URLs estruturados (/api/v1/bible/, /api/v1/ai/, /health, /metrics)
- [ ] CA4 — Models essenciais implementados (CanonicalBook, Version, Verse, APIKey)
- [ ] CA5 — DRF configurado com drf-spectacular para OpenAPI
- [ ] CA6 — Sistema de autenticação por API Key implementado
- [ ] CA7 — Health check e metrics endpoints funcionais
- [ ] CA8 — Views esqueleto funcionais (BibleOverview, Health, Metrics)

## Escopo / Fora do Escopo
**Inclui:**
- Estrutura básica do Django project (config/, bible/, common/)
- Apps principais configurados (bible, bible.ai, bible.apps.auth)
- Models **essenciais** apenas:
  - **Books**: CanonicalBook, Version (base para referências bíblicas)
  - **Content**: Verse (conteúdo principal)
  - **Auth**: APIKey (autenticação básica)
- URLs routing **estrutura** (/api/v1/bible/, /api/v1/ai/, health, metrics)
- Configuração DRF + OpenAPI (drf-spectacular)
- Authentication básica por API Key
- Health/metrics endpoints funcionais
- Settings base (development/production)

**Não inclui:**
- Models complexos (Theme, CrossReference, AI, Audio, Resources, Comments, RAG)
- Views/serializers completos (apenas esqueleto)
- Dados seed/fixtures
- Cache Redis integration
- Testes completos (apenas smoke tests)
- Deploy/infra configuration

## Impacto Técnico
**Contrato (OpenAPI)**: Novo schema será gerado com endpoints base (/api/v1/bible/, /api/v1/ai/, health, metrics)
**DB/Migrations**: Migrations iniciais para 4 models essenciais (CanonicalBook, Version, Verse, APIKey); 100% backward-compatible (projeto novo)
**Throttle/Cache**: Throttling básico configurado, cache desabilitado inicialmente
**Performance**: Orçamento p95 < 200ms para endpoints simples; índices básicos criados
**Segurança**: API Key authentication, CORS desabilitado inicialmente, sem PII em logs

## Plano de Testes
**API**:
- 200: GET /health, GET /api/v1/bible/overview/
- 401: Endpoints protegidos sem API key
- 404: Rotas inexistentes
- 200: GET /api/v1/schema/ retorna OpenAPI válido

**Contrato**: Schema gerado deve incluir todos os endpoints definidos no routing
**Dados**: Migrations aplicam sem erro; models essenciais salvam/recuperam dados corretamente

## Observabilidade
- Logs configurados (console para dev)
- Health endpoint retorna status da DB
- Metrics endpoint básico implementado
- Request ID em todas as respostas de erro

## Rollout & Rollback
**Plano de ativação:**
1. Aplicar migrations em DB local
2. Executar servidor Django
3. Verificar endpoints de health/schema

**Critérios de sucesso:**
- Health endpoint retorna 200
- Schema OpenAPI gerado sem erros
- Admin interface acessível
- Smoke tests passam

**Estratégia de reversão:**
- Rollback migrations se necessário
- Projeto novo, reversão é reset completo

## Validação Arquitetural - T-001

**✅ Conforme arquitetura BIBLE_API_BASE_PROJECT.md:**
- ✅ Modelos organizados em `bible/models/` separada
- ✅ Estrutura de apps: `bible/apps/auth/`
- ✅ URLs padrão: `/api/v1/bible/`, `/api/v1/auth/`
- ✅ Sistema de autenticação API Key customizado
- ✅ DRF + drf-spectacular configurado

**❌ Divergências identificadas e corrigidas:**
- ❌ Inicialmente criamos `CanonicalBook` (spec define `Book`)
- ❌ Modelo `Chapter` não especificado na arquitetura base
- ❌ Nomes de tabela com prefixos: `bible_books` vs `books`
- ❌ Testes não organizados hierarquicamente

**🔧 Correções aplicadas:**
- ✅ Renomeado para `Book` (sem CanonicalBook)
- ✅ Removido modelo `Chapter` (não na spec)
- ✅ Corrigidos nomes de tabela: `books`, `verses`, `versions`, `api_keys`
- ✅ Reorganizados testes: `tests/models/{books,verses,auth}/`, `tests/api/{bible,health}/`

**✋ Validação:** Arquitetura verificada e correções aplicadas ✅

## Checklist Operacional (Autor)
- [ ] OpenAPI gerado/commitado em `docs/` (primeira versão)
- [ ] `make fmt lint test` ok local (criar Makefile básico)
- [ ] CI verde (lint-and-format, migrations-check, tests, openapi-schema-check)
- [ ] PR descreve estrutura criada e próximos passos

## Checklist Operacional (Revisor)
- [ ] Estrutura de diretórios segue BIBLE_API_BASE_PROJECT.py
- [ ] Models têm constraints adequadas e relacionamentos corretos
- [ ] Settings seguem boas práticas Django (SECRET_KEY, DEBUG, etc.)
- [ ] Migrations são pequenas e aplicam sem erro
- [ ] URLs routing está organizado e RESTful
- [ ] OpenAPI schema é válido e completo
