---
id: T-DP01
title: "[infra] Deploy com Gunicorn + Whitenoise — substituir runserver"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/infra", "type/chore", "performance"]
priority: high
effort: M
risk: low
depends_on: ["T-S01"]
related: []
epic: "Confiabilidade e Segurança"
branch: "feat/deploy-gunicorn-whitenoise"
pr: ""
github_issue: ""
due: null
---

## Contexto
- `runserver` não é para produção. Adotar Gunicorn e servir estáticos com Whitenoise.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Docker com CMD `gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60`
- [ ] CA2 — `whitenoise` configurado no `MIDDLEWARE` e estáticos coletados
- [ ] CA3 — `docker-compose` separado dev/prod ou flags por env

## Escopo / Fora do Escopo
- Inclui: Dockerfile, settings, compose
- Não inclui: Nginx/Reverse proxy (futuro)

## Impacto Técnico
**Performance**: melhor | **Segurança**: melhor

## Plano de Testes
- Subir container prod e validar estáticos e resposta sob carga leve

## Observabilidade
- Logs do Gunicorn no stdout

## Rollout & Rollback
- Rollout progressivo; rollback para `runserver` com flag env
