# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Commands

The project uses a Django-based Bible API with comprehensive development workflows:

- **Development setup**: Check `BIBLE_API_BASE_PROJECT.py` for complete architecture
- **Workflow management**: Follow `DEV_FLOW_PLAYBOOK.md` for branch, commit, and CI practices  
- **Testing standards**: Apply `API_TESTING_BEST_PRACTICES.md` for endpoint testing
- **Task orchestration**: Use `BIBLE_API_ORCHESTRATOR.md` for task planning and execution

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
3. **Audio**: Text-to-speech with cache-first, on-demand synthesis
4. **AI Integration**: Agent registry with tool execution and approval workflows
5. **External Resources**: Integration with external content providers

### Data Layer
- **PostgreSQL** as primary database
- **Redis** for caching and rate limiting
- **Strategic indexing** for biblical reference lookups
- **Constraint-enforced data integrity** at database level

## Development Workflow

### Task Management
- **Always start with a TASK**: Create issues using the template in `BIBLE_API_ORCHESTRATOR.md` §7
- **Definition of Ready (DoR)** and **Definition of Done (DoD)** in `DEV_FLOW_PLAYBOOK.md` §2
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