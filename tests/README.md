# Estrutura de Testes - Bible API v1

Guia para estrutura e organização de testes seguindo `docs/api/API_TESTING_BEST_PRACTICES.md`.

## 📁 Estrutura de Diretórios

```
tests/
├── conftest.py                     # Configuração global pytest + fixtures
├── templates/
│   └── test_endpoint_template.py   # Template para novos testes de API
├──
├── api/                            # Testes de API (integração)
│   ├── ai/
│   │   ├── test_ai_endpoints.py    # Agents, tools, runs, workflows
│   │   └── test_ai_routes.py       # Routing específico
│   ├── bible/
│   │   ├── auth/
│   │   │   └── test_permissions.py # Permissions API específicas
│   │   ├── books/
│   │   │   └── test_books_endpoints.py
│   │   ├── verses/
│   │   │   └── test_verses_endpoints.py
│   │   ├── versions/
│   │   │   └── test_versions_endpoints.py
│   │   ├── crossrefs/
│   │   │   └── test_crossrefs_endpoints.py
│   │   └── themes/
│   │       └── test_themes_endpoints.py
│   ├── common/
│   │   ├── test_error_handling.py  # Error handlers globais
│   │   └── test_middleware.py      # Middleware de API
│   └── health/
│       └── test_health_endpoints.py
│
├── auth/                           # Testes unitários de autenticação
│   ├── test_authentication.py      # ApiKeyAuthentication class
│   └── test_permissions.py         # Permission classes
│
├── models/                         # Testes unitários de modelos
│   ├── auth/
│   │   └── test_apikey_model.py
│   ├── books/
│   │   └── test_book_model.py
│   ├── verses/
│   │   └── test_verse_model.py
│   ├── crossrefs/
│   │   └── test_crossreference_model.py
│   └── themes/
│       └── test_theme_model.py
│
├── serializers/                    # Testes unitários de serializers
│   ├── test_verses_serializers.py
│   ├── test_versions_serializers.py
│   ├── test_themes_serializers.py
│   └── test_crossrefs_serializers.py
│
├── utils/                          # Testes unitários de utilitários
│   ├── test_bible_utils.py
│   └── test_utils_comprehensive.py
│
├── common/                         # Testes de componentes comuns
│   └── test_exceptions.py
│
├── integration/                    # Testes de integração completos
│   └── test_api_integration.py     # Workflows end-to-end
│
├── performance/                    # Testes de performance
│   └── test_api_performance.py     # N+1 queries, response times
│
└── views/                          # Testes unitários de views
    └── test_bible_overview.py
```

## 🎯 Marcadores pytest

### Por Tipo de Teste (§2)
- `@pytest.mark.unit` - Testes unitários (rápidos, isolados)
- `@pytest.mark.api` - Testes de API (integração)
- `@pytest.mark.integration` - Testes de integração completos
- `@pytest.mark.performance` - Testes de performance (§8)
- `@pytest.mark.slow` - Testes lentos (excluídos do PR)

### Por Área Funcional
- `@pytest.mark.auth` - Autenticação/autorização (§5)
- `@pytest.mark.cache` - Relacionados a cache (§9)
- `@pytest.mark.security` - Testes de segurança (§11)
- `@pytest.mark.throttle` - Rate limiting (§5)
- `@pytest.mark.contract` - Conformidade OpenAPI (§4)

### Por Domínio (§10)
- `@pytest.mark.books` - Books/verses
- `@pytest.mark.crossrefs` - Cross references
- `@pytest.mark.audio` - Audio/TTS
- `@pytest.mark.ai` - AI agents e tools
- `@pytest.mark.resources` - Recursos externos

## 🔧 Execução de Testes

### Comandos Básicos
```bash
# Todos os testes
pytest

# Apenas testes rápidos (PR)
pytest --quick

# Apenas testes de contrato
pytest --contract-only

# Por marcador
pytest -m "api and not slow"
pytest -m "unit"
pytest -m "performance"
```

