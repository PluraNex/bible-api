---
id: T-OB02
title: "[infra] Métricas Prometheus — endpoint /metrics"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/infra", "observability", "type/feat"]
priority: medium
effort: S
risk: low
depends_on: []
related: []
epic: "Observabilidade"
branch: "feat/prometheus-metrics"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Substituir métricas estáticas por integração com `prometheus_client` (ou `django-prometheus`).

## Objetivo e Critérios de Aceite
- [ ] CA1 — Expor `/metrics` com métricas padrão de processo/HTTP
- [ ] CA2 — Coletores básicos habilitados (tempo, contadores de requests)
- [ ] CA3 — Documentar scrape no Prometheus

## Escopo / Fora do Escopo
- Inclui: integração básica
- Não inclui: dashboards Grafana (futuro)

## Impacto Técnico
**Contrato**: novo endpoint | **Segurança**: considerar proteção em prod

## Plano de Testes
- Chamar `/metrics` e validar formato

## Rollout & Rollback
- Gate por env; rollback removendo rota
