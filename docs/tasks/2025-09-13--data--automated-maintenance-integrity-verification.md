# T-DATA-006: Maintenance - Automated Integrity & Cleanup

**Created:** 2025-09-13
**Priority:** MEDIUM
**Complexity:** Medium
**Estimated Time:** 2-3 days
**Dependencies:** T-DATA-001, T-DATA-005
**Status:** Not Started

## Objective

Implement automated maintenance system for data pipeline integrity verification, cleanup operations, and operational health monitoring.

## Context

Data pipeline operations generate temporary files, require integrity verification, and need ongoing maintenance:
- **Staging directory cleanup**: Prevent disk space issues from temporary files
- **Checksum verification**: Ensure data integrity across pipeline stages
- **Metadata consistency**: Validate processed data has required metadata
- **Directory health**: Monitor pipeline structure and identify issues
- **Retention policies**: Automated cleanup based on configurable policies

## Scope

### In Scope
- Automated cleanup of staging/ directory with configurable retention
- Checksum verification for external/ source data integrity
- Metadata consistency validation for processed/ data
- Directory structure health monitoring and reporting
- Configurable retention policies for different data types
- Integration with CLI system for manual and automated execution

### Out of Scope
- Data quality assessment (content validation)
- Performance optimization recommendations
- External system monitoring integration
- Automated data repair (detection only, manual intervention required)

## Technical Implementation

### DataMaintenanceManager Architecture
```python
class DataMaintenanceManager:
    def cleanup_old_files(self, dry_run: bool = False, retention_days: int = 30) -> Dict
    def verify_directory_integrity(self) -> Dict
    def generate_directory_report(self) -> Dict
    def check_metadata_consistency(self) -> Dict
    def validate_checksums(self, source_dir: str) -> Dict
```

### Retention Policies
```python
RETENTION_POLICIES = {
    'staging': {
        'default_days': 7,      # Aggressive cleanup for temp files
        'file_patterns': ['*.json', '*.tmp'],
        'preserve_patterns': ['.gitkeep', 'README.md']
    },
    'ingested/metrics': {
        'default_days': 30,     # Keep metrics for analysis
        'file_patterns': ['*-metrics.json']
    },
    'ingested/reports': {
        'default_days': 7,      # Reports can be regenerated
        'file_patterns': ['*-report.json']
    },
    'ingested/lineage': {
        'default_days': 90,     # Long retention for audit
        'file_patterns': ['*-lineage.jsonl']
    }
}
```

### Integrity Verification
```python
def verify_directory_integrity(self) -> Dict:
    """
    - Verify external/ checksums against checksum files
    - Validate processed/ data has required metadata.json
    - Check schema-version.txt consistency
    - Detect orphaned files and missing dependencies
    """
```

## Files to Create/Modify

### New Files
```
common/data_pipeline/
  maintenance.py # DataMaintenanceManager

bible/management/commands/
  data.py # Add maintenance subcommands

tests/common/data_pipeline/
  test_maintenance.py

scripts/
  maintenance_check.py # Standalone integrity checker
```

### Modified Files
```
Makefile # Maintenance targets
config/settings.py # Maintenance configuration
```

## Maintenance Operations

### 1. Automated Cleanup
```bash
# Preview cleanup (dry-run)
python manage.py data maintenance cleanup --dry-run --retention-days 30

# Execute cleanup
python manage.py data maintenance cleanup --retention-days 7

# Specific directory cleanup
python manage.py data maintenance cleanup --directory staging --retention-days 3
```

### 2. Integrity Verification
```bash
# Full integrity check
python manage.py data maintenance verify --report-file reports/integrity.json

# Checksum verification only
python manage.py data maintenance verify --checksums-only

# Metadata consistency check
python manage.py data maintenance verify --metadata-only
```

### 3. Directory Health Report
```bash
# Generate comprehensive directory status
python manage.py data maintenance report --report-file reports/directory-status.json

# Summary report for monitoring
python manage.py data maintenance report --summary-only
```

## Maintenance Checks

