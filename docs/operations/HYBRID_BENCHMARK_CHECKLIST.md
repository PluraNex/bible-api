# Hybrid Benchmark Checklist

## Antes do reboot
- Garantir que os artefatos científicos estão salvos no repositório.
- Manter este checklist como ponto de retomada.

## Depois do reboot
1. Ativar virtualização na BIOS/UEFI, se ainda estiver desligada.
2. Abrir o Docker Desktop e esperar o backend Linux subir.
3. Preparar o ambiente Python no host antes de rodar qualquer script local:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Observacao:
- `check_hybrid_readiness.py` e `run_hybrid_benchmark.py` dependem de `requests`
- sem esse bootstrap, os scripts locais podem falhar antes mesmo de validar Docker ou API

4. Na raiz do projeto, subir a infraestrutura:

```bash
docker compose up -d db redis web
```

5. Verificar prontidão básica:

```bash
python scripts/check_hybrid_readiness.py
python scripts/check_hybrid_readiness.py --live
```

6. Se o banco estiver vazio ou sem vetores, aplicar migrations e checar embeddings:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py generate_embeddings --versions=PT_NAA --limit=100 --only-missing
```

7. Validar endpoint híbrido manualmente:

```bash
curl "http://127.0.0.1:8000/api/v1/ai/rag/hybrid/?q=amor&top_k=3"
```

8. Rodar o benchmark piloto:

```bash
python scripts/run_hybrid_benchmark.py --dry-run
python scripts/run_hybrid_benchmark.py --query-id q001 --experiment baseline_hybrid
python scripts/run_hybrid_benchmark.py
```

## Critérios de pronto
- `docker info` responde
- `docker compose ps` responde
- `/health/` responde
- `/api/v1/ai/rag/hybrid/` responde
- benchmark de `1 query x 1 experimento` gera artefato em `data/experiments/hybrid_search/runs/`

## Bloqueios conhecidos
- Sem Docker daemon ativo, o banco não sobe.
- Sem ambiente Python preparado no host, os scripts locais podem falhar por dependências ausentes.
- Sem embeddings no banco, a busca híbrida não produz evidência válida.
- Se outra aplicação estiver ocupando a porta `8000`, o benchmark pode bater em um serviço errado e retornar `404`.

## Alternativa sem Docker
- Se você tiver PostgreSQL local com `pgvector`, pode ignorar Docker e seguir:
  [LOCAL_POSTGRES_RESTORE.md](/C:/Users/Iury%20Coelho/Desktop/bible-api/docs/operations/LOCAL_POSTGRES_RESTORE.md)
