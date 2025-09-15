---
id: T-ER01
title: "[api] Tratamento de exceções específico em Verses — remover catch amplo"
status: backlog
created: 2025-09-11
updated: 2025-09-11
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/api", "type/fix"]
priority: medium
effort: S
risk: low
depends_on: []
related: []
epic: "Qualidade de Erros"
branch: "fix/verses-specific-exceptions"
pr: ""
github_issue: ""
due: null
---

## Contexto
- `bible/verses/views.py` usa `except Exception:` ao buscar livro/capítulo.

## Objetivo e Critérios de Aceite
- [ ] CA1 — Capturar `CanonicalBook.DoesNotExist` e retornar 404 claro
- [ ] CA2 — Validar `chapter` (int > 0) e retornar 400 quando inválido
- [ ] CA3 — Manter payload padronizado pelo `custom_exception_handler`

## Escopo / Fora do Escopo
- Inclui: ajustes na view e testes
- Não inclui: mudanças de contrato

## Impacto Técnico
**Contrato**: mensagens mais claras | **Segurança**: n/a

## Plano de Testes
- Casos de livro inexistente (404) e capítulo inválido (400)

## Observabilidade
- Logs de erro reduzidos (sem catch amplo)

## Rollout & Rollback
- Mudança local simples; rollback trivial