### Scripts Disponíveis
```bash
# Via Python script
python scripts/run_tests.py --all
python scripts/run_tests.py --unit
python scripts/run_tests.py --integration
python scripts/run_tests.py --performance

# Via Makefile
make test          # Testes básicos
make coverage      # Com relatório de cobertura
make ci-test       # Suite CI completa
```

## 📋 Checklist para Novos Testes

### Antes de Criar Testes (DoR - §2)
- [ ] Endpoint/funcionalidade tem objetivo claro
- [ ] Impacto em API/DB identificado
- [ ] Critérios de aceite definidos

### Criando Testes de API (§3)
- [ ] Use o template `tests/templates/test_endpoint_template.py`
- [ ] Cubra todos os 8 critérios mínimos:
  - [ ] Status codes (200/201/204/400/401/403/404/405/409/422/429)
  - [ ] Shape do erro padronizado
  - [ ] Autenticação & Permissão
  - [ ] Validação de campos
  - [ ] Paginação/Ordenação/Busca
  - [ ] Headers relevantes
  - [ ] Contrato OpenAPI
  - [ ] Performance (sem N+1)

### Finalizando (DoD - §2)
- [ ] CI verde (lint/format, migrations, tests, schema)
- [ ] Testes unitários e de API
- [ ] Schema OpenAPI atualizado se necessário
- [ ] Logs/erros sem PII
- [ ] Cobertura mínima atingida (≥85%)

## ⚡ Fixtures Disponíveis

### Autenticação (§5)
- `api_key_read` - Chave apenas leitura
- `api_key_write` - Chave leitura + escrita
- `api_key_admin` - Chave admin completa
- `api_key_ai` - Chave para AI endpoints
- `authenticated_client` - Cliente com auth read
- `admin_client` - Cliente com auth admin

### Dados de Domínio (§14)
- `languages` - Idiomas padrão (en, pt, es)
- `testaments` - Testamentos (Old, New)
- `canonical_books` - Livros canônicos (Genesis, Exodus, John)
- `versions` - Versões da Bíblia (KJV, NVI)
- `minimal_bible_data` - Dataset mínimo para testes

### Performance e Configuração (§8-9)
- `performance_settings` - Settings otimizados
- `cache_settings` - Configuração de cache
- `throttle_settings` - Configuração de throttling

## 🚨 Regras Importantes

1. **Estrutura Organizacional (§2)**
   - API: `tests/api/<area>/<endpoint>_test_*.py`
   - Unitários: `tests/<module>/test_*.py`
   - Nomes descrevem comportamento, não implementação

2. **Dados de Teste (§14)**
   - Mínimos e relevantes por caso
   - Factories em vez de fixtures gigantes
   - Isolamento automático via transações

3. **Performance (§8)**
   - Orçamentos definidos (< 1s típico)
   - `assertNumQueries()` para N+1
   - Marcador `@pytest.mark.slow` para testes caros

4. **Segurança (§11)**
   - Sem PII em logs de erro
   - Proteção mass assignment testada
   - Validação de inputs maliciosos

5. **Contratos (§4)**
   - OpenAPI como fonte da verdade
   - Schema atualizado em mudanças
   - Estruturas de resposta validadas

## 📊 Cobertura Mínima

- **API endpoints**: ≥ 85%
- **Domínios críticos**: próximo a 100%
- **Exclusões documentadas**: migrations, settings, imports

## 🔍 Debugging

### Logs de Teste
```bash
# Verbose
pytest -v

# Com output
pytest -s

# Falhas apenas
pytest --tb=short
```

### Coverage
```bash
# Relatório HTML
pytest --cov=bible --cov-report=html
# Abre: htmlcov/index.html

# Relatório terminal
pytest --cov=bible --cov-report=term-missing
```

---

📚 **Referência**: `docs/api/API_TESTING_BEST_PRACTICES.md`
