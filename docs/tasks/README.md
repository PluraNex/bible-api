# Tasks — Diretório Oficial

Este diretório concentra **todas as tarefas** (issues) do projeto em arquivos **Markdown** versionados.

> **Regra de ouro**: antes de qualquer implementação, crie/atualize uma **Task** aqui.
> Este fluxo está alinhado com o **[BIBLE_API_ORCHESTRATOR](../BIBLE_API_ORCHESTRATOR.md)**, o **[DEV_FLOW_PLAYBOOK](../DEV_FLOW_PLAYBOOK.md)** e o **[API_TESTING_BEST_PRACTICES](../API_TESTING_BEST_PRACTICES.md)**.

---

## Convenções

### Estrutura
```
tasks/
├─ README.md
├─ INDEX.md                # catálogo das tasks (atualizado manualmente)
└─ TASK_TEMPLATE.md        # template oficial
```

### Nome de arquivo
Use o padrão: `YYYY-MM-DD--area--slug.md`
Ex.: `2025-09-06--api--versions-listing.md`

### Status (workflow)
- `backlog` → `ready` → `in_progress` → `pr_draft` → `in_review` → `merged` → `done`
- Máximo de **3** tasks em `in_progress` por pessoa/agente.

### Labels
- `area/api`, `area/auth`, `area/audio`, `area/ai`, `area/resources`, `area/infra`, `area/docs`
- `type/feat`, `type/fix`, `type/chore`, `type/refactor`, `type/docs`, `type/test`
- `needs-schema`, `breaking`, `security`, `performance`, `observability`

### Branch e PR
- Branch: `feat/<slug>` (ou `fix/...`), referencie a Task e Issue no título/descrição.
- PR: siga o template do **Orchestrator §8**.
- Link: conecte PR à Issue GitHub usando "Closes #123" na descrição.
- CI precisa estar **verde** antes do merge.

---

## Como criar uma Task

### Fluxo Completo (Task Local + Issue GitHub)
1. **Crie a task local**: Copie o **TASK_TEMPLATE.md** para `tasks/YYYY-MM-DD--area--slug.md`.
2. **Preencha completamente**: front-matter, critérios de aceite, impacto técnico, plano de testes.
3. **Crie issue no GitHub**:
   - Título: use o mesmo da task (`title` field)
   - Labels: aplique as mesmas labels (`labels` field)
   - Descrição: copie as seções principais (Contexto, Objetivo, Critérios de Aceite)
   - Milestone: defina conforme epic
4. **Sincronize referências**:
   - Adicione URL da issue no campo `github_issue` da task
   - Adicione link da task local na descrição da issue
5. **Atualize INDEX.md**: adicione entrada na tabela com links para task e issue.
6. **Marque como ready**: altere `status: ready` quando refinamento estiver completo.
7. **Inicie desenvolvimento**: abra branch e comece trabalho.

---

## Manutenção
- Alterações de processo devem começar em `BIBLE_API_ORCHESTRATOR.md`.
- Mantenha status e datas coerentes (created/updated).
- Fechou PR? Atualize `status` e `INDEX.md`.
