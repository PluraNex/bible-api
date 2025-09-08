---
id: T-015
title: "[api] Error Model — Polish & Consistency"
status: done            # backlog | ready | in_progress | pr_draft | in_review | merged | done
created: 2025-09-07
updated: 2025-09-08
owner: "@iuryeng"
reviewers: ["@maintainer"]
labels: ["area/api", "type/refactor", "type/docs", "type/test"]
priority: medium
effort: S
risk: low
depends_on: ["T-014"]
related: ["T-007", "T-012"]
epic: "Fundação da API"
branch: "refactor/T-015-error-model-polish"
pr: ""
github_issue: ""
due: null
---

## Contexto
O modelo de erros padronizado (T-014) está implementado e testado. Restam ajustes finos para garantir consistência total entre domínios, schema OpenAPI e headers—sem alterar o contrato principal já entregue.

## Objetivo e Critérios de Aceite
Refinar e padronizar pontos pendentes do Error Model sem mudanças funcionais significativas.

- [x] CA1 — 429 unificado: padronizar o code para `throttled` também em erros custom (`RateLimitError`), atualizar testes e docs.
- [x] CA2 — OpenAPI: aplicar `get_error_responses()` em views de AI e domínios principais (books, verses, themes, crossrefs, versions já coberto).
- [x] CA3 — Headers em OpenAPI: documentar respostas de erro nos endpoints (401/403/404/405/429/500) via componente compartilhado.
- [x] CA4 — Logging filter: remover código morto no middleware; manter logs estruturados via handler.
- [x] CA5 — (Adiado) constants centralizados serão tratados em evolução futura se necessário.
- [x] CA6 — Testes de contrato: componente de erro presente e referenciado (versões + AI + domínios principais).
- [x] CA7 — Não há mudança de nomes adicional; documentação permanece consistente com `throttled`.

## Escopo / Fora do Escopo
- Inclui: ajustes de nomenclatura e documentação; padronização de schema/responses; pequenas mudanças nos testes.
- Não inclui: alteração de payload (continua com `detail`, `code`, `errors?`, `request_id`), mudanças de autenticação ou throttling em si.

## Impacto Técnico
- Contrato: não-breaking (apenas code 429 pode mudar, com depreciação documentada se necessário).
- OpenAPI: melhora de completude (erros e headers documentados).
- Logging: opção por simplificar o pipeline (remover filter) ou conectá-lo.

## Plano de Implementação
1) Unificar code 429 para `throttled` e ajustar testes.
2) Aplicar `get_error_responses()` nas views de AI e domínios bíblicos.
3) Adicionar headers 401/429 nas respostas do OpenAPI (quando suportado pelo spectacular).
4) Tomar decisão sobre `LoggingContextFilter` e aplicar no `LOGGING` ou remover.
5) Introduzir `ERROR_CODES` centralizados (ex.: em `common/constants.py`) e referenciar no handler/docs/tests.
6) Rodar `make ready` e atualizar `docs/openapi-v1.yaml`.

## Plano de Testes
- OpenAPI: schema possui `components.schemas.ErrorResponse` e endpoints referenciam respostas de erro.
- 429: code `throttled` em ambos caminhos (DRF e custom), `Retry-After` presente quando aplicável.
- 401: `WWW-Authenticate` consistente; testes de integração cobrem.
- Sem regressões nos testes existentes.

## Observabilidade
- Cobrir logs com `request_id` como hoje; se conectar filter, checar formatação final.

## Rollout & Rollback
- Rollout pequeno e reversível; se 429 `rate_limit_exceeded` for removido, documentar no PR (depreciação curta).

## Checklist Operacional (Autor)
- [ ] `make fmt lint test` ok
- [ ] Schema atualizado e commitado
- [ ] PR descreve mudanças e impacto (incluindo 429 code)

## Checklist Operacional (Revisor)
- [ ] Erros e headers padronizados no OpenAPI
- [ ] Testes atualizados e determinísticos
- [ ] Logging sem PII; decisão do filter coerente
