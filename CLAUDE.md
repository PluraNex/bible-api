# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
<!-- Last updated: 2026-03-28 -->

## Core Commands

### Development Setup
- `make install` - Install development dependencies
- `make dev` - Start development environment (Docker containers)
- `make docker-build` - Build Docker containers from scratch
- `make setup-repo` - Initialize repository (labels, hooks, CI)

### Daily Development
- `make ready` - Prepare code for PR (format, lint, test, generate schema)
- `make dev-cycle` - Quick development cycle (format and test only)
- `make fmt` - Format code with black and ruff
- `make lint` - Run linting checks (ruff + black check)
- `make test` - Run full test suite with pytest
- `make coverage` - Run tests with coverage report
- `make clean` - Remove Python caches and build artifacts

### Database Operations
- `make migrate` - Apply database migrations
- `make migrations` - Create new migrations
- `make db-reset` - Reset database (WARNING: destroys all data)
- `make db-shell` - Open PostgreSQL shell

### Bible Data Management (Unified System)
- `python manage.py bible status` - Check data pipeline status (926K+ verses loaded)
- `python manage.py bible migrate` - Migrate raw Bible files to organized structure
- `python manage.py bible populate` - Populate database from processed files
- `python manage.py bible populate --languages pt-BR,en-US` - Populate specific languages
- `python manage.py bible crossrefs` - Import cross references (343K+ loaded)

### API Development
- `make schema` - Generate OpenAPI schema (schema.yml)
- `make api-test` - Quick test of key API endpoints
- `make health` - Check service health status

### Testing
- `pytest tests/api/` - Test API modules
- `pytest tests/models/` - Test model modules
- `pytest -k "test_name"` - Run specific test by name
- `pytest --lf` - Run only last failed tests

### CI/CD Validation (Local)
- `make ci-all` - Run all CI checks locally
- `make ci-lint` - Run CI linting checks
- `make ci-test` - Run CI tests with coverage requirements (77% minimum)
- `make ci-schema` - Validate OpenAPI schema generation
- `make release-check` - Full release readiness check

### Docker & Debugging
- `make docker-logs` / `make logs` - Show container logs
- `make docker-shell` - Open bash shell in web container

### RAG & Vector Operations
- `make embeddings-generate` - Generate embeddings for allowed versions (requires OPENAI_API_KEY)
- `python manage.py generate_embeddings` - Generate verse embeddings for semantic search
- `python manage.py generate_unified_embeddings` - Unified embedding generation
- `python manage.py warm_embedding_cache` - Pre-cache embeddings
- `python manage.py create_vector_indexes` - Create pgvector indexes for performance

### Data Pipeline & Analysis
- `make data-setup` - Initialize data pipeline directory structure
- `make data-status` - Show data pipeline status and metrics
- `make data-cleanup` - Preview cleanup of temporary files
- `make data-pipeline` - Full pipeline: setup + status
- `make lang-analyze` - Analyze multilingual Bible files by language
- `make lang-portuguese` / `lang-english` / `lang-german` / `lang-french` - Language-specific analysis

