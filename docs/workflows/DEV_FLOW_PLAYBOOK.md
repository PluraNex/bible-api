# Playbook do Dev Flow — Bible API v1

Guia operacional para padronizar o fluxo de desenvolvimento **sem incluir código** neste momento.
Aplica-se ao repositório da *Bible API v1* e pode ser seguido por humanos e agentes de IA.

---

## 1) Política de Branches e Commits

### Branches
- **main**: protegido; só recebe merge via PR aprovado com CI verde.
- **curta duração**: `feat/<slug>`, `fix/<slug>`, `chore/<slug>`, `refactor/<slug>`, `docs/<slug>`, `test/<slug>`.

> **Branch develop**: Não utilizada. Todas as features vão diretamente para `main` via PR.

### Commits (Conventional Commits)
- Exemplos:
  - `feat(api): add versions listing`
  - `fix(auth): revoke key when expired`
  - `chore(ci): enable schema check`
  - `docs(readme): update quickstart`
- Use escopos como: `api`, `auth`, `audio`, `ai`, `resources`, `infra`, `docs`.
- Mensagens de commit devem descrever **o porquê** e **o que mudou** (linha adicional, quando necessário).

---

## 2) Definições de “Pronto” e “Feito”

### DoR — Definition of Ready
- [ ] Issue tem **objetivo claro**, contexto, **critérios de aceite** e fora de escopo.
- [ ] Impacto em **API/DB** identificado (compatibilidade, migrações, throttle).
- [ ] Riscos e dependências listados (feature flags, dados, third‑parties).

### DoD — Definition of Done
- [ ] **CI verde** (lint/format, migrations-check, tests, schema-diff).
- [ ] Testes **unitários** e **API** cobrindo caminho feliz e erros.
- [ ] **OpenAPI Schema MANDATORY**: Generate and commit `docs/openapi-v1.yaml` after ANY endpoint changes:
  ```bash
  python manage.py spectacular --file docs/openapi-v1.yaml
  git add docs/openapi-v1.yaml
  ```
- [ ] Logs/erros revisados (**sem PII**) e padronizados pelo handler.
- [ ] **Migrations** pequenas, idempotentes (1 mudança → 1 migration).
- [ ] PR documenta impacto, rollout/rollback e métricas a observar.

---

## 3) Ciclo Padrão de Tarefa

1. **Task Definition**: estruture em `tasks/YYYY-MM-DD--area--title.md` com:
   - Status: backlog → ready → in_progress → pr_draft → in_review → merged → done
   - 8 critérios de aceite claros e testáveis
   - Impacto em API/DB, riscos e dependências
   - Atualização do INDEX.md com status
2. **Issue Creation**: crie GitHub issue linkando a task e aplicando labels apropriadas
3. **Branch**: crie `feat/T-XXX-slug` referenciando task e issue
4. **Validação Arquitetural** (OBRIGATÓRIA antes da implementação):
   - **Consultar BIBLE_API_BASE_PROJECT.md** para verificar conformidade
   - **Verificar estrutura de modelos**: `bible/models/*.py`, nomes de tabela, relacionamentos
   - **Validar organização**: apps, URLs, estrutura de diretórios conforme arquitetura
   - **Identificar divergências**: listar inconsistências ou melhorias sugeridas
   - **Explicar justificativas**: documentar razões para mudanças ou adaptações
   - **Aguardar aprovação**: não prosseguir sem validação arquitetural ✅
5. **PR em rascunho (Draft)**: abra cedo para rodar CI e coletar feedback
6. **Desenvolvimento iterativo** (vertical slice):
   - Leitura simples → **View → Serializer → QuerySet/Selector**
   - Escrita/regras → **View → Serializer → Service → Manager/Selector**
   - **Nunca** coloque regra de negócio no Serializer
7. **Validação contínua**:
   - Execute `make fmt lint test` localmente
   - CI com jobs condicionais (adapta-se ao estado do projeto)
   - Verifique todos os 8 critérios de aceite
