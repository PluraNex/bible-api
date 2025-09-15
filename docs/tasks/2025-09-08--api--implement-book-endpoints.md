---
id: T-B01
title: "[api] Implementar endpoints do domínio 'Books'"
status: ready
created: 2025-09-08
updated: 2025-09-09
owner: "@gemini-agent"
reviewers: ["@revisor-principal"]
labels: ["area/api", "type/feat"]
priority: high
effort: M
risk: low
depends_on: ["T-D01"]
related: []
epic: "Fase 1: Implementação de Endpoints Base da API"
branch: "feat/api-books-endpoints"
pr: ""
github_issue: ""
due: null
---

## Contexto
O blueprint da arquitetura (`BIBLE_API_BASE_PROJECT.md`) define um conjunto rico de endpoints para o domínio de Livros (Books). A implementação atual é parcial, com apenas 3 dos 9 endpoints definidos no blueprint implementados. Esta tarefa visa expandir os endpoints existentes para cobrir todas as funcionalidades de consulta de livros previstas no blueprint, fornecendo uma interface completa e consistente para os consumidores da API.

Os endpoints já implementados são:
- `GET /books/` (BookListView)
- `GET /books/<book_name>/chapters/` (ChaptersByBookView)
- `GET /books/<book_name>/info/` (BookInfoView)

Os endpoints que precisam ser implementados são:
- `GET /books/by-author/<str:author_name>/` (BooksByAuthorView)
- `GET /books/by-testament/<int:testament_id>/` (BooksByTestamentView)
- `GET /books/<str:book_name>/outline/` (BookOutlineView)
- `GET /books/<str:book_name>/context/` (BookContextView)
- `GET /books/<str:book_name>/structure/` (BookStructureView)
- `GET /books/<str:book_name>/statistics/` (BookStatisticsView)

## Objetivo e Critérios de Aceite
O objetivo é implementar todas as views, serializers e rotas necessárias para o domínio 'Books'.

- [ ] **CA1:** Todas as 9 rotas definidas na especificação da tarefa estão implementadas e retornam `200 OK` para requisições válidas.
- [ ] **CA2:** Endpoints que dependem de um recurso específico (ex: `/books/<book_name>/info/`) retornam uma resposta `404 Not Found` padronizada se o livro não for encontrado.
- [ ] **CA3:** A view `BookListView` (`/books/`) suporta os filtros (`testament`, `is_deuterocanonical`), busca (`search`) e ordenação (`ordering`) definidos.
- [ ] **CA4:** A documentação OpenAPI (Swagger) é gerada automaticamente e refleta com precisão todos os novos endpoints, incluindo sumários, parâmetros e respostas esperadas.
- [ ] **CA5:** Novos testes de integração são criados em `tests/api/books/` para cobrir o comportamento de cada novo endpoint (casos de sucesso e de erro).
- [ ] **CA6:** Endpoints que não foram completamente implementados (`outline`, `context`, `structure`, `statistics`) retornam `501 Not Implemented` com uma mensagem apropriada.
- [ ] **CA7:** A view `BooksByTestamentView` filtra corretamente os livros pelo ID do testamento.
- [ ] **CA8:** A view `BooksByAuthorView` filtra corretamente os livros pelo nome do autor (quando a funcionalidade for implementada).

## Escopo / Fora do Escopo
- **Inclui:**
    - Criação das classes de View para os 6 endpoints faltantes.
    - Criação dos Serializers necessários para formatar as respostas.
    - Configuração das rotas em `bible/books/urls.py`.
    - Testes de integração para os novos endpoints.
    - Atualização da documentação OpenAPI.
- **Não inclui:**
    - Implementação da lógica de negócio complexa para os endpoints `outline`, `context`, `structure` e `statistics` (inicialmente, eles retornarão `501 Not Implemented`).
    - Implementação de outros domínios da API (Themes, Geography, etc.).
    - Alterações nos modelos de dados existentes.

## Impacto Técnico
**Contrato (OpenAPI)**: Sim, haverá adição de novas rotas ao schema da API.
**DB/Migrations**: Não, esta tarefa utilizará os modelos (`CanonicalBook`, etc.) já existentes. Nenhuma migração de banco de dados é esperada.
**Throttle/Cache**: Utilizará os escopos de throttling padrão definidos no `settings.py`. Nenhuma estratégia de cache específica será implementada nesta tarefa.
**Performance**: As queries devem ser otimizadas para evitar problemas de N+1, utilizando `select_related` e `prefetch_related` quando aplicável.
**Segurança**: Os endpoints são de leitura (`read-only`). A permissão padrão `IsAuthenticatedOrReadOnly` será aplicada.

## Plano de Testes
**API**: Para cada endpoint, testar:
    - Resposta de sucesso com dados válidos (`200 OK`).
    - Resposta para recursos não encontrados (`404 Not Found`).
    - Comportamento dos filtros, busca e ordenação na view de listagem.
    - Resposta `501 Not Implemented` para endpoints não finalizados.
**Contrato**: Validar se o schema OpenAPI gerado corresponde à implementação.
**Dados**: Utilizar factories ou fixtures para popular o banco de dados de teste com dados consistentes para os livros.

## Observabilidade
- Nenhuma métrica, log ou alerta novo é necessário. Os logs de requisição padrão cobrirão os novos endpoints.

## Rollout & Rollback
- **Rollout**: A implementação será mesclada ao branch principal via Pull Request após a aprovação dos revisores e a passagem da CI.
- **Rollback**: Em caso de falha crítica em produção, reverter o Pull Request correspondente.

## Checklist Operacional (Autor)
- [ ] OpenAPI gerado/commitado em `docs/` (se houve mudança)
- [ ] `make fmt lint test` ok local
- [ ] CI verde (lint, migrations-check, tests, schema-diff)
- [ ] PR descreve impacto e rollback

## Checklist Operacional (Revisor)
- [ ] Contrato estável ou depreciação formal
- [ ] Testes suficientes (felizes + erros + auth + throttle + paginação/ordenação/filtros)
- [ ] Sem N+1; p95 dentro do orçamento
- [ ] Migrations pequenas e reversíveis
- [ ] Segurança: sem PII em logs; escopos e rate adequados
- [ ] Cache/invalidação documentados
