---
id: T-C06
title: "[data] Extratores separáveis + testes unitários — BS4/cleaning"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/data", "type/refactor", "type/test"]
priority: medium
effort: M
risk: low
depends_on: ["T-C02"]
related: ["T-C05"]
epic: "Fase 3: Scraping Avançado de Comentários"
branch: "feat/scraper-parsers-tests"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Funções de parsing/cleaning estão embutidas no comando, dificultando testes.
- Queremos separar extratores (BS4, limpeza de Firecrawl/manual) em módulo util puro e cobrir com testes unitários.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Extrair funções puras para `data/scraping/utils.py` (ou similar)
- [ ] CA2 — Criar testes unitários com amostras HTML reais/minimizadas (fixtures)
- [ ] CA3 — Cobrir: extração de autor/período, leitura de rodapé, link "Go to Commentary", limpeza e deduplicação básica
- [ ] CA4 — Garantir comportamento idêntico ao atual (mesmo output para amostras)

## Escopo / Fora do Escopo
- Inclui: refactor, criação de módulo util, testes unitários
- Não inclui: testes de integração end‑to‑end (cobertos por execução manual)

## Impacto Técnico
**Contrato**: n/a
**DB**: n/a
**Performance**: neutro
**Segurança**: n/a

## Plano de Testes
- `pytest -q` com novos testes em `tests/data/` (ou `tests/scraping/`)
- Asserts para campos extraídos e conteúdo limpo (sem navegação/menu)

## Observabilidade
- n/a

## Rollout & Rollback
- Rollout seguro; mantendo API interna do comando
- Rollback simples (reverter refactor)

## Checklist Operacional (Autor)
- [ ] Cobertura > 80% nas novas funções
- [ ] `make fmt lint test` ok

## Checklist Operacional (Revisor)
- [ ] Amostras HTML claras e pequenas
- [ ] Sem regressões visíveis
