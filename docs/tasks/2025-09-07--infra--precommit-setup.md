---
id: T-006-precommit-setup
title: "[infra] Pre-commit hooks — black, ruff, end-of-line"
status: backlog
created: 2025-09-07
updated: 2025-09-07
owner: "@iuryeng"
reviewers: ["@maintainer"]
labels: ["area/infra", "type/chore", "type/test"]
priority: medium
effort: S
risk: low
depends_on: []
related: ["T-005-url-domain-refactor"]
epic: "Fase 1: Core Funcional"
branch: "chore/T-006-precommit-setup"
pr: ""
github_issue: ""
due: null
---

## Contexto
- Falhas de CI por formatação/linters (black/ruff) e diferenças de EOL entre ambientes (
 vs \n).
- Queremos feedback rápido local antes de commits/PRs.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Adicionar `.pre-commit-config.yaml` com hooks: ruff (lint+fix), black, end-of-file-fixer, trailing-whitespace.
- [ ] CA2 — Adicionar `.gitattributes` (LF) e validar comportamento em Linux/Windows.
- [ ] CA3 — Documentar no README como instalar e rodar: `pre-commit install` e `pre-commit run --all-files`.
- [ ] CA4 — Job de CI (lint-and-format) usa as mesmas versões (paridade local/CI).
- [ ] CA5 — Rodar `pre-commit run --all-files` e commitar ajustes iniciais.

## Escopo / Fora do Escopo
- Inclui: configuração de hooks, documentação, primeiro run.
- Não inclui: criação de hooks customizados complexos; apenas os básicos.

## Impacto Técnico
- Contrato/API: nenhum.
- DB: nenhum.
- CI: consistência entre local e pipeline.

## Plano
1) Criar `.pre-commit-config.yaml` com:
   - repo: https://github.com/astral-sh/ruff-pre-commit (ruff, ruff-format opcional)
   - repo: https://github.com/psf/black (black)
   - repo: https://github.com/pre-commit/pre-commit-hooks (end-of-file-fixer, trailing-whitespace)
2) Adicionar instruções ao README.
3) Rodar `pre-commit run --all-files` e commitar.
4) Validar no CI (lint step deve passar).

## Testes
- Executar `pre-commit run --all-files` localmente sem erros.
- CI verde na etapa lint-and-format.
