---
id: T-RAG01-embeddings-pgvector
title: "[rag] Embeddings + pgvector — schema, índices e scripts"
status: ready
created: 2025-09-13
updated: 2025-09-13
owner: "@iuryeng"
reviewers: ["@maintainer"]
labels: ["area/rag", "type/schema", "type/script", "pgvector"]
priority: high
effort: M
risk: medium
depends_on: []
related: ["T-RAG02-retriever-service-api", "T-011-books-by-author"]
epic: "RAG + Agents"
branch: "feat/T-RAG01-embeddings-pgvector"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Precisamos armazenar embeddings por versículo para consulta vetorial (recall + rerank) com pgvector.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Criar tabela `verse_embeddings` com colunas: verse_canonical_id, version_code, model_name, dim, embedding_small (vector), embedding_large (vector), created_at.
- [ ] CA2 — Índices pgvector (IVFFlat) em `embedding_small` (cosine) e, opcionalmente, `embedding_large`.
- [ ] CA3 — Script `scripts/embeddings.py` para gerar e inserir embeddings (small 512, large 1024).
- [ ] CA4 — Normalização de texto para embeddings (limpeza consistente e determinística).
- [ ] CA5 — Flags por versão via settings (RAG_ALLOWED_VERSIONS) para controlar o que será indexado.

## Escopo / Fora do Escopo
- Inclui: schema, índices, scripts; política de versões por settings.
- Não inclui: serviço retriever HTTP (T-RAG02).

## Impacto Técnico
**DB**: nova tabela + índices pgvector; volume por versão conforme plano.
**Performance**: criação de índice IVFFlat com número de listas adequado (nlist), ajustar `ANALYZE`.

## Plano de Testes
- Smoke: inserir poucos versos e validar consulta kNN simples (SQL).
- Verificar tempo de inserção e consulta.

## Observabilidade
- Logar contagem, tempo por batch e memória em `scripts/embeddings.py`.

## Rollout & Rollback
- Aplicar migração; para rollback, dropar tabela/índices.

## Checklist Operacional (Autor)
- [ ] `make fmt lint` ok
- [ ] Migração aplicada local

## Checklist Operacional (Revisor)
- [ ] Schema e índices coerentes
- [ ] Scripts idempotentes (podem retomar)