8. **Docs/Schema**: quando Django estiver ativo, gere/valide OpenAPI
9. **Revisão**: tire do Draft quando todos critérios atendidos
10. **Merge**: squash & merge com mensagem conventional commit
11. **Completion**: atualize task status para "done" e INDEX.md

---

## 4) CI no GitHub — Pipeline Inteligente

**Disparos**:
- Em `push` para `main`
- Em PRs para `main`

**Jobs adaptativos** (executam condicionalmente):
1) **lint-and-format** — `ruff` e `black` (executa apenas se existirem arquivos .py)
2) **migrations-check** — verifica migrações pendentes (apenas se manage.py existir)
3) **tests** — `pytest` com cobertura (apenas se diretório tests/ tiver arquivos)
4) **openapi-schema-check** — valida schema API (apenas se Django estiver configurado)

**Características especiais**:
- **Pipeline inteligente**: adapta-se ao estado atual do projeto
- **Falhas controladas**: jobs "skipam" graciosamente quando pré-requisitos não existem
- **Concurrency**: cancela execuções anteriores do mesmo branch
- **Cache de dependências**: Python pip cache para performance
- **Transição suave**: conforme projeto evolui, jobs se ativam automaticamente

---

## 5) Checklist de Revisão de PR

- [ ] PR nomeado e descrito com clareza; linka a issue.
- [ ] **Breaking change?** Política de compatibilidade aplicada (ver §7).
- [ ] Testes cobrem *happy path*, validações e permissões.
- [ ] Uso de **select_related/prefetch_related** em listas/serializações.
- [ ] **Sem PII** em logs; erros padronizados pelo handler com `request_id`.
- [ ] **Migrations**: mínimas, legíveis e com possibilidade de rollback.
- [ ] **OpenAPI** atualizado; exemplos coerentes com respostas reais.
- [ ] **Throttle scope** apropriado (`search`, `write`, `ai-run`, `audio`, etc.).
- [ ] **Cache** (quando houver): chave estável + estratégia de invalidação descrita.

---

## 6) Dicas Rápidas de Qualidade (Políticas do Projeto)

- **Serialização eficiente**: sempre `select_related/prefetch_related` onde couber.
- **Business logic**: em **services** (não em serializers/views).
- **Logs**: nada de PII; níveis ajustados; handler único para exceções.
- **Migrations**: atômicas, pequenas, compatíveis com deploy em duas etapas quando necessário.
- **Pre‑merge local**: `make fmt lint test` obrigatório.
- **Paginação/Ordenação**: use a paginação padrão; exponha `ordering` explicitamente.
- **Throttling**: defina `throttle_scope` por endpoint de acordo com custo/risco.
- **Cache**: documentar TTL e invalidação no PR.

---

## 7) Compatibilidade e Depreciação

- **API estável** em `/api/v1/`: mudanças breaking exigem:
  - Deprecar campo/rota → marcar no OpenAPI + changelog;
  - Oferecer alternativa;
  - Janela de depreciação (ex.: ≥ 30 dias) antes da remoção.
- **Banco de dados**: migrações **backward‑compatíveis** (estratégia em 2 passos quando necessário:
  adicionar colunas/índices, popular/backfill, depois trocar constraints/uso).

---

## 8) Segurança e Governança

- **Autenticação**: API Key — `Authorization: Api-Key <KEY>`.
- **Permissões**: aplique escopos para endpoints sensíveis.
- **Rate limiting**: confira escopo e limites em settings (por ex.: `write` mais restritivo).
- **Erros**: mensagens genéricas para o cliente; detalhes via `request_id`.
- **Dependências**: revisar alertas de segurança (GitHub Security) periodicamente.

---

## 9) Observabilidade e Performance

- **Health** e **Metrics** expostos e monitorados.
- **Orçamentos de performance**: documente p95 esperado em endpoints novos.
- **N+1**: evitar; índices adequados para filtros/joins comuns.
- **Auditoria**: operações críticas registradas (sem dados sensíveis).

---

## 10) Itens Iniciais para o Repositório (sem código neste momento)

