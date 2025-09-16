---
id: T-009-health-readiness-metrics
title: "[infra] Health — Liveness, Readiness e Métricas"
status: done
created: 2025-09-13
updated: 2025-09-13
owner: "@iuryeng"
reviewers: ["@maintainer"]
labels: ["area/infra", "type/feat", "observability"]
priority: medium
effort: S
risk: low
depends_on: []
related: ["T-105-prometheus-metrics-endpoint"]
epic: "Fase 2: Observabilidade"
branch: "feat/T-009-health-readiness-metrics"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Existem `/health/` e `/metrics` básicos; precisamos de checks formais para orquestradores e métricas Prometheus consistentes.

## Objetivo e Critérios de Aceite
- [x] CA1 — `GET /health/liveness`: responde 200 sempre que o processo está vivo.
- [x] CA2 — `GET /health/readiness`: valida DB e cache; 200 quando pronto, 503 caso contrário (payload padronizado).
- [x] CA3 — `GET /metrics/prometheus`: expor métricas Prometheus (requests_total, latency buckets, db_connections, cache_ops) em texto.
- [x] CA4 — Documentar integração com Kubernetes probes.

## Escopo / Fora do Escopo
- Inclui: views simples + integração `django-prometheus` ou coletor equivalente.
- Não inclui: alertas (serão definidos em observability ops).

## Impacto Técnico
**Contrato**: novos endpoints sob `/health/` e padronização do `/metrics`.
**DB/Migrations**: nenhuma.
**Segurança**: considerar proteger `/metrics` por IP/rede quando necessário.

## Plano de Testes
- Smoke: 200 liveness; readiness 503 com DB desligado (mockado).
- Métricas: endpoint responde em `text/plain; version=0.0.4`.

## Implementação (parcial)
- [x] Adicionar `django-prometheus` (INSTALLED_APPS, middlewares, engine Postgres instrumentado).
- [x] Rota `GET /metrics/prometheus/` via `django_prometheus.exports.ExportToDjangoView`.
- [x] `docker-compose` com serviço `prometheus` e `prometheus/prometheus.yml` (scraping `web:8000`).
- [x] Testes básicos para content-type e presença de métricas.

## Rollback Plan
- Reverter alterações em `config/settings.py` (remover middlewares e engine wrapper)
- Remover rota `/metrics/prometheus/` de `config/urls.py`
- Remover serviço `prometheus` do `docker-compose.yml` e arquivo `prometheus/prometheus.yml`

## Observabilidade
- Métricas incrementadas por endpoint (status code & método).

## Rollout & Rollback
- Ativação imediata; sem migrações.

## Checklist Operacional (Autor)
- [x] Docs atualizadas (`README`, `API_STANDARDS`).
- [x] make ready  # fmt, lint, test, schema
- [x] make api-test  # smoke endpoints principais

## Checklist Operacional (Revisor)
- [ ] Readiness realmente valida dependências.
- [ ] `/metrics` compatível Prometheus.
