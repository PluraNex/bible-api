---
id: T-C05
title: "[data] Salvamento idempotente por hash de conteúdo — evitar regravações"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/data", "type/feat", "performance"]
priority: medium
effort: S
risk: low
depends_on: ["T-C02"]
related: []
epic: "Fase 3: Scraping Avançado de Comentários"
branch: "feat/scraper-idempotent-save"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Hoje o arquivo JSON do versículo é sempre sobrescrito.
- Queremos evitar regravações desnecessárias quando o conteúdo não mudou (idempotência, economia de IO e diffs mais limpos).

## Objetivo e Critérios de Aceite
- [ ] CA1 — Calcular hash estável do payload relevante (ex.: concat de autores+conteúdos)
- [ ] CA2 — Se arquivo existir e hash inalterado, não sobrescrever; logar "unchanged"
- [ ] CA3 — Se mudou, sobrescrever e logar "updated" com tamanho antigo/novo
- [ ] CA4 — Persistir hash no JSON (campo `content_hash`) e/ou arquivo `.hash`

## Escopo / Fora do Escopo
- Inclui: cálculo de hash, comparação antes do write, logs
- Não inclui: versionamento de arquivo, delta storage

## Impacto Técnico
**Contrato**: n/a (campo extra no JSON é opcional)
**DB**: n/a
**Performance**: reduz IO e evita diffs/commits desnecessários
**Segurança**: n/a

## Plano de Testes
- Executar duas vezes no mesmo versículo: segunda execução não regrava
- Alterar pequeno conteúdo e verificar regravação + log "updated"

## Observabilidade
- Métricas: `scraper_files_unchanged_total`, `scraper_files_updated_total`

## Rollout & Rollback
- Rollout seguro; sem efeitos colaterais
- Rollback: remover verificação de hash

## Checklist Operacional (Autor)
- [ ] Hash determinístico documentado
- [ ] Logs claros por versículo

## Checklist Operacional (Revisor)
- [ ] Idempotência verificada localmente
- [ ] Cálculo de hash cobre campos corretos
