---
id: T-203
title: "[Data] Criar Script para Popular Versões em Português"
status: done
created: 2025-09-07
updated: 2025-09-09
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/data", "type/script"]
priority: high
effort: M
risk: low
depends_on: ["T-202"]
related: ["docs/data/00_DATA_POPULATION_PLAN.md"]
epic: "Fase 0: População da Base de Dados"
branch: "feat/T-203-seed-pt-versions"
---

## Contexto
Com os metadados canônicos no lugar, precisamos de um script para popular os textos dos versículos das versões em português, que estão localizadas no diretório `inst/json/`.

## Objetivo e Critérios de Aceite
- [ ] **CA1:** Criar um novo comando de gerenciamento em `bible/management/commands/populate_pt_versions.py`.
- [ ] **CA2:** O script deve ler todos os arquivos `.json` do diretório `inst/json/`.
- [ ] **CA3:** Para cada arquivo, deve criar um registro `Version` associado ao `Language` 'pt-BR'.
- [ ] **CA4:** O script deve usar as abreviações dos livros no JSON para buscar o `CanonicalBook` correspondente na tabela `BookName` (filtrando pelo idioma 'pt-BR').
- [ ] **CA5:** O script deve inserir todos os versículos para cada versão de forma performática, usando `bulk_create`.
- [ ] **CA6:** O script deve ser idempotente: se rodado novamente, deve limpar os versículos antigos da versão e recriá-los para evitar duplicatas.
