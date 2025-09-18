---
id: T-CR02
title: "[api] Cross-References -> Hardening, Filters e Cache"
status: done
created: 2025-09-17
updated: 2025-09-17
owner: "@codex"
reviewers: ["@iuryeng"]
labels: ["area/api", "type/refactor", "type/feat", "type/perf"]
priority: medium
effort: M
risk: medium
depends_on: ["T-010-crossrefs-fix"]
related: []
epic: "Fase 2: UX & Discoverability"
branch: "feat/T-CR02-crossrefs-hardening"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Endpoint `/api/v1/bible/cross-references/for/` ainda aceita `ref` inválida e devolve o dataset completo.
- Falta filtros por fonte/confiança e limite configurável para reduzir ruído e payloads grandes.
- Fluxo por tema não respeita o `theme_id` e não alavanca a modelagem canônica.
- Caching curto não foi aplicado, mesmo com forte chance de repetição das mesmas consultas.

## Objetivo e Critérios de Aceite
- [x] CA1 -> Validar `ref` observando parsing e retornar 400 quando faltar livro/capítulo/verso.
- [x] CA2 -> Permitir filtros `source`, `min_confidence` e `limit` (aliás de page size) no endpoint `/for/` e `/by-theme/`.
- [x] CA3 -> Responder payload enriquecido com `summary` (total, fontes, faixa de confiança) sem quebrar o formato atual de paginação.
- [x] CA4 -> `by-theme/<id>/` deve usar `VerseTheme` para buscar apenas referências ligadas ao tema.
- [x] CA5 -> Aplicar cache curto (e.g. 60s) e cobrir caminhos felizes/erro nos testes.

## Escopo / Fora do Escopo
- Inclui: ajustes nas views/serializers/pagination dos crossrefs, testes de API, documentação de task.
- Não inclui: geração de novas referências ou alterações no modelo de dados.

## Impacto Técnico
**Contrato (OpenAPI)**: adiciona filtros documentados e campo `summary`; manter compatibilidade.
**DB/Migrations**: sem novas migrações; uso de EXISTS em consultas por tema.
**Throttle/Cache**: adiciona `cache_page` (60s) aos endpoints `/for/` e agregados.
**Performance**: filtros evitam full scans; cache reduz consultas repetidas; limites respeitam `max_page_size`.
**Segurança**: sem mudanças de auth; validar entradas reduz ataques de scraping pesado.

## Plano de Testes
**API**: 200 com filtros, 400 para `ref` inválido, 404 para tema inexistente, 200 para grouped mantendo summary.
**Contrato**: ajustar exemplos futuramente se necessário (fora do escopo imediato).
**Dados**: fixtures mínimas em testes existentes, garantindo constraints.

## Observabilidade
- Logs padrão continuam; considerar métricas futuras (fora do escopo).
- Mensagens de erro preservam padrão centralizado.

## Rollout & Rollback
- Deploy simples; purgar cache após rollout.
- Rollback remove novos filtros/summary e decorators de cache.

## Checklist Operacional (Autor)
- [ ] OpenAPI gerado/commitado em `docs/` (se necessário).
- [ ] `make fmt lint test` ok local.
- [ ] CI verde (lint, migrations-check, tests, schema-diff).
- [ ] PR descreve impacto e rollback.

## Checklist Operacional (Revisor)
- [ ] Contrato estável ou depreciação formal.
- [ ] Testes cobrem filtros e erros.
- [ ] Sem N+1; desempenho dentro do esperado.
- [ ] Cache documentado e TTL apropriado.
