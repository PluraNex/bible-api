# Boas Práticas de Testes de API — Bible API v1

Guia prático para o **agente de IA** e para o **time** escreverem e revisarem testes de API de forma consistente **sem incluir código** neste momento.

---

## 1) Filosofia e Escopo
- **Piramide de testes**: unitários (rápidos) > API/integrados > end-to-end. Otimize o retorno por tempo de execução.
- **Contrato primeiro**: a fonte da verdade é o **OpenAPI**. Mudou contrato? Atualize o schema e os exemplos.
- **Testes determinísticos**: evite dependências externas e valores aleatórios sem controle (congele tempo/locale).

---

## 2) Organização e Nomenclatura
- Estrutura recomendada (alto nível): `tests/api/<area>/<endpoint>_test_*.py`.
- Nomeie arquivos e casos de teste pelo **comportamento esperado**, ex.: `test_list_versions_paginates_and_sorts`.
- Marque testes: `unit`, `api`, `integration`, `slow`. Separe execução rápida (PR) da completa (nightly).

---

## 3) Critérios Mínimos por Endpoint (Checklist)
Para cada rota, cubra no mínimo:

1. **Status codes** esperados (200/201/204/400/401/403/404/405/409/422/429 conforme aplicável).
2. **Shape do erro** padronizado (payload do handler com `detail`, `code`, `errors`, `request_id`).
3. **Autenticação & Permissão**:
   - Sem credenciais → 401 com `WWW-Authenticate` apropriado.
   - Sem escopo → 403.
   - Com escopo → passa.
4. **Validação**: campos obrigatórios, formatos, ranges e mensagens úteis (sem PII).
5. **Paginação/Ordenação/Busca**:
   - `page`, `page_size` (incluindo limites e defaults).
   - `ordering` (asc/desc; campos válidos/invalidos).
   - `filters` (existem? testá-los com casos positivos/negativos).
6. **Headers** relevantes: `Content-Type`, `ETag` / `Last-Modified` (se usado), `Cache-Control`, `Retry-After` (throttling).
7. **Contrato**: resposta adere ao **OpenAPI** e mantém compatibilidade com clientes.
8. **Performance** (orçamento local): sem N+1; número de queries previsível; tempo de resposta dentro de um alvo definido.

---

## 4) Testes de Contrato (OpenAPI)
- Gere o **schema** e verifique divergências. O PR **falha** se o schema gerado diferir do commitado em `docs/openapi-v1.yaml`.
- Valide exemplos do schema com respostas reais (amostras mínimas por rota).
- Marque campos **deprecated** e valide presença/ausência conforme fase do ciclo de vida.

---

## 5) Autenticação, Permissões e Throttling
- **API Key** obrigatória nos endpoints protegidos.
- Verifique:
  - Sem header → 401 (mensagem genérica).
  - Key inválida/expirada → 401.
  - Falta de escopo → 403.
- **Throttling** por `throttle_scope`:
  - Atingir o limite → 429 e `Retry-After` coerente.
  - Endpoints caros (ex.: AI, áudio) devem ter limites mais estritos.
- **Logs** da camada de erros **não** devem conter dados sensíveis (valide mensagem enxuta).

---

## 6) Paginação, Ordenação e Filtros (em detalhe)
- **Paginação**: defaults, `max_page_size`, páginas fora do range (última página vazia vs erro).
- **Ordenação**: múltiplos campos, prefixo `-`, campos inválidos (erro claro).
- **Filtros**: combinação de filtros (E/OU), normalização (trim/case), e resultados estáveis.
- **Estabilidade**: listagens devem ser ordenadas de forma determinística para garantir repetibilidade.

---

## 7) Erros, Internacionalização e Conteúdo
- **Handler**: payload consistente (chaves, tipos, códigos), `request_id` presente.
- **Mensagens**: genéricas para segurança; nada de stack trace em produção.
- **I18N/Locale** (se aplicável): verifique comportamento com `Accept-Language` e campos sensíveis a locale.

---

## 8) Performance e N+1
- **Orçamentos** por endpoint (ex.: p95 local < 200ms com dataset de teste).
- Verifique **N+1** usando contagem de queries nas rotas mais acessadas.
- Use relacionamentos otimizados nos seletores; resultados idênticos com custo previsível.

---

## 9) Caching e Condicionais HTTP
- **Cache-Control**: defina políticas para conteúdo semimútuo (ex.: dados bíblicos).
- **ETag/If-None-Match** / **Last-Modified/If-Modified-Since** onde couber, com testes de 304 Not Modified.
- **Invalidação**: garantir que writes invalidam caches pertinentes (documentar no PR e cobrir com teste).

