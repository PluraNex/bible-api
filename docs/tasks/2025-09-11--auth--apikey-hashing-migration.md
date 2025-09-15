---
id: T-S02
title: "[auth] Hash de API Keys + migração — segurança de credenciais"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/auth", "type/refactor", "security"]
priority: high
effort: L
risk: medium
depends_on: []
related: ["T-TS02"]
epic: "Confiabilidade e Segurança"
branch: "feat/auth-apikey-hashing"
pr: ""
github_issue: ""
due: null
---

## Contexto
- API keys são armazenadas em texto puro. Precisamos migrar para `key_hash` (SHA-256 + salt) e `key_prefix`.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Modelo com `key_hash` (indexado) e `key_prefix` (exibição), manter `key` apenas na criação
- [ ] CA2 — Autenticação compara por hash; exibe somente prefixo publicamente
- [ ] CA3 — Migração populando hash/prefix de chaves existentes
- [ ] CA4 — Atualizar criação de chave e serializers; não vazar chave após criação
- [ ] CA5 — Testes de autenticação e permissões atualizados

## Escopo / Fora do Escopo
- Inclui: modelo, migração, auth, serializers, testes
- Não inclui: rotação/expiração automática (task futura)

## Impacto Técnico
**Contrato**: n/a | **DB**: migração com dados | **Segurança**: reforçada

## Plano de Testes
- Autenticação com chave válida (hash) funciona
- Chave inválida falha
- Serializers não retornam chave após criação

## Observabilidade
- Logs não devem conter chaves ou hashes

## Rollout & Rollback
- Rollout com migração segura; backup antes
- Rollback: reverter migração e código

## Checklist Operacional (Autor)
- [ ] Cobertura de testes ≥ 80% na camada auth

## Checklist Operacional (Revisor)
- [ ] Sem vazamento de PII/segredos em logs
- [ ] Migração idempotente e reversível
