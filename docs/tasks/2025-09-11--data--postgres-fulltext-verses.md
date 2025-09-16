---
id: T-DB01
title: "[data] Full-text search Postgres em Verse.text"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/data", "type/feat", "performance"]
priority: low
effort: L
risk: medium
depends_on: []
related: []
epic: "Performance em Leitura"
branch: "feat/verses-fulltext"
pr: ""
github_issue: ""
due: null
---

## Contexto
- `icontains` em textos longos é ineficiente. Adotar FTS (GIN + `to_tsvector`).

## Objetivo e Critérios de Aceite
- [ ] CA1 — Migrar para coluna tsv e índice GIN
- [ ] CA2 — Ajustar buscas para usar FTS com idioma
- [ ] CA3 — Filtro de fallback quando FTS indisponível (dev)

## Escopo / Fora do Escopo
- Inclui: migração, manager/querysets utilitários
- Não inclui: UI de ranking avançado

## Impacto Técnico
**DB**: migração e índices grandes | **Performance**: grande ganho

## Plano de Testes
- Consultas FTS retornam resultados esperados e rápidos

## Observabilidade
- Métricas de tempo de busca (p95)

## Rollout & Rollback
- Criar índice concurrently; rollback drop do índice