### Observability
- `make prometheus-up` - Start Prometheus server (http://localhost:9090)
- `make grafana-up` - Start Grafana dashboard (http://localhost:3000, admin/admin)

### Documentation References
- **Architecture**: `docs/architecture/BIBLE_API_BASE_PROJECT.md`
- **Development workflow**: `docs/workflows/DEV_FLOW_PLAYBOOK.md`
- **API standards**: `docs/api/API_STANDARDS.md`
- **API testing**: `docs/api/API_TESTING_BEST_PRACTICES.md`
- **Task orchestration**: `docs/workflows/BIBLE_API_ORCHESTRATOR.md`
- **Search/RAG**: `docs/architecture/RAG_OPTIMIZATION_PLAN.md`
- **NLP integration**: `docs/architecture/NLP_INTEGRATION_PLAN.md`
- **Topics pipeline**: `docs/architecture/TOPICAL_PIPELINE_ARCHITECTURE.md`
- **Data pipeline**: `docs/data/UNIFIED_DATA_SYSTEM.md`
- **Observability**: `docs/operations/OBSERVABILITY.md`
- **Full docs index**: `docs/README.md`

## Architecture Overview

This is a Django REST Framework-based Bible API with the following key architectural patterns:

### Application Structure
- **Domain-driven design** with apps organized by biblical domain
- **Service layer pattern**: Views → Serializers → Services (write) or QuerySets/Managers (read)
- **Modular organization**: `bible/` as main app with domain-specific sub-apps
- **Centralized models**: Core models in `bible/models/` with domain-specific models in respective apps

### Django Apps

| App | Purpose |
|-----|---------|
| `bible` | Core: books, verses, versions, languages, references, cross-references |
| `bible.themes` | Biblical themes and thematic categorization |
| `bible.topics` | Topical indexing (Nave's, Torrey's) with AI enrichment |
| `bible.comments` | Legacy verse comments |
| `bible.commentaries` | Multi-source commentary system (authors, sources, entries, translations) |
| `bible.entities` | Canonical entities, aliases, roles, timelines, relationships |
| `bible.symbols` | Biblical symbols, meanings, occurrences, progressions |
| `bible.theology` | Systematic theology annotations |
| `bible.ai` | RAG system, query expansion, tool infrastructure |
| `bible.rag` | Vector embeddings, semantic search, retriever service |
| `bible.auth` | API key authentication, scope-based permissions |
| `common` | Shared utilities, observability, metrics, logging |
| `data` | Data pipeline management, unified CLI |

### API Design
- **Versioned API**: All endpoints under `/api/v1/`
- **OpenAPI/Swagger**: Auto-generated docs at `/api/v1/docs/` with `drf-spectacular`
- **Cache-first**: Strategic caching for biblical data and search endpoints
- **Rate limiting**: Scoped throttling by endpoint type (search, write, ai-run, audio, etc.)

### API Endpoints

```
/api/v1/bible/
  overview/        — Bible overview
  books/           — Books catalog
  verses/          — Verse retrieval
  themes/          — Themes domain
  topics/          — Topics domain
  cross-references/ — Cross-references
  versions/        — Bible versions
  languages/       — Language support
  references/      — Reference parsing
  comments/        — Commentary
  rag/             — RAG search

/api/v1/ai/
  agents/                    — List agents
  tools/                     — List tools
  agents/<name>/runs/        — Execute agent
  runs/<id>/approve|cancel/  — Manage runs
  rag/retrieve/              — Vector search
  rag/search/                — Full-text search
  rag/hybrid/                — Hybrid search (keyword + semantic)
  rag/similar/               — Semantic similarity
  rag/health/ | rag/stats/   — RAG observability

/api/v1/auth/
  status/    — Auth status
  register/  — Developer registration

/health/ | /health/liveness/ | /health/readiness/
/metrics/ | /metrics/prometheus/
```

### Key Domains

1. **Bible Core**: Books, verses, versions (34 versions, 926K+ verses), cross-references (343K+), languages (pt-BR, en-US)
2. **Topics & Knowledge**: Topical indexing from Nave's, Torrey's, Easton's, Smith's. AI-enriched with theme discovery and entity resolution
3. **Entities & Symbols**: Canonical entities with aliases, roles, timelines, relationships. Biblical symbols with meanings, occurrences, and progressions
4. **Commentaries**: Multi-source commentary system with authors, sources, entries, and translations. Review pipeline
5. **Search**: Hybrid search (tsquery keyword + pgvector semantic), NLP query tool for natural language, MMR diversification, configurable ranking
6. **RAG System**: OpenAI embeddings (text-embedding-3-small), pgvector storage, retriever service with multiple search modes
8. **Authentication**: API key-based auth with scope-based permissions and dynamic rate limiting
9. **Theology**: Systematic theology annotations

### Data Layer
- **PostgreSQL** as primary database (926K+ verses, 34 versions, 343K+ cross-refs)
- **pgvector** extension for semantic search with verse embeddings
- **Redis** for caching and rate limiting
- **Unified Data System**: Streamlined pipeline via `python manage.py bible` (3 commands instead of 26)
- **Multi-language**: Portuguese (pt-BR) and English (en-US) with automatic language detection

### Search Architecture
- **Hybrid search**: Combines PostgreSQL full-text search (tsquery) with pgvector semantic search
- **NLP Query Tool**: Natural language query understanding with entity recognition and dynamic alpha
- **Ranking fusion**: Configurable alpha between keyword and semantic scores
- **MMR diversification**: Maximal Marginal Relevance for result diversity
- **Query expansion**: Automatic query enrichment for better recall
- **Two-stage reranking**: Initial retrieval + reranking for precision

## Development Workflow

### Task Management
- **Always start with a TASK**: Create issues using the template in `docs/workflows/BIBLE_API_ORCHESTRATOR.md` §7
- **Track progress**: Check active tasks in `docs/tasks/INDEX.md`
- **Definition of Ready (DoR)** and **Definition of Done (DoD)** in `docs/workflows/DEV_FLOW_PLAYBOOK.md` §2
- **Vertical slice implementation**: View → Serializer → Service/Selector pattern

### Code Quality Standards
- **Conventional Commits** with scopes: `api`, `auth`, `ai`, `data`, `infra`, `docs`, `topics`, `search`, `nlp`, `rag`, `entities`, `symbols`, `theology`, `commentaries`, `resources`
- **CI Pipeline**: Lint/Format → Migrations Check → Tests → OpenAPI Schema validation
- **OpenAPI as source of truth**: Schema changes must be versioned in `docs/openapi-v1.yaml`

### Testing Requirements
- **Minimum coverage**: 77% enforced via pytest-cov
- **API contract testing**: Validate OpenAPI compliance
- **Authentication/authorization**: Test API key auth and scope-based permissions
- **Performance budgets**: Monitor N+1 queries and response times
- **Error handling**: Standardized error responses with request IDs

### Security & Performance
- **No PII in logs**: Standardized error handler prevents sensitive data exposure
- **Scoped rate limiting**: Different throttle rates for different endpoint types
- **Optimized queries**: Mandatory `select_related`/`prefetch_related` for list endpoints
- **Cache strategies**: Long-term caching for biblical data, shorter for dynamic content

## Important Files and Patterns

### Models Organization
- `bible/models/__init__.py` - Centralized imports for all core models
- Domain models in respective apps: `bible/comments/`, `bible/commentaries/`, `bible/entities/`, `bible/symbols/`, `bible/theology/`, `bible/themes/`, `bible/topics/`, `bible/ai/`
- Audit trails and soft deletes for critical data

### API Patterns
- Views inherit from DRF ViewSets/APIViews with consistent pagination
- Serializers handle validation only, business logic in Services
- Permissions use scope-based authorization via `HasAPIScopes`

### Configuration
- Settings in `config/settings.py` with environment-based overrides
- Throttle rates configured per endpoint scope
- Database: PostgreSQL + pgvector + Redis

## Development Guidelines

- **Always follow the DoR/DoD checklists** before starting and finishing tasks
- **Business logic belongs in Services**, not serializers or views
- **Use the standardized error handler** for consistent API responses
- **Generate and commit OpenAPI schema** when API contracts change
- **Write both unit and API tests** for new endpoints
- **Apply appropriate throttle scopes** based on endpoint cost/risk

## Architecture Decisions

Key architectural decisions implemented in this project:

- **Hybrid search with pgvector + tsquery fusion** for combining semantic and keyword search
- **NLP query understanding layer** for natural language processing of search queries
- **Topics pipeline from Nave's Topical Bible** with 6-phase processing (parse → enrich → discover → link → resolve → index)
- **Multi-source commentary aggregation** with Catena Aurea scraping and review pipeline
- **Canonical entity resolution** with aliases, roles, timelines, and cross-entity relationships
- **Biblical symbol tracking** with meanings, occurrences, and progressions across Scripture
- **AI tool infrastructure** with agent registry and tool execution pattern
- **Cache-first architecture** with strategic invalidation for biblical data
- **External resource aggregation** with provider abstraction
- **Canonical biblical referencing** supporting multiple versifications
- **Comprehensive audit logging** without PII exposure
