---
id: T-S01
title: "[infra] Hardening de produção — segurança e consistência transacional"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/infra", "type/chore", "security"]
priority: high
effort: S
risk: low
depends_on: []
related: []
epic: "Confiabilidade e Segurança"
branch: "feat/prod-hardening"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Garantir configurações seguras em produção (HTTPS, cookies, HSTS) e consistência transacional (`ATOMIC_REQUESTS`).

## Objetivo e Critérios de Aceite
- [ ] CA1 — `DEBUG=False` em prod e `ALLOWED_HOSTS` por env
- [ ] CA2 — Ativar `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`, `SECURE_REFERRER_POLICY`
- [ ] CA3 — `DATABASES['default']['ATOMIC_REQUESTS']=True`
- [ ] CA4 — Documentar variáveis em `.env.example`

## Escopo / Fora do Escopo
- Inclui: ajustes em `config/settings.py` e doc
- Não inclui: WAF/CDN (tratado fora)

## Impacto Técnico
**Contrato**: n/a | **DB**: n/a | **Segurança**: reforçada

## Plano de Testes
- Subir com `DEBUG=0` e verificar headers de segurança e redirects

## Observabilidade
- Logs confirmando modo produção

## Rollout & Rollback
- Feature flags por env; rollback simples revertendo envs

## Checklist Operacional (Autor)
- [ ] `.env.example` atualizado
- [ ] `README.md` seção deploy

## Checklist Operacional (Revisor)
- [ ] Headers presentes em prod
- [ ] Sem regressões locais