---

## 10) Casos Específicos do Projeto
### 10.1 Books/Verses
- Referências inválidas (livro, capítulo, verso) → erro claro.
- Ordenação canônica e aliases de nomes funcionam.
- Paginadores coerentes para capítulos longos (ex.: Salmos).

### 10.2 Cross References
- Unicidade por (from, to, source) e faixas válidas (`start <= end`).
- Ordenação e prioridade por `confidence`/`source`.
- Inserções duplicadas → 409/422 conforme política.

### 10.3 Audio (TTS)
- **Cache-first**: já existe → 302 para CDN.
- **Job em progresso** → 202 com `job_id` e polling.
- **Inexistente** com on-demand habilitado → cria job vs retorna 404 quando desabilitado.
- **Status de job**: transições válidas; tentativas/erros registradas.
- **Headers** de áudio consistentes (`Content-Type`, TTL).

### 10.4 Resources (provedores externos)
- Erros de rede mapeados para códigos 502/504 conforme política.
- Timeouts tratados; **sem SSRF** (valide URLs contra whitelist de domínios permitidos).
- Sincronização idempotente; o mesmo recurso não duplica chaves externas.

### 10.5 AI (Agentes & Tools)
- Execução respeita `requires_approval`.
- Estados do run: `running` → `needs_approval` → `succeeded/failed`.
- Throttling diferenciado (`ai-run`, `ai-tools`); sem vazamento de `plan`/PII.

---

## 11) Segurança
- **Mass assignment**: endpoints de escrita aceitam somente campos permitidos.
- **Injeções**: entradas que poderiam quebrar filtros/queries devem ser sanitizadas.
- **Exposição de PII**: respostas e logs não retornam dados sensíveis.
- **Uploads**: valide Content-Type e tamanho máximo; rejeite paths com `../` ou caracteres perigosos.
- **Headers**: `X-Content-Type-Options`, `X-Frame-Options` conforme política do projeto (ver settings).

---

## 12) Banco de Dados e Migrações
- Testes devem cobrir **constraints** de DB (uniqueness, checks) além da validação na API.
- Migrações **pequenas e reversíveis**; teste rollback quando houver mudança crítica.
- Estratégia de migração em duas fases para alterações breaking de schema.

---

## 13) Observabilidade
- **Health**: API sobe e reporta estado e versão.
- **Metrics**: exposições básicas ativas; erros e latência observáveis.
- **Request ID**: propagado do request para logs e payloads de erro.

---

## 14) Dados de Teste
- Construa dados **mínimos e relevantes** por caso.
- Prefira **fábricas** (ex.: receitas predefinidas) em vez de fixtures gigantes e acopladas.
- Cada teste deve **isolar** seus próprios dados; limpeza automática via transações de teste.

---

## 15) Política de Cobertura e Qualidade
- **Cobertura alvo**: ≥ 85% no módulo de API; **domínios críticos** próximos de 100%.
- **Linhas inatingíveis** (migrations, settings) podem ser excluídas do relatório—documente.
- API nova sem testes **não** é mergeável; PR deve citar endpoints e casos cobertos.

---

## 16) Checklists Operacionais (Pré-PR)

**Autor**
- [ ] Casos positivos e negativos cobrindo a issue.
- [ ] Auth/permissions/throttling validados.
- [ ] Paginação/ordenção/filters testados.
- [ ] Erro handler e mensagens revisados (sem PII).
- [ ] OpenAPI atualizado e commitado em `docs/` (se houve mudança).
- [ ] Sem N+1 em rotas listadas.
- [ ] Cobertura mínima atingida; testes determinísticos.

**Revisor**
- [ ] Contrato estável; breaking changes deprecadas corretamente.
- [ ] Dados de teste enxutos; fábricas coerentes.
- [ ] Constraints de DB realmente exercitadas.
- [ ] Caching e invalidação documentados e cobertos.
- [ ] Throttle scopes apropriados e testados.
- [ ] Tempo de execução dos testes razoável (sem flakiness).

---

## 17) Execução em CI (Sem YAML por ora)
- Rodar **lint-and-format**, **migrations-check**, **tests** (com Postgres/Redis) e **openapi-schema-check**.
- Publicar **cobertura** e **schema** como artefatos.
- Aplicar **concurrency** por branch e tornar os 4 jobs obrigatórios para merge.

---

## 18) Próximos Passos
- Formalizar **templates de casos de teste** por tipo de endpoint (List/Detail/Create/Update/Delete).
- Habilitar **relatórios de falha** amigáveis (prints de payloads reduzidos).
- Criar **orçamentos de queries** por rota crítica e validar no PR.
