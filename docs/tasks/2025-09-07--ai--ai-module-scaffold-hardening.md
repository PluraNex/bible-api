---
id: T-003-ai-scaffold-hardening
title: "[ai] AI module scaffold hardening — Auth, Docs, Tests"
status: ready            # backlog | ready | in_progress | pr_draft | in_review | merged | done
created: 2025-09-07
updated: 2025-09-07
owner: "@iuryeng"
reviewers: ["@maintainer"]
labels: ["area/ai", "type/feat", "type/test", "needs-schema"]
priority: medium           # low | medium | high | urgent
effort: S                  # XS | S | M | L | XL
risk: low                  # low | medium | high
depends_on: ["T-001-django-setup"]
related: []
epic: "fase-0-boot"
branch: "feat/T-003-ai-scaffold-hardening"
pr: ""
github_issue: ""
due: null
---

## Contexto
- O módulo de AI foi criado com rotas e views stub (T-001), porém há ajustes de segurança e documentação a aplicar.
- Valor: garantir padrões de autenticação/permissão, documentação OpenAPI e testes mínimos antes de evoluir lógica de AI.
- Hipóteses: manter autenticação global via API Key; escopos específicos (ex.: `ai`) serão tratados em task posterior.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Remover `AllowAny` e aplicar autenticação padrão nas rotas `agents/` e `tools/` (401 sem API key).
- [ ] CA2 — Registrar o app `bible.ai` em `INSTALLED_APPS` (padronização).
- [ ] CA3 — Documentar endpoints de AI com `@extend_schema` (summaries, responses 200/501, exemplos mínimos).
- [ ] CA4 — Garantir roteamento: `api/v1/ai/` permanece incluído em `config/urls.py`.
- [ ] CA5 — Testes de API cobrindo 401 sem credencial; 200 em `agents/` e `tools/` com key válida; 501 em `tools/<tool>/test/` e `runs/*`.
- [ ] CA6 — Schema OpenAPI inclui as rotas de AI e valida com Spectacular.
- [ ] CA7 — Sem mudanças de DB; CI verde.

## Escopo / Fora do Escopo
- Inclui: ajustes de auth nas views de listagem, anotações OpenAPI, testes de smoke de AI, registro do app no settings.
- Não inclui: modelos de dados de AI, execução real de agentes/tools, throttle/escopos específicos, integrações externas.

## Impacto Técnico
- Contrato (OpenAPI): inclusão de summaries/responses; sem breaking changes.
- DB/Migrations: nenhuma.
- Throttle/Cache: sem alterações nesta task; scopes/limites ficam para task futura.
- Segurança: reforço de autenticação nas rotas públicas (remover `AllowAny`).

## Plano de Testes
- API:
  - 401: `GET /api/v1/ai/agents/` e `GET /api/v1/ai/tools/` sem `Authorization`.
  - 200: `GET /api/v1/ai/agents/` e `GET /api/v1/ai/tools/` com `Api-Key` válida.
  - 501: `POST /api/v1/ai/tools/<tool>/test/`, `POST /api/v1/ai/agents/<name>/runs/`, `GET /api/v1/ai/runs/<id>/`, `POST /api/v1/ai/runs/<id>/approve/`, `DELETE /api/v1/ai/runs/<id>/cancel/`.
- Contrato: schema gerado contém as rotas; validação Spectacular sem erros.
- Dados: sem necessidade de fixtures; criar usuário e `APIKey` em testes.

## Observabilidade
- Sem alterações; manter logs padrão e respostas determinísticas (501 com mensagem padronizada).

## Rollout & Rollback
- Ativação: aplicar mudanças e rodar testes/CI.
- Sucesso: testes passam; schema inclui rotas de AI; endpoints corretamente protegidos.
- Reversão: revert patch; sem impacto em dados.

## Checklist Operacional (Autor)
- [ ] OpenAPI gerado/commitado em `docs/` se houver alteração de schema visível.
- [ ] `make fmt lint test` ok local.
- [ ] CI verde (lint, migrations-check, tests, schema-diff).
- [ ] PR descreve impacto e próximos passos (escopos/throttle em task futura).

## Checklist Operacional (Revisor)
- [ ] Auth consistente com política global; sem rotas públicas indevidas.
- [ ] Testes suficientes (401/200/501) e determinísticos.
- [ ] OpenAPI claro (summaries/responses).
- [ ] Sem mudanças em DB; sem quebra de contrato.
