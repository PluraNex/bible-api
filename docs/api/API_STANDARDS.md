## Bible API — Padrões Oficiais

Este guia consolida padrões obrigatórios para versionamento, autenticação, autorização, i18n, erros, paginação, cache e observabilidade. Aplica-se a novos endpoints e revisões.

### 1. Versionamento e URLs
- Base: `/api/v1/` (versão maior imutável; mudanças breaking exigem v2)
- Recursos no plural e sub-recursos por contexto: `/bible/books/`, `/bible/verses/`, `/bible/versions/`
- Health e docs: `/health/`, `/health/liveness/`, `/health/readiness/`, `/api/v1/docs/`, `/api/v1/schema/`
- Métricas: `/metrics/prometheus/` (formato Prometheus). Mantemos `/metrics/` JSON para compatibilidade.

### 2. Autenticação e Autorização
- Autenticação: cabeçalho `Authorization: Api-Key <key>`
- OpenAPI: `ApiKeyAuth` (drf-spectacular) e `Authorize` habilitado
- Permissão padrão: `IsAuthenticated` (config), com endpoints públicos explicitamente `AllowAny`
- Escopos (via `HasAPIScopes`): `read`, `write`, `admin`, `ai-run`, `ai-tools`, `audio`

### 3. Throttling e Rate Limit
- **Atual**: `UserRateThrottle` e `AnonRateThrottle` básicos
- **Futuro (T-T01)**: `ScopedRateThrottle` com `throttle_scope` por endpoint (ex.: `read`, `search`, `ai-run`)
- **Configuração futura**:
  ```python
  DEFAULT_THROTTLE_CLASSES = [
      'rest_framework.throttling.ScopedRateThrottle',
      'rest_framework.throttling.UserRateThrottle',
      'rest_framework.throttling.AnonRateThrottle',
  ]
  DEFAULT_THROTTLE_RATES = {
      'read': '1000/hour',
      'search': '200/hour',
      'user': '5000/day',
      'anon': '1000/day',
  }
  ```
- **Reintroduzir**: `throttle_scope` em Books/Verses após T-T01
- Futuro: throttle dinâmico por `APIKey.rate_limit` (T-T02)

### 4. Modelo de Erros (consistente)
- Handler: `common.exceptions.custom_exception_handler`
- Payload: `{ detail, code, request_id, errors? }`
- Cabeçalhos: `WWW-Authenticate` para 401; `Retry-After` para 429 (quando aplicável)
- Sempre incluir `X-Request-ID` (middleware de `RequestID`)

### 5. Paginação, Filtros e Ordenação
- Paginação padrão: `common.pagination.StandardResultsSetPagination` (page, page_size, next, previous)
- Filtros: parâmetros simples; para combinados, preferir filtros nomeados coesos
- Ordenação: `ordering` com whitelist de campos; documentar exemplos

### 6. Internacionalização (i18n)
- Parâmetro preferencial: `lang` (query), com suporte a `Accept-Language` (fallback)
- Precedência: `lang` > `Accept-Language` > `en` (fallback progressivo: `pt-BR`→`pt`→`en`)
- Texto bíblico: controlado por `version`/tradução; `lang` apenas para metadados (ex.: nomes de livros, autores, descrições)
- Headers de cache: adicionar `Vary: Accept-Language` nas respostas sensíveis a idioma
- Documentação: adicionar `OpenApiParameter(name="lang")` e exemplos em `pt` e `en`
- **Dados de metadados**: `BookName` com `version IS NULL` deve usar códigos ISO base (`pt`, `en`, `es`); códigos regionais (`pt-BR`, `en-US`) apenas em `Version.language` quando necessário

#### Comandos de Auditoria i18n
- `python manage.py audit_i18n --report-only`: Auditoria read-only sem alterações
- `python manage.py audit_i18n --report-file=audit.json`: Exporta relatório JSON detalhado
- `python manage.py audit_i18n --fail-on-missing`: Exit code ≠ 0 se houver lacunas (CI gate)
- `python manage.py audit_i18n --languages=pt,en`: Auditar idiomas específicos
- `python manage.py audit_i18n --exclude-deuterocanon`: Filtrar livros deuterocanônicos
- `python manage.py audit_i18n --min-coverage=80`: Requer cobertura mínima (0-100%)

### 7. Cache e Respostas Condicionais
- ETags/Last-Modified em endpoints estáveis (T-P01)
- `Vary: Accept-Language` quando aplicável
- Redis como backend padrão; definir `KEY_PREFIX` por ambiente

### 8. Observabilidade
- Logs com formatter incluindo `{request_id}` (T-OB01)
- `/metrics/prometheus/` expõe métricas Prometheus via `django-prometheus` (requests, latência, DB, memória)
- Evitar PII/segredos nos logs
- Health checks:
  - `GET /health/` simple OK
  - `GET /health/liveness/` (process alive)
  - `GET /health/readiness/` (DB e cache OK → 200; caso contrário 503, payload com `checks`)

#### Exemplos (Kubernetes Probes)
```
livenessProbe:
  httpGet:
    path: /health/liveness/
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 15
readinessProbe:
  httpGet:
    path: /health/readiness/
    port: 8000
  initialDelaySeconds: 15
  periodSeconds: 15
```

### 9. Documentação (OpenAPI)
- Usar `drf-spectacular` com tags, parâmetros e exemplos
- Expor segurança `ApiKeyAuth` e escopos
- Snippets em curl/JS/Python

### 10. Testes
- Smoke: `/health/`, principais recursos com e sem auth
- Contrato: validar schema OpenAPI e erros padronizados
- i18n: `lang`, `Accept-Language`, fallback
- Performance: evitar N+1 (usar `select_related`/`prefetch_related`)

### 11. Depreciação e Mudanças Breaking
- Rotular endpoints/campos deprecados em docs por no mínimo um ciclo de release
- Não introduzir breaking em `v1`; lançar `v2` quando necessário

### 12. Convenções de Dados
- Identidade canônica: `CanonicalBook` e (futuro) `CanonicalVerse` + `VerseMap` para versificações
- Metadados localizados: tabelas específicas (ex.: `BookName`, `AuthorName`, `AuthorText`, `CommentarySourceText`, `CommentaryEntryText`)

### Referências no Código
- Settings: `config/settings.py` (REST, SPECTACULAR, CORS, LOGGING)
- Erros: `common/exceptions.py`
- Paginação: `common/pagination.py`
- Middleware Request ID: `common/middleware.py`
- Auth/Scopes: `bible/auth/*`

### Exemplos (curl)
```
# Listar livros em PT
curl -H "Authorization: Api-Key <KEY>" \
  "/api/v1/bible/books/?lang=pt"

# Versões padrão para um idioma
curl -H "Authorization: Api-Key <KEY>" \
  "/api/v1/bible/versions/default/?lang=pt"

# Versículos por capítulo, nome do livro em PT, texto da versão KJV
curl -H "Authorization: Api-Key <KEY>" \
  "/api/v1/bible/verses/John/1/?version=<KJV_ID>&lang=pt"
```
