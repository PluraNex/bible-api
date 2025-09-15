# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Commands

### Development Setup
- `make install` - Install development dependencies
- `make dev` - Start development environment (Docker containers)
- `make docker-build` - Build Docker containers from scratch

### Daily Development
- `make ready` - Prepare code for PR (format, lint, test, generate schema)
- `make dev-cycle` - Quick development cycle (format and test only)
- `make fmt` - Format code with black and ruff
- `make lint` - Run linting checks (ruff + black check)
- `make test` - Run full test suite with pytest
- `make coverage` - Run tests with coverage report

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

### Testing Specific Components
- `pytest tests/api/` - Test specific API modules
- `pytest tests/models/` - Test specific model modules
- `pytest -k "test_name"` - Run specific test by name
- `pytest --lf` - Run only last failed tests

### CI/CD Validation (Local)
- `make ci-all` - Run all CI checks locally
- `make ci-lint` - Run CI linting checks
- `make ci-test` - Run CI tests with coverage requirements
- `make ci-schema` - Validate OpenAPI schema generation

### Docker & Debugging
- `make docker-logs` - Show all container logs
- `make logs-web` - Show Django application logs only
- `make docker-shell` - Open bash shell in web container

### RAG & Vector Operations
- `python manage.py generate_embeddings` - Generate verse embeddings for semantic search
- `python manage.py create_vector_indexes` - Create pgvector indexes for performance
- `make embeddings-generate` - Generate embeddings for allowed versions (requires OPENAI_API_KEY)

### Data Pipeline & Analysis
- `make data-setup` - Initialize data pipeline directory structure
- `make data-status` - Show data pipeline status and metrics
- `make lang-analyze` - Analyze multilingual Bible files by language
- `make lang-validate` - Validate language detection accuracy

### Observability
- `make prometheus-up` - Start Prometheus server (http://localhost:9090)
- `make grafana-up` - Start Grafana dashboard (http://localhost:3000, admin/admin)

### Documentation References
- **Architecture guide**: `docs/architecture/BIBLE_API_BASE_PROJECT.md`
- **Development workflow**: `docs/workflows/DEV_FLOW_PLAYBOOK.md`
- **API testing standards**: `docs/api/API_TESTING_BEST_PRACTICES.md`
- **Task orchestration**: `docs/workflows/BIBLE_API_ORCHESTRATOR.md`

## Architecture Overview

This is a Django REST Framework-based Bible API with the following key architectural patterns:

### Application Structure
- **Domain-driven design** with apps organized by business domain
- **Service layer pattern**: Views → Serializers → Services (write operations) or direct to QuerySets/Managers (read operations)
- **Modular organization**: `bible/apps/` contains domain-specific applications (auth, audio, resources)
- **Centralized models**: Core models in `bible/models/` with domain-specific models in respective apps

### API Design
- **Versioned API**: All endpoints under `/api/v1/`
- **OpenAPI/Swagger**: Automatically generated documentation with `drf-spectacular`
- **Cache-first architecture**: Strategic caching for biblical data and search endpoints
- **Rate limiting**: Scoped throttling by endpoint type (search, write, ai-run, audio, etc.)

### Key Domains
1. **Bible Core**: Books, verses, themes, cross-references
2. **Authentication**: API key-based auth with scope-based permissions
3. **AI Integration**: Agent registry with tool execution and approval workflows
4. **RAG System**: Vector embeddings with semantic search (VerseEmbedding model)
5. **References**: Biblical reference parsing and normalization
6. **Languages**: Multi-language support with automatic detection

### Data Layer
- **PostgreSQL** as primary database (926K+ verses, 34 versions, 343K+ cross-refs)
- **pgvector** extension for semantic search with verse embeddings
- **Redis** for caching and rate limiting
- **Strategic indexing** for biblical reference lookups
- **Constraint-enforced data integrity** at database level
- **Unified Data System**: Streamlined data pipeline via `python manage.py bible` commands
- **Multi-language support**: Portuguese (pt-BR) and English (en-US) with automatic language detection
- **RAG capabilities**: OpenAI embeddings for semantic verse search

## Development Workflow

### Task Management
- **Always start with a TASK**: Create issues using the template in `docs/workflows/BIBLE_API_ORCHESTRATOR.md` §7
- **Track progress**: Check active tasks in `docs/tasks/INDEX.md`
- **Definition of Ready (DoR)** and **Definition of Done (DoD)** in `docs/workflows/DEV_FLOW_PLAYBOOK.md` §2
- **Vertical slice implementation**: View → Serializer → Service/Selector pattern

### Code Quality Standards
- **Conventional Commits** with scopes: `api`, `auth`, `audio`, `ai`, `resources`, `infra`, `docs`
- **CI Pipeline**: Lint/Format → Migrations Check → Tests → OpenAPI Schema validation
- **OpenAPI as source of truth**: Schema changes must be versioned in `docs/openapi-v1.yaml`

### Testing Requirements
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
- `bible/models/__init__.py` - Centralized imports for all models
- Domain models follow canonical biblical structure with versification support
- Audit trails and soft deletes for critical data

### API Patterns
- Views inherit from DRF ViewSets/APIViews with consistent pagination
- Serializers handle validation only, business logic in Services
- Permissions use scope-based authorization via `HasAPIScopes`

### Configuration
- Settings in `config/settings.py` with environment-based overrides
- Audio/TTS configuration for multiple providers (AWS Polly, Google TTS, etc.)
- Throttle rates configured per endpoint scope

## Development Guidelines

- **Always follow the DoR/DoD checklists** before starting and finishing tasks
- **Business logic belongs in Services**, not serializers or views
- **Use the standardized error handler** for consistent API responses
- **Generate and commit OpenAPI schema** when API contracts change
- **Write both unit and API tests** for new endpoints
- **Apply appropriate throttle scopes** based on endpoint cost/risk

## Architecture Decisions

The project implements several key architectural patterns:
- **Cache-first audio synthesis** with job-based async processing
- **Agent-based AI integration** with human approval workflows
- **External resource aggregation** with provider abstraction
- **Canonical biblical referencing** supporting multiple versifications
- **Comprehensive audit logging** without PII exposure
