---
id: T-I18N18
title: "[data] I18N — Auditoria de defaults (pendências, JSON e flags)"
status: backlog
created: 2025-09-12
updated: 2025-09-12
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/data", "type/chore", "i18n"]
priority: high
effort: S
risk: low
depends_on: ["T-I18N17"]
related: ["T-I18N08", "T-I18N15"]
epic: "I18N — Suporte Multilíngue"
branch: "chore/i18n-defaults-audit"
pr: ""
github_issue: ""
due: null
---

## Contexto
O comando `prepare_i18n_defaults` (T-I18N17) prepara a base i18n garantindo `Language('pt','en')` e `BookName` defaults por idioma. Para facilitar auditoria contínua, CI e priorização de lacunas (ex.: deuterocanônicos sem PT), precisamos enriquecer o relatório com listagem de pendências, saída JSON e flags de controle — sem alterar o comportamento de escrita padrão.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Flag `--report-only`: executa auditoria completa sem qualquer escrita
- [ ] CA2 — Flag `--report-file=path.json`: salva relatório em JSON com os mesmos dados do console
- [ ] CA3 — Flag `--fail-on-missing`: exit code ≠ 0 quando houver pendências (para CI)
- [ ] CA4 — Flag `--languages=pt,en`: limita a auditoria aos idiomas informados
- [ ] CA5 — Flags `--include-deuterocanon` / `--exclude-deuterocanon` para filtrar conjunto de livros
- [ ] CA6 — Console lista, por idioma, created/updated/skipped/missing[]/coverage_pct; `missing[]` ordenado por `canonical_order`
- [ ] CA7 — JSON inclui `generated_at`, `totals`, e `languages: [{code, created, updated, skipped, missing[], coverage_pct}]`

## Escopo / Fora do Escopo
- Inclui: aprimorar `data/management/commands/prepare_i18n_defaults.py` com as flags e relatórios
- Não inclui: popular novos idiomas (T-I18N08), mudanças de contrato de API ou migrations

## Impacto Técnico
**Contrato**: n/a | **DB**: sem migrations | **Segurança**: n/a | **Performance**: insignificante (consultas de auditoria)

## Plano de Testes
- `--report-only` imprime auditoria sem alterações
- `--report-file` gera JSON válido com estrutura esperada
- `--fail-on-missing` retorna código ≠ 0 quando houver pendências
- `--languages=pt,en` limita corretamente; combina com deuterocanon filters
- Auditoria lista `missing[]` em ordem canônica e valores de cobertura coerentes

## Observabilidade
- Saída console clara e resumida; artefato JSON para consumo por pipelines

## Rollout & Rollback
- Rollout seguro (somente leitura por padrão). Rollback: remover flags adicionais

## Checklist Operacional (Autor)
- [ ] Flags implementadas e documentadas no help do comando
- [ ] Geração de JSON validada (estrutura e conteúdo)
- [ ] `docs/API_STANDARDS.md` §6 atualizado com referência às novas flags

## Checklist Operacional (Revisor)
- [ ] Auditoria funciona em base atual (faltas refletidas)
- [ ] Saída JSON legível e estável
- [ ] Não há regressão no modo padrão (sem flags)
