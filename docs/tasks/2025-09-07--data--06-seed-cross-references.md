---
id: T-206
title: "[Data] Criar Script para Popular Referências Cruzadas"
status: done
created: 2025-09-07
updated: 2025-09-09
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/data", "type/script"]
priority: high
effort: M
risk: medium
depends_on: ["T-202"]
related: ["docs/data/00_DATA_POPULATION_PLAN.md"]
epic: "Fase 0: População da Base de Dados"
branch: "feat/T-206-seed-cross-references"
---

## Contexto
Com todos os livros canônicos devidamente registrados, podemos popular a tabela de referências cruzadas, que é agnóstica à versão. Os dados virão do arquivo `cross_references.txt`.

## Objetivo e Critérios de Aceite
- [ ] **CA1:** Criar um novo comando de gerenciamento em `bible/management/commands/populate_cross_references.py`.
- [ ] **CA2:** O script deve ler e processar o arquivo `bible_databases-2024/cross_references.txt`.
- [ ] **CA3:** O script deve conter uma função para "parsear" as strings de referência (ex: `Gen.1.1` e `Prov.8.22-30`) e extrair as abreviações e números.
- [ ] **CA4:** O script deve usar as abreviações para buscar os `CanonicalBook` correspondentes.
- [ ] **CA5:** O script deve criar os registros `CrossReference` com os dados canônicos (`from_book`, `to_book`, etc.) e o campo `votes`.
- [ ] **CA6:** O script deve usar `bulk_create` para a inserção em massa.
- [ ] **CA7:** O script deve ser idempotente.
