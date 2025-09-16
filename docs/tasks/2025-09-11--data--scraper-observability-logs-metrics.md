---
id: T-C07
title: "[data] Observabilidade do scraper — logs estruturados + métricas"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/data", "observability", "type/chore"]
priority: medium
effort: S
risk: low
depends_on: ["T-C02"]
related: ["T-C04", "T-C05"]
epic: "Fase 3: Scraping Avançado de Comentários"
branch: "feat/scraper-observability"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Queremos melhorar a visibilidade operacional do scraper: sucesso/falhas por versículo, tentativas, método de extração, tempos e arquivos atualizados.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Logs estruturados por versículo: `{book,chapter,verse,method,attempts,duration_ms,result}`
- [ ] CA2 — Contadores de métricas: `scraper_commentaries_total`, `scraper_fullcontent_success_total`, `scraper_errors_total`
- [ ] CA3 — Tempo médio por versículo (pelo menos via logs; métrica opcional)

## Escopo / Fora do Escopo
- Inclui: logging estruturado e contadores locais (ex.: console, CSV opcional)
- Não inclui: integração Prometheus (coberto em epic de observabilidade geral)

## Impacto Técnico
**Contrato**: n/a
**DB**: n/a
**Performance**: overhead mínimo
**Segurança**: evitar logar URLs com tokens/PII

## Plano de Testes
- Executar scraper em `--verbose` e validar presença dos campos nos logs
- Validar contagem coerente dos totais após execução

## Observabilidade
- Logs com `request_id` (quando disponível) e contexto por versículo

## Rollout & Rollback
- Rollout incremental e seguro
- Rollback simples (reduzir verbosidade)

## Checklist Operacional (Autor)
- [ ] Documentar exemplos de logs e métricas no `PROJETO_ORGANIZADO.md`

## Checklist Operacional (Revisor)
- [ ] Logs úteis para troubleshooting
- [ ] Métricas coerentes com execução
