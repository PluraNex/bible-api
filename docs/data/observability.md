# Observabilidade — Lineage, Métricas e Relatórios

Rastreia a proveniência e transformações dos dados, além de gerar relatórios operacionais.

## Lineage (proveniência)

- Armazenado como JSONL diário em `data/ingested/lineage/YYYY-MM-DD-lineage.jsonl`
- Gravado por `common.data_pipeline.lineage.DataLineageTracker`
  - `record_ingestion(source_name, target_file, metadata)`
  - `record_transformation(source_file, target_file, transformation_type, metadata)`
  - `record_validation(file_path, schema_version, validation_result)`
- Integração já realizada em migração e conversão (quando `--validate`)

## Relatórios de Lineage

- CLI:
```
python manage.py data maintenance lineage --start-date 2025-09-06 --end-date 2025-09-13 --report-file reports/lineage-7days.json
```
- Campos agregados: operações por tipo, total de registros, top targets

## Métricas de Comando

- `common.data_pipeline.reporting.{CommandMetrics, ReportManager}`
- Pode ser integrado aos subcomandos para salvar duração, contagens e arquivos criados (futuro)

## Logging Estruturado

- `common.data_pipeline.logging.StructuredLogger`
- Emite JSON por operação (útil para pipelines/CI)

## Retenção

- Recomenda-se reter lineage por 90 dias e relatórios por 7 dias
- Pode ser integrado a `data cleanup` futuramente (`--lineage-days`)
