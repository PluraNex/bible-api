---
id: T-014
title: "[api] Error Model Standardization"
status: done
created: 2025-09-07
updated: 2025-09-08
owner: "@iuryeng"
reviewers: ["@IuryAlves"]
labels: ["area/api", "type/feature", "type/docs", "type/test"]
priority: high
effort: M
risk: low
depends_on: []
related: ["T-007", "T-012"]
epic: "Fundação da API"
branch: "feat/T-014-error-model"
pr: "PR#TBD"
github_issue: ""
due: null
---

## Contexto
Atualmente, a API retorna diferentes formatos de erro dependendo do tipo de exceção (DRF validation, 404, permission errors, etc.). Para uma experiência consistente do desenvolvedor e melhor debugging, precisamos padronizar todas as respostas de erro com um formato único que inclua request IDs para rastreabilidade.

## Objetivo e Critérios de Aceite
Implementar sistema de error handling padronizado que forneça respostas consistentes e rastreabilidade para todas as APIs.

- [x] **CA1:** Implementar formato padronizado de error response com `detail`, `code`, `errors`, `request_id`
- [x] **CA2:** Criar custom exception handler que intercepta todas as exceções da API
- [x] **CA3:** Implementar middleware para Request ID tracking em todas as requests
- [x] **CA4:** Definir códigos de erro padronizados (validation_error, not_found, permission_denied, authentication_failed, throttled, method_not_allowed, internal_server_error)
- [x] **CA5:** Integrar com sistema de logging para rastreabilidade sem exposição de dados sensíveis
- [x] **CA6:** Atualizar endpoints existentes para usar o novo formato (via handler global)
- [x] **CA7:** Criar testes para diferentes cenários de erro (unit e integração)
- [x] **CA8:** Documentar formato de erro na OpenAPI (aplicado ao domínio Versions; demais domínios serão cobertos na T-015)

## Formato de Error Response
```json
{
  "detail": "Invalid input",
  "code": "validation_error",
  "errors": { "field_name": ["This field is required"] },
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Códigos de Erro Padronizados
- `validation_error` - Erro de validação de dados (400)
- `not_found` - Recurso não encontrado (404)
- `permission_denied` - Permissão negada (403)
- `authentication_failed` - Autenticação necessária (401)
- `throttled` - Limite de taxa excedido (429)
- `method_not_allowed` - Método HTTP não permitido (405)
- `internal_server_error` - Erro interno do servidor (500)

## Escopo / Fora do Escopo
- **Inclui:** Sistema completo de error handling, middleware de Request ID, custom exceptions, logging integration
- **Não inclui:** Alerting/monitoring específico, métricas detalhadas de erro

## Impacto Técnico
**Contrato (OpenAPI)**: Todas as respostas de erro terão formato padronizado - breaking change controlado
**Logging**: Melhoria na rastreabilidade com Request IDs
**Performance**: Impacto mínimo - apenas overhead de geração de UUID
**Debugging**: Melhoria significativa na capacidade de debug

## Plano de Testes
**API**: Testes para cada tipo de erro (validation, 404, 403, etc.)
**Integration**: Verificar que Request ID é propagado corretamente
**Logging**: Validar que logs contêm Request ID sem dados sensíveis
**Existing endpoints**: Garantir que endpoints existentes funcionam com novo formato

## Observabilidade
- Request IDs em todas as respostas de erro
- Logs estruturados com contexto de erro
- Métricas de tipos de erro mais comuns

## Rollout & Rollback
- Deploy incremental: Exception handler primeiro, depois middleware
- Rollback: Remover custom exception handler de settings.py
- Compatibilidade: Clientes existentes continuam funcionando

## Checklist Operacional (Autor)
- [ ] Custom exception handler implementado e testado
- [ ] Middleware de Request ID funcionando
- [ ] Todos tipos de erro padronizados
- [ ] Testes cobrindo diferentes cenários
- [ ] OpenAPI documentation atualizada
- [ ] CI verde e lint passing

## Checklist Operacional (Revisor)
- [ ] Error responses consistentes em todos endpoints
- [ ] Request IDs presentes e únicos
- [ ] Logs não expõem dados sensíveis
- [ ] Performance não degradada
- [ ] Documentação clara do formato de erro
