# GitHub Integration Guide

Este guia explica como sincronizar tasks locais com issues do GitHub para máxima visibilidade e rastreabilidade.

## Fluxo de Trabalho Integrado

### 1. Criar Issue no GitHub

Após criar a task local (seguindo `tasks/README.md`), crie a issue correspondente:

**Título**: Use exatamente o mesmo da task
```
[api] Setup Django Project Structure — Core API Foundation
```

**Labels**: Aplique as mesmas labels da task
- `area/api`, `area/auth`, `area/audio`, `area/ai`, `area/resources`, `area/infra`, `area/docs`
- `type/feat`, `type/fix`, `type/chore`, `type/refactor`, `type/docs`, `type/test`
- `needs-schema`, `breaking`, `security`, `performance`, `observability`

**Milestone**: Defina conforme epic (ex: "Fase 0 - Boot")

**Descrição Template**:
```markdown
## Contexto
[Copie da task local]

## Objetivo e Critérios de Aceite
[Copie da task local]

## Impacto Técnico
[Resumo do impacto da task local]

---
**Task Local**: [Link para o arquivo da task no repo]
**Epic**: [Nome do épico]
**Priority**: [high/medium/low]
```

### 2. Sincronizar Referências

**Na Task Local**:
- Adicione URL da issue no campo `github_issue`
- Atualize o `INDEX.md` com link para a issue

**Na Issue GitHub**:
- Adicione link para a task local na descrição
- Use a seção "Task Local" no template

### 3. Branch e PR

**Ao criar branch**:
```bash
git checkout -b feat/django-project-setup
git push -u origin feat/django-project-setup
```

**No PR description**, conecte à issue:
```markdown
## O que foi implementado
[Descrição das mudanças]

## Critérios de Aceite Atendidos
- [x] CA1 — Django project criado
- [x] CA2 — Apps principais configurados
- [ ] CA3 — URLs estruturados (em progresso)

Closes #123
```

### 4. Atualização de Status

Mantenha sincronizados:

| Task Status | Issue Status | GitHub State |
|---|---|---|
| backlog | Aberta | Open |
| ready | Aberta + label "ready" | Open |
| in_progress | Aberta + label "in progress" | Open |
| pr_draft | Aberta + PR draft | Open |
| in_review | Aberta + PR review | Open |
| merged | Fechada + PR merged | Closed |
| done | Fechada + validação | Closed |

## Automações Sugeridas

### GitHub Actions
Considere criar automações para:
- Auto-aplicar labels baseado no título
- Atualizar milestone baseado em convenções
- Comentar na issue quando PR é aberto/merged

### Scripts Locais
Scripts utilitários para:
- Criar issue GitHub a partir de task local
- Sincronizar status entre task e issue
- Gerar relatórios de progresso

## Benefícios da Integração

1. **Visibilidade**: Issues aparecem no GitHub para stakeholders
2. **Rastreabilidade**: Histórico completo de discussões e decisões
3. **Automação**: PRs se conectam automaticamente às issues
4. **Métricas**: GitHub Insights mostra progresso do projeto
5. **Colaboração**: Facilita code review e feedback

## Template de Issue Completo

```markdown
## Contexto
- **Problema**: [Descrição do problema]
- **Valor**: [Valor para usuário/sistema]
- **Hipóteses**: [Premissas assumidas]
- **Restrições**: [Limitações conhecidas]

## Objetivo e Critérios de Aceite
- [ ] CA1 — [Critério específico e mensurável]
- [ ] CA2 — [Critério específico e mensurável]
- [ ] CA3 — [Critério específico e mensurável]

## Impacto Técnico
**OpenAPI**: [Mudanças no contrato]
**Database**: [Migrations necessárias]
**Performance**: [Orçamentos e riscos]
**Security**: [Considerações de segurança]

## Acceptance Tests
- [ ] API retorna 200 para casos felizes
- [ ] API retorna 4xx para validações
- [ ] Schema OpenAPI atualizado
- [ ] Migrations aplicam sem erro

---
**Task Local**: `tasks/YYYY-MM-DD--area--slug.md`
**Epic**: [Nome do épico]
**Priority**: [high/medium/low]
**Effort**: [XS/S/M/L/XL]
```

## Checklist de Sincronização

**Ao criar task/issue**:
- [ ] Task local criada e preenchida
- [ ] Issue GitHub criada com mesmo título
- [ ] Labels aplicadas consistentemente
- [ ] Milestone definido conforme epic
- [ ] Referências cruzadas adicionadas
- [ ] INDEX.md atualizado

**Durante desenvolvimento**:
- [ ] Status sincronizado entre task e issue
- [ ] Comentários importantes replicados
- [ ] PR conectado à issue com "Closes #N"

**Ao finalizar**:
- [ ] Todos CAs marcados como completos
- [ ] Issue fechada automaticamente pelo merge
- [ ] Task marcada como "done" após validação