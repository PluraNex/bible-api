# T-DATA-004: Migration System - Dataset Reorganization Engine

**Created:** 2025-09-13
**Priority:** HIGH
**Complexity:** High
**Estimated Time:** 4-5 days
**Dependencies:** T-DATA-002, T-DATA-003
**Status:** Not Started

## Objective

Implement comprehensive migration system to reorganize existing scattered datasets into the new language-first, pipeline-driven structure.

## Context

Current data is scattered across multiple directories:
- **Portuguese Bibles:** `data/datasets/inst/json/` (13 versions: NVI, ARC, ARA, etc.)
- **Multilingual Bibles:** `data/datasets/json/` (150+ versions in 25+ languages)
- **Commentary Authors:** `data/datasets/commentary/` (biblical, modern, church-fathers)
- **Redundant data:** `data/datasets/bibles-2024/` (duplicates from json/)

Need intelligent migration that preserves data integrity while reorganizing for optimal i18n structure.

## Scope

### In Scope
- Automated migration of Portuguese Bibles with metadata preservation
- Intelligent multilingual Bible migration using language detection
- Commentary author categorization and restructuring
- Data format normalization to consistent schemas
- Checksum verification and integrity preservation
- Rollback capability for failed migrations
- Cleanup of redundant/obsolete directory structures

### Out of Scope
- Manual data curation (automated classification only)
- Translation quality improvements
- Data validation beyond integrity checks (covered in other tasks)

## Technical Implementation

### Migration Architecture
```python
class DataMigrationManager:
    def migrate_portuguese_bibles(self, source_dir: str) -> Dict
    def migrate_multilingual_bibles(self, source_dir: str) -> Dict
    def migrate_commentary_authors(self, source_dir: str) -> Dict
    def cleanup_old_structures(self, options: dict) -> Dict

    def _migrate_single_bible(self, bible_data: dict, version_code: str,
                             language: str, source_name: str) -> dict
    def _normalize_bible_format(self, bible_data: dict) -> dict
    def _create_migration_manifest(self, results: list) -> dict
```

### Migration Flow
1. **Analysis Phase**: Use language detection to classify all files
2. **Staging Phase**: Copy data to staging/ with format normalization
3. **Processing Phase**: Move to processed/ with proper directory structure
4. **Verification Phase**: Validate checksums and metadata consistency
5. **Cleanup Phase**: Remove redundant source directories

### Target Structure After Migration
```
data/processed/bibles/canonical/
â”œâ”€â”€ pt/                    # Portuguese (15+ versions)
â”‚   â”œâ”€â”€ nvi/
â”‚   â”‚   â”œâ”€â”€ nvi.json
â”‚   â”‚   â”œâ”€â”€ metadata.json
â”‚   â”‚   â””â”€â”€ schema-version.txt
â”‚   â”œâ”€â”€ arc/
â”‚   â”œâ”€â”€ ara/
â”‚   â””â”€â”€ tb/
â”œâ”€â”€ en/                    # English (30+ versions)
â”‚   â”œâ”€â”€ kjv/
â”‚   â”œâ”€â”€ asv/
â”‚   â””â”€â”€ web/
â”œâ”€â”€ de/                    # German (10+ versions)
â”œâ”€â”€ fr/                    # French (15+ versions)
â””â”€â”€ [20+ other languages]

data/processed/commentary/authors/
â”œâ”€â”€ biblical/
â”‚   â”œâ”€â”€ biblical-authors.json
â”‚   â””â”€â”€ metadata.json
â”œâ”€â”€ church-fathers/
â””â”€â”€ modern/
```

## Files to Create/Modify

### New Files
```
common/data_pipeline/
â”œâ”€â”€ migration.py               # DataMigrationManager

data/management/commands/
â”œâ”€â”€ data.py                    # Add migrate subcommands

scripts/
â”œâ”€â”€ migration_preview.py       # Pre-migration analysis tool

tests/common/data_pipeline/
â”œâ”€â”€ test_migration.py

data/ingested/reports/
â”œâ”€â”€ migration-*.json           # Generated migration reports
```

### Modified Files
```
Makefile                       # Migration targets
.gitignore                     # Ignore old directories after migration
```

## Migration Commands

### Portuguese Bibles Migration
```bash
python manage.py data migrate portuguese-bibles \
  --source-dir data/datasets/inst/json \
  --dry-run \
  --report-file reports/migrate-pt.json
```

### Multilingual Bibles Migration
```bash
python manage.py data migrate multilingual-bibles \
  --source-dir data/datasets/json \
  --min-confidence 0.5 \
  --dry-run \
  --report-file reports/migrate-multi.json
```

### Commentary Authors Migration
```bash
python manage.py data migrate commentary-authors \
  --source-dir data/datasets/commentary \
  --report-file reports/migrate-authors.json
```

