---
id: T-C03
title: "[data] Firecrawl por ENV + validação — chave e fallback"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/data", "type/chore", "security"]
priority: high
effort: S
risk: low
depends_on: ["T-C02"]
related: []
epic: "Fase 3: Scraping Avançado de Comentários"
branch: "feat/scraper-firecrawl-env"
pr: ""
github_issue: ""
due: null
---

## Contexto
- O scraper híbrido (`scrape_catena_bible.py`) possui placeholder de chave do Firecrawl no código.
- Precisamos ler a chave via variável de ambiente (`FIRECRAWL_API_KEY`), validar quando necessário e manter fallback robusto quando ausente.
- Benefícios: segurança, facilidade operacional e execução previsível em diferentes ambientes.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Chave lida de `FIRECRAWL_API_KEY` (sem valor hardcoded no código)
- [ ] CA2 — Flag `--force-firecrawl` exige chave válida e falha com mensagem clara se ausente
- [ ] CA3 — Quando sem chave (ou erro), fallback para extração manual/BS4 permanece funcional
- [ ] CA4 — Logs informam modo em uso (firecrawl/manual) por versículo

## Escopo / Fora do Escopo
- Inclui: leitura de env, flag CLI, mensagens e logs
- Não inclui: métricas/observabilidade (cobertas em outra task), testes unitários extensivos

## Impacto Técnico
**Contrato (OpenAPI)**: não muda
**DB/Migrations**: n/a
**Throttle/Cache**: n/a
**Performance**: neutro (melhora UX operacional)
**Segurança**: evita exposição de credenciais no código

## Plano de Testes
- Execução com `FIRECRAWL_API_KEY` definida → usa Firecrawl; logs confirmam
- Execução sem chave → fallback manual; logs confirmam
- Execução com `--force-firecrawl` sem chave → falha com mensagem clara (exit code ≠ 0)

## Observabilidade
- Logs estruturados indicando: método de extração, URL de destino, resultado (success/fallback)

## Rollout & Rollback
- Rollout: variável de ambiente em `docker-compose.yml`/CI
- Sucesso: comandos funcionam com e sem key; sem credenciais no código
- Rollback: remover flag e leitura de env sem efeitos colaterais

## Checklist Operacional (Autor)
- [ ] `make fmt lint test` ok
- [ ] Docs do comando atualizadas em `PROJETO_ORGANIZADO.md`

## Checklist Operacional (Revisor)
- [ ] Sem credenciais hardcoded
- [ ] CLI e mensagens claras
- [ ] Logs úteis e não verborrágicos
