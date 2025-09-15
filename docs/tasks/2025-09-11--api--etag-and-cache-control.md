---
id: T-P01
title: "[api] ETag/Last-Modified + Cache-Control em endpoints de leitura"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/api", "type/feat", "performance"]
priority: medium
effort: M
risk: low
depends_on: []
related: []
epic: "Performance em Leitura"
branch: "feat/api-etag-cache"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Melhorar eficiência de leitura com validação condicional e política de cache.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Adicionar `ETag`/`Last-Modified` em books/versions/verses list/detail
- [ ] CA2 — Suportar `If-None-Match`/`If-Modified-Since` (retornar 304)
- [ ] CA3 — Definir `Cache-Control` coerente

## Escopo / Fora do Escopo
- Inclui: mixins/utils para DRF e headers
- Não inclui: invalidadores complexos

## Impacto Técnico
**Contrato**: headers | **Performance**: menor banda e latência

## Plano de Testes
- Requisição subsequente com ETag deve retornar 304

## Observabilidade
- Logs de 304 e acertos de cache

## Rollout & Rollback
- Habilitar por rota; rollback removendo mixins
