# Bible API - Copilot Instructions

## Project Overview
Django REST Framework Bible API with AI integration, multi-language support, and RAG (semantic search via pgvector). Production-ready with 926K+ verses, 34 versions, 343K+ cross-references.

## Architecture
- **Domain-driven structure**: `bible/{domain}/` (books, verses, themes, crossrefs, rag, ai, auth, comments)
- **Centralized models**: Core models in `bible/models/` with domain imports via `__init__.py`
- **API pattern**: Views → Serializers (validation only) → Services (business logic)
- **Versioned API**: All endpoints under `/api/v1/` via `config/urls.py`
- **AI Agents**: `bible/ai/agents/{agent_name}/` with service, views, serializers, urls, tools/

## Docker Environment (PREFERRED for Django)

### Running Django Commands
**ALWAYS use Docker for Django commands** - the local environment may not have all dependencies:

```powershell
# ✅ CORRECT - Use Docker for Django
docker exec bible-api-web-1 python manage.py check
docker exec bible-api-web-1 python manage.py shell
docker exec bible-api-web-1 python -c "from bible.models import Verse; print(Verse.objects.count())"
docker exec bible-api-web-1 pytest tests/ -v

# ✅ Run migrations
docker exec bible-api-web-1 python manage.py migrate

# ✅ Interactive shell
docker exec -it bible-api-web-1 python manage.py shell
```

### Docker Management
```powershell
# Start environment
cd "c:\Users\Iury Coelho\Desktop\bible-api"; docker-compose up -d

# Rebuild after code changes
docker-compose up -d --build

# View logs
docker-compose logs -f web

# Stop all
docker-compose down

# Full reset (if issues)
docker-compose down -v; docker-compose up -d --build
```

### Container Names
- **Web/Django**: `bible-api-web-1`
- **Database**: `bible-api-db-1`
- **Redis**: `bible-api-redis-1`

### When to Use Local Python (without Docker)
Only for code that doesn't need Django ORM or database:
```powershell
# ✅ OK without Docker - pure Python utilities
py -c "from bible.ai.agents.theological_reviewer.tools.review_tool import TheologicalReviewTool; tool = TheologicalReviewTool()"

# ❌ NEEDS Docker - Django ORM
py manage.py check  # Will fail without proper env
```

## Critical Commands
```bash
make ready          # Pre-PR: format + lint + test + schema (REQUIRED before commits)
make dev            # Start Docker dev environment
make test           # Run full pytest suite
make ci-all         # Full CI validation locally
python manage.py bible status    # Check data pipeline (926K+ verses)
python manage.py bible populate  # Populate DB from processed files
```

## Key Patterns

### Authentication & Permissions
```python
# bible/auth/permissions.py - Use HasAPIScopes for scoped access
from bible.auth.permissions import HasAPIScopes

class MyView(APIView):
    permission_classes = [HasAPIScopes]
    required_scopes = ['read']  # Options: read, write, admin, ai-run, ai-tools, audio
```

### Error Handling
Always use standardized errors from `common/exceptions.py`:
```python
from common.exceptions import APIError, NotFoundError, ValidationError
# Payload: { detail, code, request_id, errors? }
```

### Query Optimization (CRITICAL)
Always use `select_related`/`prefetch_related` to avoid N+1:
```python
Verse.objects.select_related("book", "version").filter(...)
```

### Pagination
Use `StandardResultsSetPagination` from `common/pagination.py`:
- Default: 20 items, max 100
- Response: `{ pagination: {...}, results: [...] }`

### i18n Support
- Query param: `lang=pt` (preferred) or `Accept-Language` header
- Fallback: `pt-BR` → `pt` → `en`
- Add `Vary: Accept-Language` for language-sensitive responses

## Testing Conventions
```bash
pytest -k "test_name"     # Run specific test
pytest --lf               # Run last failed
pytest --quick            # Skip slow/performance tests
```

Test fixtures in `tests/conftest.py`:
- `authenticated_client` - API client with read scope
- `write_client`, `admin_client`, `ai_client` - Scoped clients
- `minimal_bible_data` - Deterministic test data

Markers: `@pytest.mark.api`, `@pytest.mark.unit`, `@pytest.mark.auth`, `@pytest.mark.slow`

