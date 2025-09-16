---
id: T-C04
title: "[data] Respeitar robots.txt e crawl-delay — Catena"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/data", "type/feat", "observability"]
priority: medium
effort: M
risk: low
depends_on: ["T-C02"]
related: ["T-C03"]
epic: "Fase 3: Scraping Avançado de Comentários"
branch: "feat/scraper-robots-crawl-delay"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Precisamos garantir respeito às políticas do site de origem (`catenabible.com`).
- Implementar leitura de `robots.txt` (disallow e `crawl-delay`) e ajustar `--delay` automaticamente.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Baixar e interpretar `https://catenabible.com/robots.txt`
- [ ] CA2 — Se houver `crawl-delay`, aplicá-lo (prioridade sobre `--delay` menor)
- [ ] CA3 — Avisar no log se a rota consultada for disallow (e pular com contagem)
- [ ] CA4 — Cache local simples de `robots.txt` por 24h

## Escopo / Fora do Escopo
- Inclui: fetch e parse de robots, integração no fluxo do scraper, logs
- Não inclui: politeness avançada (fila distribuída, rate per host), retries customizados

## Impacto Técnico
**Contrato**: n/a
**DB**: n/a
**Performance**: pequena latência inicial (download robots); melhor comportamento
**Segurança**: n/a

## Plano de Testes
- Simular `robots.txt` com e sem `crawl-delay`
- Verificar aplicação do delay efetivo > `--delay` quando necessário
- Testar disallow para um path e checar que foi pulado e logado

## Observabilidade
- Logs por início de execução: crawl-delay efetivo, data de expiração do cache
- Métrica (contadores): `scraper_robots_disallowed_total`

## Rollout & Rollback
- Rollout conservador (apenas adiciona politeness)
- Rollback simples (desativar leitura de robots)

## Checklist Operacional (Autor)
- [ ] Logs legíveis e úteis
- [ ] Documentar comportamento no `PROJETO_ORGANIZADO.md`

## Checklist Operacional (Revisor)
- [ ] Validação do delay aplicado
- [ ] Pulos de disallow corretos
