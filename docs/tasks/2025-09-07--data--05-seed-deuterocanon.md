---
id: T-205
title: "[Data] Criar Script para Popular Livros Deuterocanônicos"
status: done
created: 2025-09-07
updated: 2025-09-09
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/data", "type/script"]
priority: medium
effort: M
risk: low
depends_on: ["T-202"]
related: ["docs/data/00_DATA_POPULATION_PLAN.md"]
epic: "Fase 0: População da Base de Dados"
branch: "feat/T-205-seed-deuterocanon"
---

## Contexto
Os textos para os livros deuterocanônicos estão em um repositório separado (`bible_databases_deuterocanonical/`) e precisam ser populados em uma versão específica.

## Objetivo e Critérios de Aceite
- [ ] **CA1:** Criar um novo comando de gerenciamento em `bible/management/commands/populate_deuterocanon.py`.
- [ ] **CA2:** O script deve criar um registro `Version` específico para este conjunto (ex: 'EN_APOCRYPHA').
- [ ] **CA3:** O script deve iterar sobre os subdiretórios de `bible_databases_deuterocanonical/sources/en/`.
- [ ] **CA4:** Para cada livro, deve buscar o `CanonicalBook` correspondente (que já está marcado como `is_deuterocanonical=True` pela tarefa T-202).
- [ ] **CA5:** O script deve ler o arquivo `.json` de cada livro e usar `bulk_create` para inserir os versículos.
- [ ] **CA6:** O script deve ser idempotente.
