---
id: T-201
title: "[Data] Refatorar Modelos para Alinhamento com Blueprint"
status: backlog
created: 2025-09-07
owner: "@gemini"
reviewers: ["@IuryAlves"]
labels: ["area/data", "type/refactor"]
priority: urgent
effort: M
risk: high
depends_on: []
related: ["docs/data/00_DATA_POPULATION_PLAN.md"]
epic: "Fase 0: População da Base de Dados"
branch: "refactor/T-201-model-alignment"
---

## Contexto
A população de dados definitiva requer que os modelos do Django (`Language`, `CanonicalBook`, `Version`, `Verse`, `CrossReference`, etc.) estejam perfeitamente alinhados com a arquitetura de referência. A estrutura atual é simplificada e incompatível com os scripts de seeding planejados.

## Objetivo e Critérios de Aceite
- [ ] **CA1:** Refatorar todos os modelos de dados para corresponderem exatamente à estrutura definida em `docs/architecture/BIBLE_API_BASE_PROJECT.md`.
- [ ] **CA2:** Substituir o modelo `Book` pela estrutura `Testament`, `CanonicalBook` e `BookName`.
- [ ] **CA3:** Ajustar o modelo `CrossReference` para ser canônico e agnóstico à versão.
- [ ] **CA4:** Ajustar os modelos `Version` e `APIKey` para incluir todos os campos do blueprint.
- [ ] **CA5:** Gerar e revisar as migrações de banco de dados resultantes das alterações.
- [ ] **CA6:** Garantir que os testes existentes (se aplicável) sejam adaptados e passem com a nova estrutura de modelos.
