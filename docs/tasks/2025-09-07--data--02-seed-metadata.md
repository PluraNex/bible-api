---
id: T-202
title: "[Data] Criar Script para Popular Metadados Universais"
status: done
created: 2025-09-07
updated: 2025-09-09
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/data", "type/script"]
priority: high
effort: M
risk: medium
depends_on: ["T-201"]
related: ["docs/data/00_DATA_POPULATION_PLAN.md"]
epic: "Fase 0: População da Base de Dados"
branch: "feat/T-202-seed-metadata"
---

## Contexto
Com os modelos alinhados ao blueprint, precisamos de um script para popular as tabelas de base (`Language`, `Testament`, `CanonicalBook`, `BookName`). Estes dados são a fundação para todos os outros scripts de população de conteúdo.

## Objetivo e Critérios de Aceite
- [ ] **CA1:** Criar um novo comando de gerenciamento em `bible/management/commands/seed_metadata.py`.
- [ ] **CA2:** O script deve popular a tabela `Language` com os idiomas a serem suportados (pt-BR, en-US, etc.).
- [ ] **CA3:** O script deve popular a tabela `Testament` (Antigo, Novo, Apócrifo).
- [ ] **CA4:** O script deve conter um dicionário de metadados para os livros canônicos e deuterocanônicos.
- [ ] **CA5:** O script deve usar o dicionário para popular a tabela `CanonicalBook`, incluindo a flag `is_deuterocanonical`.
- [ ] **CA6:** O script deve popular a tabela `BookName` com os nomes e abreviações em múltiplos idiomas para cada `CanonicalBook`.
- [ ] **CA7:** O script deve ser idempotente (usar `get_or_create`) e transacional.
