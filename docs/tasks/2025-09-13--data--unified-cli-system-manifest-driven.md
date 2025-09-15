# T-DATA-003: CLI System - Unified Data Management Commands

**Created:** 2025-09-13
**Priority:** HIGH
**Complexity:** High
**Estimated Time:** 3-4 days
**Dependencies:** T-DATA-001, T-DATA-002
**Status:** Not Started

## Objective

Create unified, extensible CLI system for data management operations with manifest-driven configuration and plugin architecture.

## Context

Current data management uses scattered commands (`populate_bibles`, `import_firecrawl_json`, etc.) with inconsistent interfaces. We need:

- Unified `python manage.py data` command with subcommands
- Consistent flags and behavior across operations
- Extensible plugin system for new data types
- Manifest-driven source discovery (no hardcoded paths)
- Professional observability and error handling

## Scope

### In Scope
- Unified CLI with subcommands: `ingest`, `convert`, `audit`, `seed`, `migrate`, `maintenance`
- Plugin registry system for extensible handlers
- Manifest-driven configuration (YAML-based)
- Standardized flags: `--dry-run`, `--overwrite`, `--report-file`, `--limit`, `--langs`
- Backwards compatibility layer for existing commands
- JSON reporting and structured logging
- Integration with Makefile targets

### Out of Scope
- Actual data processing logic (delegated to handlers)
- Migration implementation (T-DATA-004)
- Maintenance operations (T-DATA-006)

## Technical Implementation

### Command Structure
```bash
python manage.py data ingest bibles --source instituto --version nvi --dry-run
python manage.py data convert bibles --validate --report-file convert.json
python manage.py data audit i18n --threshold 0.95 --langs pt en
python manage.py data seed names --langs pt en es
python manage.py data migrate portuguese-bibles --dry-run
python manage.py data maintenance cleanup --retention-days 30
```

### Plugin Registry Architecture
```python
class DataHandler(ABC):
    @abstractmethod
    def can_handle(self, source_type: str, manifest: dict) -> bool

    @abstractmethod
    def ingest(self, manifest: dict, options: dict) -> dict

    @abstractmethod
    def convert(self, staging_data: dict, options: dict) -> dict

class HandlerRegistry:
    def register(self, name: str, handler_class: Type[DataHandler])
    def get_handler(self, source_type: str, manifest: dict) -> DataHandler
```

### Manifest-Driven Configuration
```yaml
# data/catalog.yaml - Master catalog
sources:
  bibles:
    canonical:
      - source: "instituto_biblico"
        manifest: "data/external/instituto-biblico/manifest.yaml"
        priority: 1
      - source: "multilingual_collection"
        manifest: "data/external/multilingual/manifest.yaml"
        priority: 2

# data/external/instituto-biblico/manifest.yaml - Source-specific
datasets:
  bibles:
    nvi:
      name: "Nova Versao Internacional"
      language: "pt"
      file_pattern: "nvi*.json"
      schema_version: "bible-text-v1"
```

## Files to Create/Modify

### New Files
```
bible/management/commands/
  data.py # Unified CLI command

common/data_pipeline/
  registry.py # Plugin registry
  manifest.py # Manifest management
  reporting.py # Report generation
  handlers/
    __init__.py
    base.py # Base handler class
    bible_handler.py # Bible operations
    crossref_handler.py # Cross-reference operations
    commentary_handler.py # Commentary operations

data/
  catalog.yaml # Master data catalog
  external/
    */manifest.yaml # Per-source manifests

tests/management/commands/
  test_data_command.py

tests/common/data_pipeline/
  test_registry.py
  test_manifest.py
  test_handlers.py
```

### Modified Files
```
bible/management/commands/
  populate_bibles.py # Add deprecation warnings
  import_firecrawl_json.py # Add deprecation warnings

Makefile # Add new data-* targets
```

### Backwards Compatibility Layer
```python
# bible/management/commands/populate_bibles.py
class Command(BaseCommand):
    help = '[DEPRECATED] Use "python manage.py data ingest bibles" instead'

    def handle(self, *args, **options):
        warnings.warn("Command deprecated. Use 'data ingest bibles'")
        # Delegate to new system
        data_command = DataCommand()
        return data_command.handle(subcommand='ingest', source_type='bibles', **mapped_options)
```

## Definition of Ready (DoR)

- [ ] Current commands cataloged and analyzed
- [ ] Plugin architecture design validated
- [ ] Manifest structure agreed upon
- [ ] Flag standardization defined
- [ ] Backwards compatibility strategy confirmed

## Definition of Done (DoD)

- [ ] `python manage.py data` with all subcommands functional
- [ ] Plugin registry with auto-discovery working
- [ ] Manifest-driven source discovery operational
- [ ] Standard flags working across all subcommands
- [ ] Backwards compatibility for existing commands
- [ ] JSON reporting system functional
- [ ] Structured logging implemented
- [ ] Error handling centralized and consistent
- [ ] Help system comprehensive and user-friendly
- [ ] Makefile integration complete
- [ ] Unit tests for all components
- [ ] Integration tests for command flows

## Command Specifications

### data ingest
```bash
python manage.py data ingest <source_type> [options]
```
**Purpose:** Import raw data from external sources
**Options:** `--source`, `--version`, `--dry-run`, `--overwrite`

### data convert
```bash
python manage.py data convert <data_type> [options]
```
**Purpose:** Convert staging data to processed format
**Options:** `--validate`, `--dry-run`, `--report-file`

### data audit
```bash
python manage.py data audit <audit_type> [options]
```
**Purpose:** Audit data quality, i18n coverage, integrity
**Options:** `--threshold`, `--fail-on-missing`, `--report-file`

### data seed
```bash
python manage.py data seed <seed_type> [options]
```
**Purpose:** Generate metadata and reference data
**Options:** `--langs`, `--overwrite`, `--dry-run`

## Makefile Integration

```makefile
# Data pipeline commands
data-ingest: ## Ingest all data sources
	python manage.py data ingest bibles --report-file=reports/ingest.json

data-convert: ## Convert staging to processed
	python manage.py data convert bibles --validate

data-audit: ## Run data quality audits
	python manage.py data audit i18n coverage integrity

data-seed: ## Seed reference metadata
	python manage.py data seed names metadata

data-pipeline: ## Complete pipeline execution
	$(MAKE) data-ingest data-convert data-seed data-audit
```

## Testing Strategy

- Unit tests for each handler type
- Integration tests for full command flows
- Plugin registry functionality tests
- Manifest parsing and validation tests
- Backwards compatibility tests
- Error handling and edge case tests

## Success Metrics

- All existing functionality available through new CLI
- 90% reduction in command-specific code duplication
- Sub-5 second response time for help/dry-run operations
- Zero breaking changes for existing workflows
- 100% test coverage for command dispatch logic

## Notes

### Design Principles
1. **Consistency** - Same flags and behavior everywhere
2. **Extensibility** - Easy to add new data types/operations
3. **Discoverability** - Manifest-driven, no hardcoded paths
4. **Safety** - Dry-run mode for all destructive operations
5. **Observability** - Structured logs and detailed reports

### Plugin Handler Responsibilities
- **Bible Handler**: Bible text ingestion, validation, conversion
- **Crossref Handler**: Cross-reference data management
- **Commentary Handler**: Commentary and author data operations

## Related Tasks

- **Depends on:** T-DATA-001 (directory structure), T-DATA-002 (language detection)
- **Blocks:** T-DATA-004 (migration uses CLI), T-DATA-005 (observability), T-DATA-006 (maintenance)
- **Integrates with:** All data pipeline tasks
