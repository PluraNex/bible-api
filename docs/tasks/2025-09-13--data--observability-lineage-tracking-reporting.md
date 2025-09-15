# T-DATA-005: Observability - Lineage Tracking & Reporting

**Created:** 2025-09-13
**Priority:** MEDIUM
**Complexity:** Medium
**Estimated Time:** 2-3 days
**Dependencies:** T-DATA-003, T-DATA-004
**Status:** Not Started

## Objective

Implement comprehensive data lineage tracking and observability system for the data pipeline with audit trails and operational reporting.

## Context

Data pipeline operations need full observability for:
- **Audit compliance**: Track data transformations and provenance
- **Debugging**: Understand data flow when issues occur
- **Performance monitoring**: Identify bottlenecks and optimization opportunities
- **Operational insights**: Usage patterns and processing metrics

Current system lacks visibility into data transformations, making troubleshooting difficult and compliance challenging.

## Scope

### In Scope
- Data lineage tracking for all pipeline operations (ingestion, transformation, validation)
- Structured logging with performance metrics
- JSON report generation for automation and dashboards
- Console output with progress indicators and summaries
- Daily lineage files in JSONL format for audit trails
- Query interface to trace data transformation chains
- Retention policies for lineage data management

### Out of Scope
- Real-time dashboards (JSON reports enable external dashboard integration)
- Advanced analytics or ML-based insights
- Integration with external monitoring systems (focus on data export)

## Technical Implementation

### Data Lineage Architecture
```python
@dataclass
class LineageRecord:
    id: str                     # Unique operation ID
    timestamp: str              # ISO format timestamp
    operation_type: str         # 'ingestion', 'transformation', 'validation'
    source_path: str           # Input file/source
    target_path: str           # Output file/target
    transformation_type: str    # Specific transformation applied
    metadata: dict             # Operation-specific data
    checksum_before: str       # Source checksum
    checksum_after: str        # Target checksum

class DataLineageTracker:
    def record_ingestion(self, source_name: str, target_file: Path, metadata: dict) -> str
    def record_transformation(self, source_file: Path, target_file: Path,
                            transformation_type: str, metadata: dict) -> str
    def record_validation(self, file_path: Path, schema_version: str,
                         validation_result: dict) -> str
    def get_lineage_chain(self, file_path: str) -> List[LineageRecord]
    def generate_lineage_report(self, start_date: str, end_date: str) -> dict
```

### Structured Logging System
```python
class StructuredLogger:
    def log_operation(self, operation: str, dataset: str = None, version: str = None,
                     status: str = None, duration: float = None, count: int = None,
                     extra: dict = None)
```

### Report Generation
```python
class ReportManager:
    @staticmethod
    def create_metrics(command: str, subcommand: str) -> CommandMetrics

    @staticmethod
    def save_report(metrics: CommandMetrics, report_file: str)

    @staticmethod
    def print_summary(metrics: CommandMetrics, verbose: int = 0)
```

## Files to Create/Modify

### New Files
```
common/data_pipeline/
  lineage.py # DataLineageTracker
  reporting.py # ReportManager, CommandMetrics
  logging.py # StructuredLogger

data/ingested/
  lineage/
    2025-09-13-lineage.jsonl # Daily lineage files
    2025-09-14-lineage.jsonl
  metrics/
    2025-09-13-ingest-metrics.json
    2025-09-13-convert-metrics.json
  reports/
    2025-09-13-data-quality.json
    2025-09-13-lineage-report.json

tests/common/data_pipeline/
  test_lineage.py
  test_reporting.py
  test_logging.py
```

### Modified Files
```
bible/management/commands/
  data.py # Integrate lineage tracking

common/data_pipeline/
  migration.py # Add lineage tracking calls
  handlers/ # Add lineage tracking to all handlers
```

## Data Lineage Tracking Points