### Full Migration
```bash
python manage.py data migrate full \
  --skip-confirmation \
  --report-file reports/migrate-full.json
```

## Definition of Ready (DoR)

- [ ] Language detection system operational (T-DATA-002)
- [x] CLI framework implemented (T-DATA-003)
- [ ] Current data structures fully mapped and analyzed
- [ ] Target structure validated with stakeholders
- [ ] Rollback strategy defined and tested
- [ ] Data backup procedures established

## Definition of Done (DoD)

- [ ] **Portuguese Bibles**: All 13 versions migrated to `processed/bibles/canonical/pt/`
- [ ] **Multilingual Bibles**: 150+ versions classified and organized by language
- [ ] **Commentary Authors**: Categorized into biblical/church-fathers/modern
- [ ] **Data Integrity**: All checksums verified, no data loss
- [ ] **Format Normalization**: Consistent schema across all migrated data
- [ ] **Metadata Preservation**: Source information and lineage tracked
- [ ] **Redundant Cleanup**: `bibles-2024/` and duplicates removed
- [ ] **CLI Integration**: All migration commands functional
- [ ] **Rollback Tested**: Ability to restore original structure
- [ ] **Documentation**: Migration manifest and reports generated

## Expected Migration Results

### Portuguese Bibles (data/datasets/inst/json/)
- **NVI.json** â†’ `processed/bibles/canonical/pt/nvi/`
- **ARC.json** â†’ `processed/bibles/canonical/pt/arc/`
- **ARA.json** â†’ `processed/bibles/canonical/pt/ara/`
- **TB.json** â†’ `processed/bibles/canonical/pt/tb/`
- ... and 9 more versions

### Multilingual Bibles (data/datasets/json/)
- **English (30+ files)**: KJV.json, ASV.json, BBE.json, etc. â†’ `processed/bibles/canonical/en/`
- **German (10+ files)**: GerSch.json, GerMenge.json, etc. â†’ `processed/bibles/canonical/de/`
- **French (15+ files)**: FreCrampon.json, FreJND.json, etc. â†’ `processed/bibles/canonical/fr/`
- **Other Languages**: Spanish, Italian, Dutch, Czech, etc.

### Commentary Authors
- **biblical-authors.json** â†’ `processed/commentary/authors/biblical/`
- **church-fathers-authors.json** â†’ `processed/commentary/authors/church-fathers/`
- **modern-authors.json** â†’ `processed/commentary/authors/modern/`

## Data Normalization

### Bible Text Format Normalization
```json
{
  "metadata": {
    "version_code": "nvi",
    "language": "pt",
    "name": "Nova VersÃ£o Internacional",
    "schema_version": "processed-bible-v1",
    "migrated_from": "data/datasets/inst/json/NVI.json",
    "migrated_at": "2025-09-13T10:30:00Z"
  },
  "books": [
    {
      "name": "Genesis",
      "chapters": [
        {
          "chapter": 1,
          "verses": [
            {"verse": 1, "text": "No princÃ­pio Deus criou os cÃ©us e a terra."}
          ]
        }
      ]
    }
  ]
}
```

## Risk Mitigation

### Data Loss Prevention
- Create complete backup before migration
- Checksums verification at every step
- Atomic operations where possible
- Detailed logging of all transformations

### Migration Failure Recovery
- Rollback scripts to restore original structure
- Staged migration allows partial rollback
- Dry-run mode for testing migration logic
- Manual intervention points for problematic files

## Testing Strategy

- Unit tests for each migration component
- Integration tests for full migration flow
- Data integrity validation tests
- Performance tests with large datasets
- Rollback scenario testing
- Edge case handling (corrupted files, missing data)

## Success Metrics

- **100% data preservation**: No loss of content during migration
- **95%+ automatic classification**: Minimal manual intervention needed
- **Performance**: Complete migration in <30 minutes
- **Consistency**: All migrated data follows standardized schema
- **Rollback capability**: Can restore original structure in <5 minutes

## Notes

### Critical Migration Decisions
1. **Preserve original filenames** in metadata for traceability
2. **Language confidence threshold** of 0.5 for automatic migration
3. **Atomic operations** where possible to prevent partial failures
4. **Comprehensive logging** for audit trail and debugging

### Manual Review Required For
- Files with language confidence < 0.5
- Corrupted or incomplete JSON files
- Unusual formatting that doesn't match expected schema
- Duplicate versions with different content

## Related Tasks

- **Depends on:** T-DATA-002 (language detection), T-DATA-003 (CLI system)
- **Enables:** T-DATA-007 (complete reorganization)
- **Integrates with:** T-DATA-005 (lineage tracking), T-DATA-006 (maintenance)
