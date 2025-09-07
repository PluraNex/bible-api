# BIBLE API — ORCHESTRATOR (Projeto Base)

> **Propósito**: este documento orquestra o **fluxo de trabalho**, a **governança** e a **execução** por Tasks.
> **Regra de ouro**: **sempre** comece qualquer entrega escrevendo uma **TASK** (issue) com critérios de aceite, plano de testes e impacto em contrato (OpenAPI) — antes de tocar em código.

---

## 0) Fonte de Verdade (SSOT) dos Docs
- **Visão & Norte**: [`../architecture/BIBLE_API_BASE_PROJECT.md`](../architecture/BIBLE_API_BASE_PROJECT.md) (ponto de chegada, KPIs, pilares).
  _Se não existir, crie a partir deste orquestrador (ver Template no §7)._
- **Fluxo de Dev**: [`DEV_FLOW_PLAYBOOK.md`](DEV_FLOW_PLAYBOOK.md) — políticas de branch, DoR/DoD, CI, revisão.
- **Testes de API**: [`API_TESTING_BEST_PRACTICES.md`](../api/API_TESTING_BEST_PRACTICES.md) — critérios mínimos, contrato, perf, segurança.
> ***Este** arquivo é o hub. Ele referencia e alinha os demais; qualquer mudança de processo nasce aqui.*

---

## 1) Modelo Mental de Entrega
1. **Planeje via Task** → descreva objetivo, valor, critérios, riscos.
2. **Projete contrato** → verifique/atualize OpenAPI (impacto & compatibilidade).
3. **Implemente em fatias verticais** → View → Serializer → Service/Selector.
4. **Teste primeiro** → unit + API (Contrato + erros + limites).
5. **CI & Revisão** → checks verdes e PR claro.
6. **Observabilidade** → health/metrics e orçamentos de queries/latência.
7. **Release** → changelog, migração e plano de rollback.

---

## 2) Governança (resumo prático)
- **Branches**: `main` (protegido), curtas `feat/`, `fix/`, `chore/`, `refactor/`.
- **Commits**: Conventional Commits com escopo (`api`, `auth`, `audio`, `ai`, `resources`, `infra`, `docs`).
- **CI (Jobs obrigatórios)**: lint-and-format → migrations-check → tests → openapi-schema-check.
- **Qualidade**: ver checklists no §5 e nos docs vinculados.
- **Compatibilidade**: `/api/v1` é **estável**; breaking exige depreciação e janela (ver Playbook §7).

---

## 3) Papéis e Responsabilidades
- **Dev**: escreve a Task, implementa a fatia vertical, mantém contrato e testes.
- **Revisor**: garante qualidade/segurança/contrato; orienta reversibilidade.
- **Maintainer**: configura guard-rails (branch protection, CI required).
- **Agente de IA**: automatiza tarefas **operacionais** (criar arquivos de CI, templates, esqueleto de testes, rotinas de schema), **sempre** obedecendo às políticas aqui definidas e **nunca** gerando código além do escopo da Task aprovada.

---

## 4) Workflow de Task (do intake ao merge)
1. **Criar Task Local** usando template em `tasks/TASK_TEMPLATE.md`.
2. **Criar Issue GitHub** seguindo `docs/GITHUB_INTEGRATION.md`.
3. **Sincronizar referências** entre task local e issue GitHub.
4. **Refinar** (DoR): confirmar critérios, impacto em API/DB, riscos, throttle/cache.
5. **Criar branch**: `feat/<slug>` (ou `fix/...`).
6. **PR Draft**: abrir cedo para CI, conectar com "Closes #issue".
7. **Desenvolver** pequeno e iterativo (cada commit fecha um subcritério).
8. **Validar** local: `fmt`, `lint`, `test`, contrato (schema).
9. **Atualizar docs**: exemplos no Swagger & `docs/openapi-v1.yaml`.
10. **Revisão**: aplicar checklists do §5.
11. **Merge**: squash, changelog, tag se for release.
12. **Pós-merge**: observar métricas/erros por 24h; criar follow-ups para falhas ou degradação de performance.

---

## 5) Quality Gates (antes do merge)
- **Contrato**: OpenAPI gerado, versionado e sem quebras não deprecadas.
- **Testes**: unit + API cobrindo caminho feliz e erros (401/403/404/422/429).
- **Desempenho**: sem N+1; queries e p95 dentro do orçamento da rota.
- **Segurança**: sem PII em logs; handlers padronizados; escopos/throttle corretos.
- **Migrations**: pequenas, reversíveis, uma mudança → uma migration.
- **Documentação**: PR descreve impacto, rollout/rollback, métricas a observar.
- **CI**: 4 jobs verdes; schema artifact atualizado.

> Detalhes finos estão em: **Playbook** §5/6/7 e **Boas Práticas de Testes** §§3–11.

---

## 6) Roadmap Tático (exemplo inicial)
> Ajuste conforme `BIBLE_API_BASE_PROJECT.md` (visão e prioridades).