### 1. Data Ingestion Operations
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-09-13T10:30:00Z",
  "operation_type": "ingestion",
  "source_path": "external_source:instituto_biblico",
  "target_path": "data/external/instituto/raw/nvi-20250913.json",
  "transformation_type": "external_to_raw",
  "metadata": {
    "source_name": "instituto_biblico",
    "record_count": 31102,
    "ingestion_method": "manual_upload"
  },
  "checksum_after": "sha256:abc123..."
}
```

### 2. Data Transformation Operations
```json
{
  "id": "660f9511-f39c-52e5-b827-557766551001",
  "timestamp": "2025-09-13T10:35:00Z",
  "operation_type": "transformation",
  "source_path": "data/datasets/inst/json/NVI.json",
  "target_path": "data/processed/bibles/canonical/pt/nvi/nvi.json",
  "transformation_type": "migration_to_processed",
  "metadata": {
    "migration_type": "existing_to_new_structure",
    "language": "pt",
    "version_code": "nvi",
    "confidence": 1.0
  },
  "checksum_before": "sha256:def456...",
  "checksum_after": "sha256:ghi789..."
}
```

### 3. Validation Operations
```json
{
  "id": "770a0622-a4ad-63f6-c938-668877662002",
  "timestamp": "2025-09-13T10:40:00Z",
  "operation_type": "validation",
  "source_path": "data/processed/bibles/canonical/pt/nvi/nvi.json",
  "target_path": "data/processed/bibles/canonical/pt/nvi/nvi.json",
  "transformation_type": "validation",
  "metadata": {
    "schema_version": "processed-bible-v1",
    "validation_passed": true,
    "error_count": 0,
    "warning_count": 2
  },
  "checksum_before": "sha256:ghi789..."
}
```

## Report Formats

### Command Execution Report
```json
{
  "summary": {
    "command": "data migrate portuguese-bibles",
    "status": "success",
    "duration": "45.2s",
    "processed": 13,
    "success_rate": "100.0%"
  },
  "metrics": {
    "command": "data",
    "subcommand": "migrate",
    "start_time": "2025-09-13T10:30:00Z",
    "end_time": "2025-09-13T10:30:45Z",
    "records_processed": 13,
    "records_success": 13,
    "records_failed": 0,
    "files_created": ["data/processed/bibles/canonical/pt/nvi/nvi.json", "..."],
    "memory_peak_mb": 245.6
  },
  "generated_at": "2025-09-13T10:30:45Z"
}
```

### Lineage Chain Report
```json
{
  "file_path": "data/processed/bibles/canonical/pt/nvi/nvi.json",
  "lineage_chain": [
    {
      "operation": "ingestion",
      "timestamp": "2025-09-13T09:00:00Z",
      "source": "external_source:instituto_biblico",
      "transformation": "external_to_raw"
    },
    {
      "operation": "transformation",
      "timestamp": "2025-09-13T10:30:00Z",
      "source": "data/datasets/inst/json/NVI.json",
      "transformation": "migration_to_processed"
    },
    {
      "operation": "validation",
      "timestamp": "2025-09-13T10:40:00Z",
      "schema": "processed-bible-v1",
      "result": "passed"
    }
  ],
  "total_operations": 3,
  "data_age_hours": 1.5
}
```

## Definition of Ready (DoR)

- [ ] CLI system operational (T-DATA-003)
- [ ] Migration system available for tracking (T-DATA-004)
- [ ] Lineage record structure defined
- [ ] Report formats specified
- [ ] Storage and retention policies established

## Definition of Done (DoD)

- [ ] **Lineage tracking**: All pipeline operations (ingestion, transformation, validation) tracked
- [ ] **JSONL storage**: Daily lineage files with complete audit trail
- [ ] **Performance metrics**: Command execution time, memory usage, throughput tracked
- [ ] **JSON reports**: Structured reports for automation and dashboards
- [ ] **Console output**: User-friendly progress and summary information
- [ ] **Query interface**: Can trace complete lineage chain for any file
- [ ] **Retention policies**: Automatic cleanup of old lineage data
- [ ] **CLI integration**: All data commands include lineage tracking
- [ ] **Error tracking**: Failed operations logged with detailed error information
- [ ] **Unit tests**: Comprehensive test coverage for all tracking components

## CLI Integration Examples

### Report Generation
```bash
# Generate lineage report for last 7 days
python manage.py data maintenance lineage \
  --start-date 2025-09-06 \
  --end-date 2025-09-13 \
  --report-file reports/lineage-7days.json

# Trace lineage for specific file
python manage.py data audit lineage \
  --file data/processed/bibles/canonical/pt/nvi/nvi.json \
  --report-file reports/nvi-lineage.json
```

### Makefile Integration
```makefile
data-lineage: ## Generate data lineage report for last 7 days
	python manage.py data maintenance lineage \
	  --start-date=$(shell date -d '7 days ago' +%Y-%m-%d) \
	  --report-file=reports/lineage-7days.json

data-metrics: ## Show pipeline performance metrics
	@python manage.py data maintenance report | grep -E "(duration|memory|throughput)"
```

## Testing Strategy

- Unit tests for lineage record creation and storage
- Integration tests for full pipeline tracking
- Performance tests for high-volume lineage data
- Query interface functionality tests
- Report generation accuracy tests
- Retention policy automation tests

## Success Metrics

- **100% operation coverage**: All pipeline operations tracked
- **<5% performance overhead**: Lineage tracking adds minimal latency
- **Complete audit trail**: Can trace any file back to original source
- **Automated reporting**: Zero manual effort for operational reports
- **Query performance**: Lineage chain retrieval in <1 second

## Notes

### Design Decisions
1. **JSONL format** for lineage storage (append-only, easy to parse)
2. **Daily file rotation** for manageable file sizes and retention
3. **UUID-based operation IDs** for unique identification across systems
4. **Checksum tracking** for data integrity verification
5. **Structured metadata** for operation-specific information

### Retention Policies
- **Lineage data**: 90 days retention (configurable)
- **Metrics**: 30 days detailed, 1 year summary
- **Reports**: 7 days automatic, manual archiving for longer

## Related Tasks

- **Depends on:** T-DATA-003 (CLI system), T-DATA-004 (migration operations)
- **Enables:** Better debugging and compliance for all data operations
- **Integrates with:** T-DATA-006 (maintenance uses lineage data)
