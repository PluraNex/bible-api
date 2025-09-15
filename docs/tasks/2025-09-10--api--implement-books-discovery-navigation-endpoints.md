---
id: T-B02
title: "[api] Implementar endpoints avançados de descoberta e navegação para Books"
status: ready
created: 2025-09-10
updated: 2025-09-10
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/api", "type/feat"]
priority: high
effort: L
risk: low
depends_on: []
related: ["T-T01"]
epic: "Fase 2: Endpoints Avançados de Navegação e Descoberta"
branch: "feat/api-books-discovery-navigation"
pr: ""
github_issue: ""
due: null
---

## Contexto

Com a implementação bem-sucedida dos endpoints avançados de Themes (T-T01), o próximo passo natural é expandir as funcionalidades do domínio **Books** com recursos de descoberta, normalização e navegação. Atualmente, os endpoints de books são básicos (listagem e detalhes), mas os usuários da API precisam de funcionalidades mais ricas para:

1. **Descobrir livros** através de diferentes formas de busca e identificação
2. **Navegar pela estrutura** canônica e seções dos livros
3. **Normalizar identificadores** de diferentes tradições e idiomas
4. **Buscar conteúdo** dentro de contextos específicos

### **Endpoints Existentes:**
- ✅ `GET /api/v1/bible/books/` - Listagem básica de livros
- ✅ `GET /api/v1/bible/books/<int:pk>/detail/` - Detalhes de um livro

### **Endpoints a Implementar:**

#### **🔎 Descoberta / Normalização (Prioridade Alta):**
- ❌ `GET /api/v1/bible/books/search/` - Busca livros por nome, alias, OSIS
- ❌ `GET /api/v1/bible/books/aliases/` - Mapa de nomes alternativos por idioma
- ❌ `GET /api/v1/bible/books/resolve/<str:identifier>/` - Normaliza identificador para canônico
- ❌ `GET /api/v1/bible/books/canon/<str:tradition>/` - Lista livros por tradição canônica

#### **🧭 Navegação / Estrutura (Prioridade Média):**
- ❌ `GET /api/v1/bible/books/<str:book>/neighbors/` - Livro anterior e próximo no cânon
- ❌ `GET /api/v1/bible/books/<str:book>/sections/` - Perícopes/títulos de seções
- ❌ `GET /api/v1/bible/books/<str:book>/sections/<int:section_id>/` - Detalhe de seção
- ❌ `GET /api/v1/bible/books/<str:book>/search/` - Busca restrita ao livro
- ❌ `GET /api/v1/bible/books/<str:book>/chapters/<int:chapter>/verses/` - Versículos do capítulo
- ❌ `GET /api/v1/bible/books/<str:book>/range/` - Intervalo de versículos

### **Arquitetura dos Dados:**
- **Modelo Principal**: `CanonicalBook` (livros canônicos)
- **Relacionamentos**: `BookName` (nomes por idioma/versão), `Verse` (conteúdo)
- **Consultas**: Agregações sobre 73 livros e múltiplas versões/idiomas

## Objetivo e Critérios de Aceite

O objetivo é implementar 10 endpoints avançados para Books, priorizando descoberta/normalização e depois navegação/estrutura, criando uma experiência rica para consumidores da API.

### **Critérios de Aceite Funcionais (Descoberta/Normalização):**
- [ ] **CA1:** `BookSearchView` busca por nome, OSIS, aliases com suporte multilíngue
- [ ] **CA2:** `BookAliasesView` retorna mapa completo de nomes alternativos por idioma
- [ ] **CA3:** `BookResolveView` normaliza qualquer identificador (OSIS, slug, apelido) para formato canônico
- [ ] **CA4:** `BookCanonView` lista livros filtrados por tradição (protestant/catholic/orthodox/lxx)

### **Critérios de Aceite Funcionais (Navegação/Estrutura):**
- [ ] **CA5:** `BookNeighborsView` retorna livro anterior e próximo na ordem canônica
- [ ] **CA6:** `BookSectionsView` lista perícopes/seções estruturais do livro
- [ ] **CA7:** `BookSectionDetailView` detalha seção específica com range de versículos
- [ ] **CA8:** `BookRestrictedSearchView` busca conteúdo dentro do livro específico
- [ ] **CA9:** `BookChapterVersesView` lista versículos de um capítulo específico
- [ ] **CA10:** `BookRangeView` retorna intervalo contínuo (pode cruzar capítulos)

