---
id: T-DOC01
title: "[docs] Padrões de API — guia oficial (versionamento, auth, erros, i18n, cache)"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/docs", "type/docs"]
priority: high
effort: M
risk: low
depends_on: []
related: ["T-I18N01", "T-T01", "T-S01", "T-OB01", "T-P01"]
epic: "DX & Documentação"
branch: "docs/api-standards"
pr: ""
github_issue: ""
due: null
---

## Contexto
Precisamos consolidar em um único guia os padrões da API para garantir consistência entre domínios e acelerar onboard/PR reviews. O guia deve alinhar com o que já está implementado no projeto e com as tasks vigentes.

Referências no repositório:
- Esquema: `schema.yml`
- Settings/DRF: `config/settings.py`
- Erros: `common/exceptions.py`
- Paginação: `common/pagination.py`
- Middleware: `common/middleware.py`
- Auth/Scopes/OpenAPI: `bible/auth/*`
- Padrões existentes: `docs/openapi-v1.yaml`, `docs/tasks/*`

## Objetivo e Critérios de Aceite
- [ ] CA1 — Documento `docs/API_STANDARDS.md` com seções claras (versionamento, auth/escopos, throttling, erros, paginação, i18n, cache/ETag, observabilidade, OpenAPI, testes, depreciação)
- [ ] CA2 — Referências cruzadas à implementação atual (settings, middleware, exceptions, serializers, views)
- [ ] CA3 — Exemplos OpenAPI e snippets (curl/JS/Python) prontos para copiar
- [ ] CA4 — Política de depreciação e semântica de mudanças por versão
- [ ] CA5 — Padronização de `lang` e `Accept-Language` com precedência e `Vary`
- [ ] CA6 — Linkado em tasks que impactam contrato (i18n, throttling, hardening)

## Escopo / Fora do Escopo
- Inclui: padrões de design/uso, exemplos, referências a arquivos
- Não inclui: alterações de código; serão feitas em tasks dedicadas

## Plano de Testes
- Revisão editorial e consistência com OpenAPI gerada

## Impacto Técnico
**Contrato (OpenAPI)**: documento guia; sem mudanças diretas, mas guia deve orientar futuras alterações
**Segurança**: diretrizes claras para auth, escopos, throttling
**Observabilidade**: diretrizes de logs, métricas e headers

## Observabilidade
- Incluir seções sobre `X-Request-ID`, `WWW-Authenticate`, `Retry-After`, `/metrics`

## Rollout & Rollback
- Rollout: publicar guia e referenciar nas tasks e PR templates
- Rollback: ajustar o documento sem impacto no runtime

## Checklist Operacional (Autor)
- [ ] Guia completo commitado em `docs/API_STANDARDS.md`
- [ ] Links/verificações de arquivos citados conferidos
- [ ] Tasks relacionadas referenciadas no documento

## Checklist Operacional (Revisor)
- [ ] Seções contemplam todos os tópicos críticos
- [ ] Exemplos e parâmetros (`lang`, throttling) coerentes com o código
- [ ] Documento fácil de seguir por devs novos
