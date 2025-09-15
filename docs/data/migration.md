# Migração de Datasets — Reorganização e Normalização

A migração reorganiza datasets legados para a estrutura `data/processed/` com foco em idiomas e conformidade de schema.

## Engine

- `common.data_pipeline.migration.DataMigrationManager`
  - `migrate_portuguese_bibles(source_dir, dry_run=True)`
  - `migrate_multilingual_bibles(source_dir, min_confidence=0.5, dry_run=True)`
  - `migrate_commentary_authors(source_dir, dry_run=True)`
  - `cleanup_old_structures(dry_run=True, remove_bibles_2024=False)`

Lineage é registrado automaticamente durante cópias (ver `observability.md`).

## Comandos

```
python manage.py data migrate portuguese-bibles --source-dir data/datasets/inst/json --dry-run --report-file reports/migrate-pt.json
python manage.py data migrate multilingual-bibles --source-dir data/datasets/json --min-confidence 0.5 --dry-run --report-file reports/migrate-multi.json
python manage.py data migrate commentary-authors --source-dir data/datasets/commentary --dry-run --report-file reports/migrate-authors.json
python manage.py data migrate cleanup-old --remove-bibles-2024 --dry-run --report-file reports/migrate-cleanup.json
```

## Saída

- Bíblias: `data/processed/bibles/canonical/<lang>/<version_code>/`
  - `<version_code>.json` (arquivo original)
  - `metadata.json` (lineage: migrated_from/migrated_at/schema_version)

> Nota: Conversão total para `processed-bible-v1` (normalização estrutural) pode ser adicionada em etapa posterior.