### Checksum Verification
- Verify external/*/raw/checksums.sha256 against actual files
- Detect corrupted or modified source files
- Report checksum mismatches for investigation

### Metadata Consistency
- Ensure processed/ data has metadata.json and schema-version.txt
- Validate metadata structure and required fields
- Check for orphaned data files without metadata

### Directory Structure Health
- Verify required directories exist and have correct permissions
- Check for unexpected files in protected directories (external/)
- Validate directory hierarchy consistency

### File System Health
- Monitor disk space usage by directory
- Track file count and size growth trends
- Identify potential storage issues before they impact operations

## Report Formats

### Cleanup Report
```json
{
  "cleanup_summary": {
    "files_cleaned": 42,
    "size_freed_mb": 156.8,
    "directories_processed": ["staging/", "ingested/reports/"],
    "retention_days": 7
  },
  "cleaned_files": [
    {
      "path": "staging/bibles/nvi-staging.json",
      "age_days": 14,
      "size_mb": 3.2,
      "action": "deleted"
    }
  ],
  "errors": [
    {
      "path": "staging/locked-file.json",
      "error": "Permission denied"
    }
  ]
}
```

### Integrity Report
```json
{
  "integrity_status": "issues_found",
  "checksums": {
    "verified": 45,
    "failed": 2,
    "missing": 1
  },
  "metadata": {
    "consistent": 38,
    "missing": 3,
    "invalid": 1
  },
  "issues": [
    {
      "type": "checksum_mismatch",
      "path": "external/instituto/raw/nvi-original.json",
      "expected": "sha256:abc123...",
      "actual": "sha256:def456..."
    },
    {
      "type": "missing_metadata",
      "path": "processed/bibles/canonical/pt/arc/arc.json",
      "message": "metadata.json file missing"
    }
  ]
}
```

### Directory Status Report
```json
{
  "summary": {
    "total_files": 1247,
    "total_size_mb": 2841.6,
    "external_sources": 3,
    "processed_datasets": 58,
    "last_activity": "2025-09-13T10:30:00Z"
  },
  "directories": {
    "external": {
      "files": 156,
      "size_mb": 834.2,
      "subdirectories": ["instituto", "multilingual", "commentary"]
    },
    "staging": {
      "files": 8,
      "size_mb": 23.4,
      "oldest_file_days": 3
    },
    "processed": {
      "files": 987,
      "size_mb": 1842.1,
      "languages": 25,
      "datasets": 58
    }
  }
}
```

## Definition of Ready (DoR)

- [ ] Directory structure established (T-DATA-001)
- [ ] Lineage system available for tracking (T-DATA-005)
- [ ] Retention policies defined
- [ ] Integrity check criteria specified
- [ ] Maintenance schedule planned

## Definition of Done (DoD)

- [ ] **Automated cleanup**: Staging/ directory cleaned with configurable retention
- [ ] **Checksum verification**: External/ sources verified for integrity
- [ ] **Metadata validation**: Processed/ data consistency checked
- [ ] **Directory health**: Complete status reporting functional
- [ ] **CLI integration**: All maintenance commands operational
- [ ] **Configurable policies**: Retention settings via configuration
- [ ] **Error detection**: Issues identified and reported clearly
- [ ] **Dry-run mode**: Safe preview of all destructive operations
- [ ] **Makefile targets**: Integrated with build system
- [ ] **Unit tests**: Comprehensive test coverage for all operations

## Makefile Integration

```makefile
# Maintenance commands
data-cleanup: ## Clean old temporary files (dry-run preview)
	python manage.py data maintenance cleanup --dry-run

data-cleanup-execute: ## Execute cleanup (removes files)
	python manage.py data maintenance cleanup --retention-days 7

data-verify: ## Verify data integrity
	python manage.py data maintenance verify --report-file reports/integrity.json

data-status: ## Show data pipeline status
	python manage.py data maintenance report --summary-only

data-maintenance: ## Complete maintenance cycle
	$(MAKE) data-verify
	$(MAKE) data-cleanup
	$(MAKE) data-status

# CI/CD integration
ci-data-health: ## CI health check (fast)
	python manage.py data maintenance verify --checksums-only --fail-fast

ci-data-cleanup: ## CI cleanup (conservative)
	python manage.py data maintenance cleanup --retention-days 30 --dry-run
```

## Automation and Scheduling

### GitHub Actions Integration
```yaml
name: Data Maintenance
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  maintenance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Data integrity check
        run: make ci-data-health
      - name: Cleanup preview
        run: make ci-data-cleanup
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: maintenance-reports
          path: reports/
```

### Cron Job Example
```bash
# Daily maintenance at 2 AM
0 2 * * * cd /path/to/bible-api && make data-maintenance >> /var/log/bible-api-maintenance.log 2>&1
```

## Testing Strategy

- Unit tests for cleanup logic and retention policies
- Integration tests for full maintenance workflow
- Checksum verification accuracy tests
- Metadata validation tests with various data states
- Performance tests with large directory structures
- Error handling tests for permission issues and corrupted data

## Success Metrics

- **Storage efficiency**: 80% reduction in staging/ directory usage
- **Data integrity**: 100% checksum verification success rate
- **Metadata consistency**: 95%+ processed data has valid metadata
- **Automation reliability**: Maintenance runs successfully without manual intervention
- **Issue detection**: Proactive identification of data integrity problems

## Notes

### Design Principles
1. **Safety first**: Dry-run mode for all destructive operations
2. **Configurable**: Retention policies adjustable via configuration
3. **Comprehensive**: Check all aspects of pipeline health
4. **Actionable**: Clear error reporting with remediation guidance
5. **Automated**: Minimal manual intervention required

### Critical Safety Features
- Never delete external/ data (read-only protection)
- Always preserve .gitkeep and README.md files
- Confirm deletions in interactive mode
- Comprehensive logging of all maintenance actions

## Related Tasks

- **Depends on:** T-DATA-001 (directory structure), T-DATA-005 (lineage data)
- **Integrates with:** All data pipeline tasks (provides operational support)
- **Enables:** Reliable long-term operation of data pipeline
