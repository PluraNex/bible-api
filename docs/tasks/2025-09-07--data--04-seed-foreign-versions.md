---
id: T-204
title: "[Data] Criar Script para Popular Versões em Outros Idiomas"
status: done
created: 2025-09-07
updated: 2025-09-09
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/data", "type/script"]
priority: medium
effort: M
risk: medium
depends_on: ["T-202"]
related: ["docs/data/00_DATA_POPULATION_PLAN.md"]
epic: "Fase 0: População da Base de Dados"
branch: "feat/T-204-seed-foreign-versions"
---

## Contexto
Precisamos popular os textos de versões em outros idiomas (primariamente inglês) a partir dos dados no diretório `bible_databases-2024/`.

## Objetivo e Critérios de Aceite
- [ ] **CA1:** Criar um novo comando de gerenciamento em `bible/management/commands/populate_foreign_versions.py`.
- [ ] **CA2:** O script deve ser capaz de processar os formatos de dados encontrados no diretório `bible_databases-2024/` (JSON, CSV, etc.).
- [ ] **CA3:** Para cada versão, deve criar um registro `Version` associado ao `Language` correto (ex: 'en-US').
- [ ] **CA4:** O script deve usar as abreviações dos livros para buscar o `CanonicalBook` correspondente na tabela `BookName` (filtrando pelo idioma apropriado).
- [ ] **CA5:** O script deve usar `bulk_create` para a inserção dos versículos.
- [ ] **CA6:** O script deve ser idempotente.
