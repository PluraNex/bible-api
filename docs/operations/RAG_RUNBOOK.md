---
title: "RAG Runbook — Operação & Manutenção"
status: draft
owner: "@iuryeng"
updated: 2025-09-14
---

## TL;DR
- Geração: `make embeddings-generate` (ou comando manual com `--only-missing`).
- Índice IVFFlat: `manage.py create_vector_indexes --create --lists=64 --dim=1536 --alter-dim --maintenance-work-mem=2GB`.
- Probes: defina `PG_IVFFLAT_PROBES=10` no `.env`.
- Diagnóstico: métricas `/metrics/prometheus/` e logs com `request_id`.

## Procedimentos
1) Subir serviços
   - `docker-compose up -d`

2) Verificar DB & extensão
   - `docker-compose exec db psql -U bible_user -d bible_api -c "SELECT extname FROM pg_extension"`
   - Esperado: `vector` presente.

3) Migrações
   - `docker-compose exec web python manage.py migrate`

4) Geração de embeddings
   - Pequeno lote (sanidade):
     - `docker-compose exec web python manage.py generate_embeddings --versions=PT_NAA --limit=100 --batch-size=64 --only-missing --sleep=0.2`
   - Produção (por etapas):
     - Rodar por versão (PT_* depois EN_*), noite/finais de semana.
     - `--only-missing` por padrão; `--overwrite` só em troca de modelo.

5) Índice IVFFlat (recall)
   - Dev: `lists=64` (baixo custo)
   - Prod: após popular bem a tabela, recriar com `lists=1000–4000`:
     - `docker-compose exec web python manage.py create_vector_indexes --create --lists=2000 --dim=1536 --alter-dim --maintenance-work-mem=4GB`
   - Ajustar probes (recall vs latência): `.env -> PG_IVFFLAT_PROBES=10–20`.

6) Monitoramento
   - Latência/volume: `rag_retrieve_total`, `rag_retrieve_latency_seconds_bucket`.
   - Índices: `inprogress_index_builds` durante criações.
   - Alertas: 5xx no endpoint `/api/v1/ai/rag/retrieve`, spikes de 429 no OpenAI.

7) Desempenho & Custos
   - Throttling: `--sleep`, `--batch-size` moderados.
   - Retentativas: `--max-retries=5` e `--timeout=60`.
   - Rate limit da API: habilitar throttling DRF para rota de retrieve.

8) Problemas comuns
   - `maintenance_work_mem` insuficiente ao criar índice: aumente via `--maintenance-work-mem=2GB` no comando.
   - Dimensões inconsistentes: use a versão atual do modelo e confira `dim_small=1536, dim_large=3072`.
   - Sem `OPENAI_API_KEY`: o retrieve exige `vector` no request ou configurar a chave.

## Rollback
- `DROP INDEX CONCURRENTLY idx_verse_embeddings_embedding_small_ivf`
- Reverter variáveis no `.env`; restaurar probes.

## SLOs sugeridos
- Latência P95 do retrieve ≤ 250 ms com `top_k=10` em produção (IVFFlat `lists>=1000`, `probes>=10`).
- Disponibilidade ≥ 99.9%.
