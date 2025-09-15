---
id: T-B02
title: "[api] Implementar endpoints pendentes do domínio 'Books' — com i18n (lang/Accept-Language)"
status: completed
created: 2025-09-09
updated: 2025-09-11
owner: "@gemini-agent"
reviewers: ["@revisor-principal"]
labels: ["area/api", "type/feat"]
priority: high
effort: M
risk: low
depends_on: ["T-B01", "T-I18N01", "T-I18N02"]
related: []
epic: "Fase 1: Implementação de Endpoints Base da API"
branch: "feat/api-books-pending-endpoints"
pr: ""
github_issue: ""
due: null
---

## Contexto
Na tarefa T-B01, implementamos os endpoints principais do domínio "Books", mas deixamos 4 endpoints retornando o status 501 NotImplemented conforme previsto. Agora vamos implementar esses endpoints pendentes para fornecer a funcionalidade completa para o domínio "Books".

Os endpoints que precisam ser implementados são (já considerando suporte a i18n via `lang` e `Accept-Language`):
- `GET /api/v1/bible/books/{book_name}/outline/` - Outline do livro
- `GET /api/v1/bible/books/{book_name}/context/` - Contexto do livro
- `GET /api/v1/bible/books/{book_name}/structure/` - Estrutura do livro
- `GET /api/v1/bible/books/{book_name}/statistics/` - Estatísticas do livro

## Objetivo e Critérios de Aceite
O objetivo é implementar as views, serializers e atualizar as rotas necessárias para os endpoints pendentes do domínio 'Books'.

- [ ] **CA1:** Todos os 4 endpoints pendentes estão implementados e retornam `200 OK` para requisições válidas.
- [ ] **CA2:** Endpoints que dependem de um recurso específico retornam uma resposta `404 Not Found` padronizada se o livro não for encontrado.
- [ ] **CA3:** A documentação OpenAPI reflete com precisão todos os endpoints atualizados, incluindo `OpenApiParameter(name="lang")` e comportamento de fallback com `Accept-Language`.
- [ ] **CA4:** Novos testes de integração são criados em `tests/api/books/` para cobrir o comportamento de cada endpoint implementado (casos de sucesso e de erro).
- [ ] **CA5:** As respostas dos endpoints seguem o formato especificado no blueprint da arquitetura.
- [ ] **CA6 (i18n):** Os endpoints aceitam `lang` (query) e respeitam `Accept-Language`; nomes/abreviações de livros são exibidos no idioma solicitado com fallback para `en`.
- [ ] **CA7 (i18n):** Remover hardcodes de `"en"` nas views/serializers e passar `context={'request': request}` aos serializers; utilizar `request.lang_code` (resolvido por util/middleware).
- [ ] **CA8 (Perf/i18n):** Respostas que variam por idioma definem header `Vary: Accept-Language`.

## Escopo / Fora do Escopo
- **Inclui:**
    - Implementação das views para os 4 endpoints pendentes.
    - Criação/atualização dos Serializers necessários para formatar as respostas.
    - Atualização das rotas em `bible/books/urls.py` se necessário.
    - Testes de integração para os endpoints implementados.
- **Não inclui:**
    - Alterações nos modelos de dados existentes.
    - Implementação de outros domínios da API.

## Impacto Técnico
**Contrato (OpenAPI)**: Sim, haverá atualização das rotas existentes no schema da API.
**DB/Migrations**: Não, esta tarefa utilizará os modelos (`CanonicalBook`, etc.) já existentes. Nenhuma migração de banco de dados é esperada.
**Throttle/Cache**: Utilizará os escopos de throttling padrão definidos no `settings.py` (escopo de leitura). Incluir `Vary: Accept-Language` nas respostas sensíveis a idioma. Estratégias ampliadas de cache/ETag serão tratadas na task T-P01/T-I18N07.
**Performance**: As queries devem ser otimizadas para evitar problemas de N+1, utilizando `select_related` e `prefetch_related` quando aplicável.
**Segurança**: Endpoints de leitura. Aplicar permissão padrão do projeto (autenticação por Api-Key) e, se aplicável, `throttle_scope="read"`.

## Plano de Testes
**API**: Para cada endpoint, testar:
    - Resposta de sucesso com dados válidos (`200 OK`).
    - Resposta para recursos não encontrados (`404 Not Found`).
    - Estrutura da resposta conforme especificado no blueprint.
    - i18n: `lang=pt` retorna nomes em PT; `lang` inválido faz fallback para `en`; sem `lang`, `Accept-Language: pt` é respeitado.
**Contrato**: Validar se o schema OpenAPI gerado corresponde à implementação.
**Dados**: Utilizar factories ou fixtures para popular o banco de dados de teste com dados consistentes para os livros.

## Observabilidade
- Adicionar `Vary: Accept-Language` nas respostas sensíveis a idioma.

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
