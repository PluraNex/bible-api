---
id: T-001
title: "[api] Refatoração para Alinhamento Arquitetural"
status: backlog
created: 2025-09-07
updated: 2025-09-07
owner: "@gemini"
reviewers: ["@IuryAlves"]
labels: ["area/api", "type/refactor"]
priority: high
effort: L
risk: medium
depends_on: []
related: ["docs/architecture/BIBLE_API_BASE_PROJECT.md"]
epic: "Fundação da API"
branch: "refactor/architecture-alignment"
pr: ""
github_issue: ""
due: null
---

## Contexto
A implementação atual da API, embora funcional, diverge da arquitetura de referência documentada em `docs/architecture/BIBLE_API_BASE_PROJECT.md`. Para garantir a escalabilidade, manutenibilidade e consistência do projeto, é necessário refatorar a estrutura atual para alinhá-la com a visão arquitetural.

## Objetivo e Critérios de Aceite
O objetivo desta tarefa é reestruturar o projeto para seguir o padrão DDD-like proposto, com separação clara de domínios e camadas de serviço.

- [ ] **CA1:** Os domínios (`books`, `verses`, `themes`, etc.) devem ser refatorados para apps Django independentes dentro de `bible/apps/`.
- [ ] **CA2:** A lógica de negócio deve ser extraída das views e movida para uma camada de `services` e `selectors`.
- [ ] **CA3:** A estrutura de URLs deve ser expandida para incluir os endpoints detalhados na documentação de arquitetura.
- [ ] **CA4:** Os modelos devem ser atualizados e expandidos para refletir a estrutura proposta na documentação.
- [ ] **CA5:** As configurações do projeto (`settings.py`) devem ser atualizadas para incluir as configurações avançadas de cache, CORS e logging.

## Escopo / Fora do Escopo
- **Inclui:** Refatoração da estrutura de diretórios, criação de apps Django para cada domínio, implementação da camada de serviço, expansão das URLs e modelos.
- **Não inclui:** Implementação de todas as funcionalidades de negócio para todos os endpoints. O foco é na estrutura e no alinhamento arquitetural.

## Impacto Técnico
**Contrato (OpenAPI)**: Haverá mudanças significativas nas URLs e na estrutura dos dados de resposta.
**DB/Migrations**: Serão necessárias novas migrações para refletir as mudanças nos modelos.
**Throttle/Cache**: As políticas de throttle e cache serão implementadas conforme a documentação.
**Performance**: A introdução da camada de serviço pode ter um pequeno impacto na performance, que deve ser monitorado.
**Segurança**: As permissões e escopos de API serão revisados e aplicados de forma mais granular.

## Plano de Testes
**API**: Todos os endpoints existentes devem continuar funcionando após a refatoração. Novos testes devem ser criados para os novos endpoints.
**Contrato**: O schema OpenAPI deve ser atualizado para refletir as novas URLs e estruturas de dados.
**Dados**: As migrações de banco de dados devem ser testadas para garantir que não haja perda de dados.

## Observabilidade
- Métricas de performance devem ser monitoradas para identificar qualquer regressão.
- Logs devem ser configurados para fornecer visibilidade sobre a nova camada de serviço.

## Rollout & Rollback
- A refatoração será implementada em um branch separado.
- A reversão pode ser feita descartando o branch de refatoração.

## Checklist Operacional (Autor)
- [ ] OpenAPI gerado/commitado em `docs/`
- [ ] `make fmt lint test` ok local
- [ ] CI verde
- [ ] PR descreve impacto e rollback

## Checklist Operacional (Revisor)
- [ ] Contrato estável ou depreciação formal
- [ ] Testes suficientes
- [ ] Sem N+1; p95 dentro do orçamento
- [ ] Migrations pequenas e reversíveis
- [ ] Segurança: sem PII em logs; escopos e rate adequados
- [ ] Cache/invalidação documentados
