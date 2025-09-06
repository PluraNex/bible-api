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
- [ ] **Swagger/OpenAPI** atualizado e arquivo versionado em `docs/`.
- [ ] Logs/erros revisados (**sem PII**) e padronizados pelo handler.
- [ ] **Migrations** pequenas, idempotentes (1 mudança → 1 migration).
- [ ] PR documenta impacto, rollout/rollback e métricas a observar.

---

## 3) Ciclo Padrão de Tarefa

1. **Issue**: defina objetivo, user story, critérios de aceite, riscos e impacto (API/DB/cache/throttle).
2. **Branch**: crie `feat/...` (ou `fix/...`) referenciando a issue.
3. **PR em rascunho (Draft)**: abra cedo para rodar CI e coletar feedback.
4. **Desenvolvimento iterativo** (vertical slice):
   - Leitura simples → **View → Serializer → QuerySet/Selector**.
   - Escrita/regras → **View → Serializer → Service → Manager/Selector**.
   - **Nunca** coloque regra de negócio no Serializer.
5. **Qualidade local**: executar `make fmt lint test`.
6. **Docs/Schema**: gere/valide OpenAPI; se mudar, **commite** o `docs/openapi-v1.yaml` e atualize exemplos.
7. **Revisão**: tire do Draft quando cobertura e checklists ok; PR com contexto e riscos.
8. **Merge**: squash & merge (histórico limpo); tag se for release.
9. **Pós-merge**: monitore `health/` e `metrics/`, latência e erros.

---

## 4) CI no GitHub — Regras (sem YAML por enquanto)

**Disparos**:
- Em `push` para `main`.
- Em PRs para `main`.

**Jobs obrigatórios** (bloqueiam merge):
1) **lint-and-format** — `ruff` e `black` (modo *check only*).  
2) **migrations-check** — falha se existirem migrações pendentes.  
3) **tests** — `pytest` contra Postgres e Redis; cobertura publicada como artefato.  
4) **openapi-schema-check** — gerar `docs/openapi-v1.yaml` e falhar se houver diferença não commitada.

**Boas práticas de pipeline**:
- Cache de dependências Python.
- **Concurrency** por branch (cancela execuções anteriores do mesmo ref).
- Publicar artefatos de **cobertura** e do **schema**.
- Tornar os 4 jobs **status obrigatórios** nas proteções de branch.

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

## 12) Próximos Passos
- Formalizar os **templates** (Issue/PR) e proteção de branch.
- Configurar **workflow de CI** conforme §4 (em uma task separada).
- Socializar este playbook com o time e mantê‑lo atualizado.
