# Esquemas JSON e Validação

O pipeline utiliza JSON Schemas para garantir interoperabilidade e qualidade.

## Esquemas Suportados

- `manifest-v1` — Manifesto de fonte/catálogo (configura ingest/convert)
- `staging-bible-v1` — Dados em staging (pré‑processamento)
- `processed-bible-v1` — Dados processados (consumo pela API)

Os arquivos ficam em `data/schemas/` e são validados via `SchemaValidator`.

## Validação

- Validar arquivo/diretório:
```
python manage.py data validate data/external/example/manifest.yaml --schema manifest-v1
python manage.py data validate data/processed/bibles/canonical/pt/nvi --schema processed-bible-v1
```

## Validação ciente de Models (opcional)

Para dados processados, há uma validação adicional (model‑aware) que verifica:
- `Language` existente (com fallback base/regional)
- `Version(language, code)` existente (quando `version_code` presente)
- Mapeamento de livros para `CanonicalBook`
- Estrutura capítulo/verso válida; sem duplicatas

Uso (em convert):
```
python manage.py data convert bibles --manifest ... --validate --output-file <processed.json>
```