## File Structure
| Path | Purpose |
|------|---------|
| `bible/{domain}/urls.py` | Domain-specific routes |
| `bible/models/__init__.py` | Central model imports |
| `common/exceptions.py` | Standardized API errors |
| `common/pagination.py` | Standard pagination class |
| `config/settings.py` | DRF/cache/DB configuration |
| `tests/conftest.py` | Shared fixtures and markers |

## AI Agents Structure
Each agent follows domain-driven design in `bible/ai/agents/{agent_name}/`:

```
bible/ai/agents/
├── __init__.py              # Public exports
├── base/                    # Shared infrastructure
│   ├── client.py            # ResponsesAPIClient (OpenAI Responses API)
│   └── executor.py          # BaseToolExecutor, ToolExecutor
├── theological_reviewer/    # Example agent
│   ├── __init__.py          # Agent exports
│   ├── service.py           # Agent logic (TheologicalReviewerAgent)
│   ├── views.py             # API endpoints
│   ├── serializers.py       # DRF serializers
│   ├── urls.py              # Agent routes
│   ├── schemas.py           # OpenAI tool definitions & structured outputs
│   └── tools/               # Agent-specific tools
│       ├── review_tool.py   # Core validation logic
│       └── executor.py      # Tool executor for this agent
└── tools/                   # Legacy/shared tools
```

### Creating a New Agent
1. Create folder: `bible/ai/agents/{agent_name}/`
2. Create files: `__init__.py`, `service.py`, `views.py`, `serializers.py`, `urls.py`, `schemas.py`
3. Create `tools/` subfolder with agent-specific tools
4. Register in `bible/ai/urls.py`: `path("{agent}/", include("bible.ai.agents.{agent_name}.urls"))`
5. Export in `bible/ai/agents/__init__.py`

## Phase 0 Data Pipeline
Topical data processing in `scripts/topical_pipeline/`:

```
scripts/topical_pipeline/
├── data/
│   ├── topics_v3/           # Processed topic JSONs (organized by letter A-Z)
│   ├── enrichment_cache/    # AI enrichment cache
│   └── logs/                # Pipeline logs
├── run_phase0.py            # Main pipeline script
└── enrichment/              # AI enrichment modules
```

### Topic Review API (Phase 0)
Endpoints for reviewing/correcting topics before DB import:
- `GET /api/v1/topics/review/` - List topics from JSON files
- `GET /api/v1/topics/review/{key}/` - Topic details
- `POST /api/v1/topics/review/{key}/validate/` - Validate topic
- `PATCH /api/v1/topics/review/{key}/entities/` - Correct entities
- `POST /api/v1/topics/review/batch-validate/` - Batch validation

## OpenAPI/Schema
- Generate: `make schema` → `schema.yml`
- Docs at `/api/v1/schema/swagger-ui/`
- Use `drf-spectacular` decorators for docs

## CI Requirements
- Coverage minimum: 77%
- Schema validation: 5+ endpoints required
- i18n audit: 90% coverage for pt,en
- Conventional commits: `feat:`, `fix:`, `docs:` with scopes (api, auth, ai, docs)

## PowerShell Terminal (Windows Environment)

### Command Execution
- **Use semicolons (`;`) to chain commands** - NEVER use `&&`
- Use pipelines (`|`) for object-based data flow
- Never create sub-shells unless explicitly asked

```powershell
# ✅ CORRECT
cd "c:\path\to\project"; py script.py

# ❌ WRONG - && doesn't work in PowerShell
cd "c:\path\to\project" && py script.py
```

### Python Commands
- **Use `py` instead of `python`** on Windows (Python Launcher)
- Use `py -m pip` for pip operations

```powershell
# ✅ CORRECT
py script.py
py -m pip install package

# ❌ WRONG - may fail on Windows
python script.py
pip install package
```

### Output Management
- Use `Select-Object -Last N` to limit output (not `tail`)
- Use `Select-Object -First N` instead of `head`
- Use `Out-String` or `Format-List` for pager commands

```powershell
# ✅ CORRECT
Get-Content file.txt | Select-Object -Last 50
py script.py 2>&1 | Select-Object -Last 100

# ❌ WRONG - Unix commands
tail -50 file.txt
```

### Path Handling
- Use absolute paths with double quotes for spaces
- Use `$PWD` or `Get-Location` for current directory

```powershell
# ✅ CORRECT
cd "c:\Users\Name\My Project"
Get-ChildItem "$PWD\src"
```