- **Templates**:
  - **Issue Template** (contexto, critérios de aceite, impacto em API/DB, riscos, testes, rollout/rollback).
  - **PR Template** (o que/por quê, screenshots, migrações, schema, riscos).

- **Governança**:
  - `CODEOWNERS`, `CONTRIBUTING.md`, `SECURITY.md`, `LICENSE`.
  - Proteção de branch: exigir os 4 checks da CI; proibido push direto em `main`.

- **Padrões**:
  - `.editorconfig`, `.gitattributes`.
  - Labels no repositório: `area/api`, `area/auth`, `area/audio`, `area/ai`, `area/resources`, `type/feat`, `type/fix`, `breaking`, `needs-schema`, `needs-tests`.

---

## 11) Glossário Rápido

- **Selector**: consulta de leitura em Manager/QuerySet (otimizada e reutilizável).
- **Service**: regra de negócio para escrita/processos (anti‑corrupção da camada API).
- **Throttle scope**: rótulo para aplicar limites distintos por tipo de endpoint.
- **OpenAPI**: fonte de verdade da documentação; mudanças devem ser versionadas em `docs/`.

---

## 11.5) Validação Arquitetural - Fluxo Detalhado

### Processo Obrigatório de Validação
Antes de qualquer implementação, siga este checklist:

**📋 Checklist de Validação Arquitetural:**

1. **📖 Consulta da Arquitetura Base**:
   - Abrir `docs/architecture/BIBLE_API_BASE_PROJECT.md`
   - Identificar seção relevante (models, apps, URLs, etc.)
   - Verificar estrutura definida vs. implementação planejada

2. **🔍 Verificação de Modelos**:
   - Localização correta: `bible/models/*.py`
   - Nomes de tabela: sem prefixos desnecessários (`books` vs `bible_books`)
   - Relacionamentos e campos conforme especificação
   - Índices e constraints apropriados

3. **🏗️ Estrutura de Apps**:
   - Organização: `bible/apps/<domain>/`
   - URLs: padrão `/api/v1/<domain>/`
   - Views, serializers, services em locais corretos

4. **📝 Documentação de Divergências**:
   ```markdown
   ### Validação Arquitetural - T-XXX

   **✅ Conforme arquitetura:**
   - Modelos em bible/models/
   - Estrutura de URLs correta

   **❌ Divergências identificadas:**
   - Modelo Chapter não existe na spec (criado por necessidade)
   - Nome de tabela bible_books vs books

   **🔧 Correções aplicadas:**
   - Removido modelo Chapter
   - Corrigido nome de tabela para books

   **✋ Aguardando aprovação:** N/A
   ```

5. **⏳ Processo de Aprovação**:
   - Apresentar análise completa
   - Explicar justificativas para mudanças
   - **NÃO PROSSEGUIR** sem aprovação explícita
   - Aplicar correções solicitadas

### Exemplo Prático (T-001)
Durante T-001, identificamos:
- ❌ Criamos `CanonicalBook` (spec define `Book`)
- ❌ Modelo `Chapter` não especificado na arquitetura
- ❌ Nomes de tabela com prefixos desnecessários
- ✅ Correções aplicadas após validação

---

## 12) Lições Aprendidas (T-000)

**Fluxo de task bem-sucedido**:
- ✅ Task estruturada com 8 critérios claros
- ✅ CI inteligente que se adapta ao estado do projeto
- ✅ GitHub integration completo (issue → branch → PR)
- ✅ Conventional commits sem atribuição AI
- ✅ Validação contínua com múltiplas iterações

**Melhorias identificadas**:
- 📁 Reorganizar estrutura de documentação em diretórios lógicos
- 📋 Templates de issue/PR mais detalhados
- 🔧 Scripts de automação para criação de tasks
- 📊 Dashboard de acompanhamento de tasks mais visual

## 13) Próximos Passos
- Implementar reorganização de documentação (próxima ação)
- Criar templates formais de Issue/PR
- Desenvolver automações para workflow de tasks
- Socializar playbook atualizado com o time
