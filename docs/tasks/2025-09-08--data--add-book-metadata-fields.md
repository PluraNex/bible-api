---
id: T-D01
title: "[data] Adicionar campos de metadados (context/outline) ao modelo CanonicalBook"
status: done
created: 2025-09-08
updated: 2025-09-09
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/data", "type/feat"]
priority: high
effort: XS
risk: low
depends_on: []
related: ["T-B01"]
epic: "Fase 1: Implementação de Endpoints Base da API"
branch: "feat/data-book-metadata-fields"
pr: ""
github_issue: ""
due: null
---

## Contexto
Esta é uma tarefa pré-requisito para a `T-B01`. Para implementar os endpoints de `context` e `outline` para os livros, precisamos de um local no banco de dados para armazenar essa informação. O modelo `CanonicalBook` atual não possui campos para dados editoriais ricos.

Esta tarefa implementa a solução mais simples e rápida (Opção 1, conforme discutido) para desbloquear o desenvolvimento dos endpoints, adicionando campos `JSONField` ao modelo existente.

## Objetivo e Critérios de Aceite
O objetivo é modificar o modelo `CanonicalBook` para suportar o armazenamento de dados de contexto e esboço.

- [ ] **CA1:** O modelo `CanonicalBook` em `bible/models/books.py` é atualizado para incluir dois novos campos: `outline_data` e `context_data`, ambos do tipo `models.JSONField` e configurados para serem `null=True, blank=True`.
- [ ] **CA2:** Um novo arquivo de migração é gerado com sucesso no diretório `bible/migrations/` após a alteração do modelo, usando o comando `make makemigrations` ou `python manage.py makemigrations bible`.
- [ ] **CA3:** A nova migração é aplicada ao banco de dados sem erros usando o comando `make migrate` ou `python manage.py migrate`.
- [ ] **CA4:** A alteração é não-destrutiva. Os dados existentes na tabela `canonical_books` permanecem intactos após a migração.

## Escopo / Fora do Escopo
- **Inclui:**
    - Modificar o arquivo `bible/models/books.py`.
    - Gerar e verificar um novo arquivo de migração do Django.
- **Não inclui:**
    - Popular os novos campos com dados. Isso será feito em uma tarefa separada ou como parte da T-B01.
    - Implementar os endpoints da API que consumirão esses campos.

## Impacto Técnico
**Contrato (OpenAPI)**: Nenhum. Esta alteração não afeta a API diretamente.
**DB/Migrations**: Sim, será criada uma nova migração para adicionar duas colunas `jsonb` (no PostgreSQL) à tabela `canonical_books`. A alteração é reversível e não deve causar downtime.
**Performance**: Impacto de performance insignificante, pois os novos campos são nulos por padrão e não serão carregados em queries a menos que explicitamente solicitados.

## Plano de Testes
- O teste principal é a aplicação bem-sucedida da migração em um banco de dados limpo e em um banco de dados com dados existentes.
- Verificar se os testes existentes que criam instâncias de `CanonicalBook` continuam passando sem modificações.

## Observabilidade
- Nenhuma métrica, log ou alerta novo é necessário para esta alteração de modelo.
- A migração será registrada nos logs padrão do Django durante o deploy.

## Rollout & Rollback
- **Rollout**: Aplicar a migração (`manage.py migrate`) durante o processo de deploy.
- **Rollback**: Reverter a migração específica usando seu número de versão (ex: `manage.py migrate bible <numero_da_migracao_anterior>`).

## Checklist Operacional (Autor)
- [ ] `make fmt lint test` ok local
- [ ] CI verde (lint, migrations-check, tests, schema-diff)
- [ ] PR descreve impacto e rollback

## Checklist Operacional (Revisor)
- [ ] Migration é aditiva e reversível.
- [ ] Testes existentes não foram quebrados.
