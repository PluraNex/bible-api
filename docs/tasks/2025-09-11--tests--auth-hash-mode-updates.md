---
id: T-TS02
title: "[tests] Atualizar suite de auth para modo hash de API Keys"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/auth", "type/test", "security"]
priority: high
effort: S
risk: low
depends_on: ["T-S02"]
related: ["T-TS01"]
epic: "Qualidade e Confiabilidade"
branch: "test/auth-hash-mode"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Após migração para hash, fixtures e asserts de auth precisam refletir novo fluxo.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Fixtures criam chaves e validam autenticação pelo hash
- [ ] CA2 — Testes garantem que chave completa só aparece no momento da criação
- [ ] CA3 — Falhas de auth adequadas (mensagens/401)

## Escopo / Fora do Escopo
- Inclui: atualização de `tests/auth/*`
- Não inclui: mudanças funcionais além da migração

## Impacto Técnico
**Segurança**: validada | **CI**: mantém cobertura

## Plano de Testes
- Executar suite de auth; tudo verde

## Observabilidade
- n/a

## Rollout & Rollback
- Apenas testes; rollback não aplicável
