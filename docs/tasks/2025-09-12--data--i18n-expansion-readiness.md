---
id: T-I18N17
title: "[data] I18N — Readiness para expansão de idiomas (bases ISO, defaults e checks)"
status: backlog
created: 2025-09-12
updated: 2025-09-12
owner: "@iuryeng"
reviewers: ["@iuryeng"]
labels: ["area/data", "type/chore", "i18n"]
priority: high
effort: S
risk: low
depends_on: ["T-I18N01", "T-I18N02", "T-I18N15"]
related: ["T-I18N08"]
epic: "I18N — Suporte Multilíngue"
branch: "chore/i18n-expansion-readiness"
pr: ""
github_issue: ""
due: null
---

## Contexto
Já preparamos a API para i18n com `lang`/`Accept-Language` e serializers/views usando `request.lang_code`. Para facilitar expansão futura (ex.: `es`) sem retrabalho, precisamos garantir que a base de dados e os comandos estejam prontos: idiomas base ISO existentes (pt, en), nomes default por idioma (`BookName` com `version IS NULL`) e validações para evitar uso de regionais em defaults.

Esta task NÃO altera dado existente de forma destrutiva; apenas prepara e corrige lacunas de forma idempotente.

### Fonte de dados (referência)
- Repositório: scrollmapper/bible_databases — branch `2025-languages`
  - URL: https://github.com/scrollmapper/bible_databases/tree/2025-languages
  - Notas:
    - O projeto mantém múltiplas traduções e mapeamentos (OSIS, nomes, abreviações) em vários formatos.
    - A documentação da estrutura atualizada está em `docs/` dessa branch (paths de “keys” por idioma podem ter mudado em relação à branch 2024).
    - Quando formos expandir idiomas (ex.: `es`), usar estes artefatos como fonte para `BookName` default por idioma (version = NULL), respeitando ISO base (`es`).

## Objetivo e Critérios de Aceite
- [ ] CA1 — Garantir presença de `Language('pt')` e `Language('en')` (além de regionais já existentes)
- [ ] CA2 — Comando de preparação que replica `BookName` default de regionais para base quando faltarem (ex.: `pt-BR` → `pt`, `en-US` → `en`), sem sobrescrever por padrão
- [ ] CA3 — `--dry-run` mostra relatório (criaria/atualizaria) e não altera dados
- [ ] CA4 — `--overwrite` permite atualização opcional e explícita
- [ ] CA5 — Relatório final com contagem de criados/atualizados/pulados e lacunas remanescentes
- [ ] CA6 — Documentação breve no `API_STANDARDS.md` sobre defaults em base ISO e regionais em `Version`

## Escopo / Fora do Escopo
- Inclui: novo management command idempotente (ex.: `prepare_i18n_defaults`), criação segura de `Language('pt')`/`Language('en')`, relatório
- Não inclui: popular `BookName` para novos idiomas (coberto em T-I18N08), mudanças em versões/textos, remoção de regionais

## Plano (implementação sugerida)
1) Criar comando `data/management/commands/prepare_i18n_defaults.py`
   - Args: `--dry-run`, `--overwrite`
   - Passos:
     - `get_or_create(Language, code='pt')` e `get_or_create(Language, code='en')`
     - Para cada `CanonicalBook`:
       - Se houver `BookName(language.code in ['pt-BR','pt'], version=None)`, garantir `BookName(language='pt', version=None)` — criar quando faltante
       - Se houver `BookName(language.code in ['en-US','en'], version=None)`, garantir `BookName(language='en', version=None)`
     - Nunca sobrescrever por padrão; só com `--overwrite`
     - Relatar por idioma: criados/atualizados/pulados e livros sem dados para base
2) Adicionar nota em `docs/API_STANDARDS.md` §6 reforçando: defaults em base ISO; regionais apenas em `Version.language`
3) (Opcional) Pequeno teste de smoke para o comando (execução com banco mínimo)

## Impacto Técnico
**Contrato**: n/a | **DB/Migrations**: n/a (apenas inserções idempotentes) | **Segurança**: n/a | **Performance**: baixo impacto

## Plano de Testes
- Rodar `--dry-run` em base atual e verificar relatório coerente
- Rodar sem flags e confirmar criação apenas quando faltante
- Rodar com `--overwrite` (ambiente de teste) e validar atualização controlada

## Observabilidade
- Logs resumidos no stdout do management command

## Rollout & Rollback
- Rollout seguro (somente inserts/updates opcionais); rollback não necessário

## Checklist Operacional (Autor)
- [ ] Comando criado e idempotente
- [ ] `make fmt lint` ok
- [ ] Nota adicionada no `API_STANDARDS.md`

## Checklist Operacional (Revisor)
- [ ] Sem quebras de contrato
- [ ] Execução segura em produção (dry-run confiável)
- [ ] Relatório claro e útil
