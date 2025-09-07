---
id: T-<número-ou-slug>
title: "[area] <ação> — <resultado>"
status: backlog            # backlog | ready | in_progress | pr_draft | in_review | merged | done
created: YYYY-MM-DD
updated: YYYY-MM-DD
owner: "@usuario-ou-agente"
reviewers: ["@revisor1", "@revisor2"]
labels: ["area/api", "type/feat"]
priority: medium           # low | medium | high | urgent
effort: S                  # XS | S | M | L | XL
risk: low                  # low | medium | high
depends_on: []
related: []
epic: "<nome-do-epico-ou-fase>"
branch: "feat/<slug>"
pr: ""                     # URL do PR quando existir
github_issue: ""           # URL da issue no GitHub
due: null
---

## Contexto
- Problema / oportunidade
- Valor para o usuário / sistema
- Hipóteses e restrições

## Objetivo e Critérios de Aceite
- [ ] CA1 — …
- [ ] CA2 — …

## Escopo / Fora do Escopo
- Inclui: …
- Não inclui: …

## Impacto Técnico
**Contrato (OpenAPI)**: muda? (rotas, campos, exemplos, deprecated)
**DB/Migrations**: quais? backward-compat? volume/tempo?
**Throttle/Cache**: escopos e política
**Performance**: orçamento (p95 local), risco de N+1
**Segurança**: PII, auth, permissões, rate limit

## Plano de Testes
**API**: casos (+ códigos 200/201/204/400/401/403/404/422/429 conforme)
**Contrato**: exemplos e validação do schema
**Dados**: fábricas mínimas, constraints do DB

## Observabilidade
- Métricas/Logs/Alertas alterados/novos
- Request ID, erros padronizados
- Health/metrics afetados?

## Rollout & Rollback
- Plano de ativação
- Critérios de sucesso/falha
- Estratégia de reversão

## Checklist Operacional (Autor)
- [ ] OpenAPI gerado/commitado em `docs/` (se houve mudança)
- [ ] `make fmt lint test` ok local
- [ ] CI verde (lint, migrations-check, tests, schema-diff)
- [ ] PR descreve impacto e rollback

## Checklist Operacional (Revisor)
- [ ] Contrato estável ou depreciação formal
- [ ] Testes suficientes (felizes + erros + auth + throttle + paginação/ordenação/filtros)
- [ ] Sem N+1; p95 dentro do orçamento
- [ ] Migrations pequenas e reversíveis
- [ ] Segurança: sem PII em logs; escopos e rate adequados
- [ ] Cache/invalidação documentados
