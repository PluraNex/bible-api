# PostgreSQL Local Restore Guide

Este guia cobre o cenário sem Docker, usando PostgreSQL nativo no Windows e o dump já existente em `E:\embeding_bibles`.

## O que já existe
- Dump completo: `E:\embeding_bibles\bible_api_1M_embeddings_20250922_154638.dump`
- Tipo: PostgreSQL custom format (`pg_restore`)
- Conteúdo esperado:
  - schema completo
  - dados
  - índices
  - embeddings

## Pré-requisitos
1. PostgreSQL 15 instalado localmente.
2. `pg_restore`, `psql`, `createdb` e `dropdb` no `PATH`.
3. Extensão `pgvector` disponível na instalação local.
4. Um banco `bible_api` acessível em `localhost:5432`.

## Instalação recomendada
- PostgreSQL 15 nativo no Windows.
- Durante a instalação:
  - usuário sugerido: `postgres`
  - porta: `5432`
  - senha: definir e guardar
- Depois instalar ou habilitar `pgvector` na mesma instância.

## Passo 1: criar banco vazio

Exemplo com usuário `postgres`:

```powershell
createdb -h localhost -p 5432 -U postgres bible_api
```

Se o banco já existir:

```powershell
dropdb -h localhost -p 5432 -U postgres bible_api
createdb -h localhost -p 5432 -U postgres bible_api
```

## Passo 2: garantir extensão vector

```powershell
psql -h localhost -p 5432 -U postgres -d bible_api -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## Passo 3: restaurar o dump

Restore completo:

```powershell
pg_restore -h localhost -p 5432 -U postgres -d bible_api -v "E:\embeding_bibles\bible_api_1M_embeddings_20250922_154638.dump"
```

Se houver erro por objetos já existentes, recrie o banco e rode novamente em banco limpo.

## Passo 4: configurar o projeto para usar o banco local

No `.env`, alinhar:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bible_api
DB_USER=postgres
DB_PASSWORD=<sua_senha>
DATABASE_URL=postgresql://postgres:<sua_senha>@localhost:5432/bible_api
REDIS_URL=redis://127.0.0.1:6379/1
```

Observação:
- sem Redis local, parte do projeto ainda pode subir, mas caches e alguns fluxos podem degradar.
- atalho recomendado: usar o template [`/.env.postgres-local.example`](/C:/Users/Iury%20Coelho/Desktop/bible-api/.env.postgres-local.example) como base e copiar os valores para o `.env`

## Passo 5: validar o banco restaurado

Checagem rápida:

```powershell
python scripts/check_local_postgres_readiness.py
```

Checagem manual:

```powershell
psql -h localhost -p 5432 -U postgres -d bible_api -c "SELECT COUNT(*) FROM versions;"
psql -h localhost -p 5432 -U postgres -d bible_api -c "SELECT COUNT(*) FROM verses;"
psql -h localhost -p 5432 -U postgres -d bible_api -c "SELECT COUNT(*) FROM verse_embeddings;"
psql -h localhost -p 5432 -U postgres -d bible_api -c "SELECT COUNT(*) FROM unified_verse_embeddings;"
psql -h localhost -p 5432 -U postgres -d bible_api -c "SELECT extname FROM pg_extension WHERE extname='vector';"
```

## Passo 6: subir a API sem Docker

```powershell
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

## Passo 7: validar o endpoint híbrido

```powershell
curl "http://127.0.0.1:8000/api/v1/ai/rag/hybrid/?q=amor&top_k=3"
```

## Passo 8: rodar o benchmark piloto

```powershell
python scripts/run_hybrid_benchmark.py --dry-run
python scripts/run_hybrid_benchmark.py --query-id q001 --experiment baseline_hybrid
```

## Se o restore falhar

### Caso 1: `pg_restore` não encontrado
- PostgreSQL local não está instalado ou o `bin` não está no `PATH`.

### Caso 2: erro `extension "vector" is not available`
- PostgreSQL foi instalado sem `pgvector`.
- Alternativa prática: carregar manualmente o tipo `vector` a partir da `vector.dll` em um caminho legível pelo serviço PostgreSQL e restaurar o dump excluindo apenas os itens `EXTENSION vector`.

### Caso 3: restore termina, mas `unified_verse_embeddings` fica vazio
- O dump pode ser mais antigo que a fase unificada.
- Nesse caso, o endpoint ainda pode funcionar com `embedding_source=verse`.

### Caso 4: API responde 404 no benchmark
- Porta `8000` está apontando para outro serviço.
- Ajuste `API_BASE` ou suba a API correta.

## Estratégia recomendada
- Melhor caminho: restaurar o dump e usar `embedding_source=verse` primeiro.
- Só depois confirmar se `unified_verse_embeddings` também veio no backup.
- Isso já é suficiente para rodar a primeira rodada real de benchmark.