### **Critérios de Aceite Técnicos:**
- [ ] **CA11:** Todos os endpoints retornam `404 Not Found` padronizado para recursos inexistentes
- [ ] **CA12:** Queries otimizadas com `select_related`/`prefetch_related` para evitar N+1
- [ ] **CA13:** Suporte completo à internacionalização (múltiplos idiomas/nomes)
- [ ] **CA14:** Documentação OpenAPI completa com exemplos de request/response
- [ ] **CA15:** Cobertura de testes >= 90% com casos felizes, de erro e edge cases
- [ ] **CA16:** Performance: endpoints respondem em <300ms para datasets típicos (P95)

## Escopo / Fora do Escopo

### **Inclui:**
- Criação de 10 classes de View para os novos endpoints
- Serializers especializados para cada tipo de resposta
- Configuração das rotas em `bible/books/urls.py`
- Sistema de resolução de identificadores flexível
- Suporte a múltiplas tradições canônicas
- Testes de integração completos

### **Não inclui:**
- Implementação de endpoints de outros domínios (Verses, Themes, etc.)
- Criação de novas tabelas/migrations (usa modelos existentes)
- Sistema de cache específico (usa cache padrão do projeto)

## Impacto Técnico

**Contrato (OpenAPI)**: Sim, 10 novas rotas serão adicionadas ao schema da API.

**DB/Migrations**: Utilizará modelos existentes (`CanonicalBook`, `BookName`, `Verse`). Nenhuma migração esperada.

**Throttle/Cache**: Utilizará escopos de throttling padrão. Cache de longo prazo para dados canônicos.

**Performance**: Queries otimizadas com prefetch para relacionamentos multilíngues. Índices existentes suportam as consultas.

**Segurança**: Endpoints read-only. Permissão `IsAuthenticatedOrReadOnly` aplicada.

**Internacionalização**: Suporte completo a múltiplos idiomas através do modelo `BookName`.

## Plano de Testes

### **API**: Para cada endpoint, testar:
- Resposta de sucesso com dados válidos (`200 OK`)
- Resposta para recursos não encontrados (`404 Not Found`)
- Validação de parâmetros e filtros
- Comportamento com diferentes idiomas/tradições

### **Contrato**: Validar schema OpenAPI gerado corresponde à implementação.

### **Dados**: Utilizar factories para popular dados de teste com múltiplos idiomas e tradições.

### **Performance**: Verificar tempo de resposta e número de queries SQL.

## Observabilidade

- Logs de requisição padrão cobrirão os novos endpoints
- Métricas de performance para endpoints de busca e resolução
- Monitoramento de cache hit rate para dados canônicos

## Rollout & Rollback

- **Rollout**: Implementação via Pull Request após aprovação e CI verde
- **Rollback**: Reverter PR em caso de falha crítica
- **Feature Flag**: Considerar flag para endpoints de navegação (Fase 2)

## Implementação Faseada

### **Fase 1 - Descoberta/Normalização (Semana 1):**
1. `BookSearchView` - Busca flexível por livros
2. `BookAliasesView` - Mapa de aliases multilíngue
3. `BookResolveView` - Normalização de identificadores
4. `BookCanonView` - Filtragem por tradição canônica

### **Fase 2 - Navegação/Estrutura (Semana 2):**
5. `BookNeighborsView` - Navegação sequencial
6. `BookChapterVersesView` - Listagem de versículos por capítulo
7. `BookRangeView` - Intervalos contínuos de versículos
8. `BookRestrictedSearchView` - Busca dentro do livro
9. `BookSectionsView` - Lista de seções/perícopes
10. `BookSectionDetailView` - Detalhe de seção específica

## Checklist Operacional (Autor)

- [ ] Implementação Fase 1 completa e testada
- [ ] Implementação Fase 2 completa e testada
- [ ] OpenAPI gerado/commitado em `schema.yml`
- [ ] `make fmt lint test` ok local
- [ ] CI verde (lint, migrations-check, tests, schema-diff)
- [ ] PR descreve impacto, fases e rollback
- [ ] Cobertura de testes >= 90% verificada

## Checklist Operacional (Revisor)

- [ ] Contrato OpenAPI estável e bem documentado
- [ ] Testes suficientes (happy path + errors + auth + edge cases)
- [ ] Performance dentro do orçamento (<300ms P95)
- [ ] Suporte multilíngue funcionando corretamente
- [ ] Resolução de identificadores robusta
- [ ] Queries otimizadas (sem N+1)
- [ ] Segurança: escopos e rate adequados
