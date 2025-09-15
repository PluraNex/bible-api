---
id: T-T01
title: "[api] Implementar endpoints do domínio 'Themes'"
status: ready
created: 2025-09-09
updated: 2025-09-09
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/api", "type/feat"]
priority: high
effort: M
risk: low
depends_on: []
related: []
epic: "Fase 1: Implementação de Endpoints Base da API"
branch: "feat/api-themes-endpoints"
pr: ""
github_issue: ""
due: null
---

## Contexto
O blueprint da arquitetura (`BIBLE_API_BASE_PROJECT.md`) define um conjunto rico de endpoints para o domínio de Temas (Themes). Após a população completa da base de dados com 18 versões bíblicas, 73 livros e 562K+ versículos, esta tarefa visa implementar os endpoints avançados do domínio Themes, fornecendo funcionalidades de análise temática e pesquisa para os consumidores da API.

### **Endpoints Existentes:**
- ✅ `GET /api/v1/bible/themes/` - Listagem básica de temas (`ThemeListView`)
- ✅ `GET /api/v1/bible/themes/<int:pk>/detail/` - Detalhes de um tema (`ThemeDetailView`)

### **Endpoints a Implementar:**
- ❌ `GET /api/v1/bible/themes/search/` - Busca textual de temas por nome/descrição
- ❌ `GET /api/v1/bible/themes/<int:theme_id>/statistics/` - Métricas e estatísticas do tema
- ❌ `GET /api/v1/bible/themes/analysis/by-book/<str:book_name>/` - Análise temática por livro bíblico
- ❌ `GET /api/v1/bible/themes/<int:theme_id>/progression/` - Progressão cronológica do tema na Bíblia
- ❌ `GET /api/v1/bible/themes/concept-map/<str:concept>/` - Mapa de relacionamentos conceituais

### **Arquitetura dos Dados:**
- **Modelo Principal**: `Theme` (temas bíblicos centrais)
- **Relacionamentos**: `VerseTheme` (associações versículo-tema via FK)
- **Consultas**: Agregações complexas sobre 562K+ versículos distribuídos em 18 versões

## Objetivo e Critérios de Aceite
O objetivo é implementar os 5 endpoints avançados do domínio Themes, expandindo a funcionalidade básica existente com recursos de busca, análise estatística e mapeamento conceitual.

### **Critérios de Aceite Funcionais:**
- [ ] **CA1:** `ThemeSearchView` implementada com busca full-text por `name` e `description` usando filtros Django/PostgreSQL
- [ ] **CA2:** `ThemeStatisticsView` retorna métricas agregadas (contagem de versículos, livros, versões) para o tema específico
- [ ] **CA3:** `ThemeAnalysisByBookView` analisa distribuição temática por livro bíblico com aggregations otimizadas
- [ ] **CA4:** `ThemeProgressionView` mapeia evolução cronológica do tema através da ordem canônica dos livros
- [ ] **CA5:** `ConceptMapView` identifica temas relacionados baseado em co-ocorrência de versículos

### **Critérios de Aceite Técnicos:**
- [ ] **CA6:** Todos os endpoints retornam `404 Not Found` padronizado para recursos inexistentes
- [ ] **CA7:** Queries otimizadas com `select_related`/`prefetch_related` para evitar problemas N+1
- [ ] **CA8:** Documentação OpenAPI completa com exemplos de request/response para cada endpoint
- [ ] **CA9:** Cobertura de testes >= 90% com casos felizes, de erro e edge cases
- [ ] **CA10:** Performance: endpoints respondem em <500ms para datasets típicos (P95)

## Escopo / Fora do Escopo
- **Inclui:**
    - Criação das classes de View para os 7 endpoints.
    - Criação dos Serializers necessários para formatar as respostas.
    - Configuração das rotas em `bible/themes/urls.py`.
    - Testes de integração para os novos endpoints.
- **Não inclui:**
    - Implementação de outros domínios da API (Verses, Cross-references, etc.).

## Impacto Técnico
**Contrato (OpenAPI)**: Sim, haverá adição de novas rotas ao schema da API.
**DB/Migrations**: Esta tarefa utilizará os modelos (`Theme`, etc.) já existentes. Nenhuma migração de banco de dados é esperada.
**Throttle/Cache**: Utilizará os escopos de throttling padrão definidos no `settings.py`. Nenhuma estratégia de cache específica será implementada nesta tarefa.
**Performance**: As queries devem ser otimizadas para evitar problemas de N+1, utilizando `select_related` e `prefetch_related` quando aplicável.
**Segurança**: Os endpoints são de leitura (`read-only`). A permissão padrão `IsAuthenticatedOrReadOnly` será aplicada.

## Plano de Testes
**API**: Para cada endpoint, testar:
    - Resposta de sucesso com dados válidos (`200 OK`).
    - Resposta para recursos não encontrados (`404 Not Found`).
    - Comportamento da paginação e ordenação na view de listagem.
**Contrato**: Validar se o schema OpenAPI gerado corresponde à implementação.
**Dados**: Utilizar factories ou fixtures para popular o banco de dados de teste com dados consistentes para os temas.

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