- **Fase 0 — Boot**: Health/Metrics, Swagger agregado, API Keys mínimas, handler de erros.
- **Fase 0 — Boot**: Health/Metrics, Swagger agregado, API Keys mínimas, handler de erros.
- **Fase 1 — Read-only**: Books/Verses (lista/detalhe/paginação/ordenação), filtros básicos.
- **Fase 2 — Conteúdo externo**: Resources list + filtros; timeouts e mapeamento de erros.
- **Fase 3 — Áudio (TTS)**: cache-first, criação de Job on-demand, status/polling.

Cada fase é um **épico**; decomponha em **Tasks** “vertical slice”.

---

## 7) TEMPLATE — TASK (Issue)
> **Use o template oficial**: `tasks/TASK_TEMPLATE.md`
>
> Para criar uma task:
> 1. Copie `tasks/TASK_TEMPLATE.md` para `tasks/YYYY-MM-DD--area--slug.md`
> 2. Preencha front-matter e seções conforme template
> 3. Adicione entrada no `tasks/INDEX.md`

---

## 8) TEMPLATE — PR (Resumo)
- **O quê** (mudanças) e **por quê** (objetivo/valor).
- **Contrato**: mudanças no OpenAPI + exemplos.
- **Migrations**: riscos, tempo estimado, reversão.
- **Performance**: orçamento, queries, N+1 (se aplicável).
- **Testes**: lista dos casos incluídos.
- **Rollout/rollback**: plano e sinais de sucesso/falha.
- **Screenshots / evidências** (quando útil).

---

## 9) Board de Execução (Kanban sugerido)
- **Backlog** → **Ready** → **In Progress** → **PR (Draft)** → **Review** → **Merged** → **Done (Released)**
- **WIP**: no máximo 3 itens por pessoa/Agente.
- Itens **sem DoR** **não** entram em “Ready”.

---

## 10) Taxonomia de Labels
- `area/api`, `area/auth`, `area/audio`, `area/ai`, `area/resources`, `area/infra`, `area/docs`
- `type/feat`, `type/fix`, `type/chore`, `type/refactor`, `type/docs`, `type/test`
- `needs-schema`, `breaking`, `security`, `performance`, `observability`

---

## 11) Políticas de Versão & Depreciação (API)
- `/api/v1` é estável. Quebras exigem **depreciação** documentada e janela (≥ 30 dias).
- Campos/rotas **deprecated** devem ser marcados no schema e no changelog.
- Releases: usar tags semânticas para **backend** (`v1.x.y`) quando relevante.

---

## 12) Segurança & Dados
- **Auth** por API Key; permissões por escopo.
- **Sem PII em logs**; erros via handler único + `request_id`.
- **Validação** anti injeções; mass assignment controlado.
- **Dependências**: alertas de segurança do GitHub tratados.

---

## 13) Observabilidade & Perf
- **Health/Metrics** ativos; erros e latência acompanhados.
- **Orçamentos** por endpoint; alertas quando ultrapassar.
- **Auditoria** de operações críticas (sem dados sensíveis).

---

## 14) Como o Agente de IA deve atuar
- **Antes de qualquer alteração**, criar/atualizar a **Task** com o template do §7.
- **Executar apenas** o que estiver descrito e aprovado na Task.
- **Anexar** ao PR: listas de verificação atendidas e referências ao Playbook/Testes.
- **Não** extrapolar escopo (sem “mágica”). Qualquer lacuna → abrir nova Task.

---

## 15) Template — `BIBLE_API_BASE_PROJECT.md` (esqueleto)
> Use este esqueleto caso o documento de visão ainda não exista.

**Visão**: onde queremos chegar (ex.: “Estudo bíblico programável, seguro e performático”).
**Pilares**: estabilidade do contrato, performance (p95 X ms), DX (Swagger completo), segurança.
**KPIs/Sucesso**: uptime, erro rate, p95, time-to-first-API, cobertura de testes, lat/erro por domínio.
**Escopo v1**: domínios incluídos (books/verses/themes/…).
**Não escopo**: UI web, autenticação social, etc.
**Roadmap**: fases e épicos (ver §6).
**Riscos**: licenças de textos, custos TTS, cargas, limites de terceiros.
**Padrões**: versionamento, OpenAPI como fonte de verdade, migrations pequenas.
**Governança**: papéis, branch protection, CI required.

---

## 16) Referências Cruzadas
- **Playbook de Dev** → `DEV_FLOW_PLAYBOOK.md`
- **Boas Práticas de Testes** → `API_TESTING_BEST_PRACTICES.md`
- **Visão** → `BIBLE_API_BASE_PROJECT.md`

> Manter estes três documentos alinhados. Qualquer divergência → atualizar todos na mesma PR.

---

## 17) Manutenção deste Orquestrador
- Toda mudança de processo **passa por PR** alterando **este** arquivo.
- O PR deve linkar exemplos e apontar impactos nos outros dois docs (Playbook/Testes).
- Versione o orquestrador quando houver mudanças estruturais no processo: mantenha um *changelog interno* ao final deste arquivo.

---

### Changelog (do Orquestrador)
- v1.0 — versão inicial do orquestrador.
