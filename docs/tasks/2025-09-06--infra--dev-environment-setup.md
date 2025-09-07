---
id: T-000-dev-setup
title: "[infra] Setup Development Environment — Docker, Dependencies & Tooling"
status: pr_draft
created: 2025-09-06
updated: 2025-09-06
owner: "@claude-agent"
reviewers: ["@maintainer"]
labels: ["area/infra", "type/feat"]
priority: urgent
effort: M
risk: low
depends_on: []
related: ["T-001-django-setup"]
epic: "fase-0-boot"
branch: "feat/dev-environment-setup"
pr: ""
github_issue: "https://github.com/PluraNex/bible-api/issues/1"
due: null
---

## Contexto
- **Problema**: Projeto precisa de ambiente de desenvolvimento padronizado e reproduzível para todos os desenvolvedores e agentes IA
- **Valor**: Garante consistência entre ambientes, facilita onboarding e elimina "funciona na minha máquina"
- **Hipóteses**: Docker como padrão para containerização; PostgreSQL e Redis como dependências principais
- **Restrições**: Deve funcionar em Windows, macOS e Linux; setup simples em poucos comandos

## Objetivo e Critérios de Aceite
- [ ] CA1 — Docker Compose configurado com PostgreSQL, Redis e aplicação Django
- [ ] CA2 — Dependências Python gerenciadas (pyproject.toml + requirements.txt)
- [ ] CA3 — Makefile com comandos de desenvolvimento (setup, test, lint, format)
- [ ] CA4 — GitHub Actions workflow configurado (4 jobs obrigatórios)
- [ ] CA5 — Configuração de ambiente (.env.example, .gitignore, .editorconfig)
- [ ] CA6 — Scripts de inicialização (migrations, superuser, dados base)
- [ ] CA7 — Documentação de setup no README.md
- [ ] CA8 — Validação funciona: `make setup && make test` executa sem erros

## Escopo / Fora do Escopo
**Inclui:**
- **Docker**: Dockerfile, docker-compose.yml (app, postgres, redis)
- **Dependências**: pyproject.toml, requirements.txt, requirements-dev.txt
- **Tooling**: ruff, black, pytest, coverage
- **CI/CD**: GitHub Actions (.github/workflows/ci.yml)
- **Scripts**: Makefile, scripts/setup.sh, scripts/wait-for-it.sh
- **Config**: .env.example, .gitignore, .editorconfig, .dockerignore
- **Docs**: README.md com quick start
- **VS Code**: .vscode/settings.json com configurações recomendadas

**Não inclui:**
- Código Django (será na T-001)
- Deploy para produção
- Monitoring/observability tools
- SSL/certificados
- Backup/restore procedures

## Impacto Técnico
**Contrato (OpenAPI)**: Nenhum impacto (pré-código)
**DB/Migrations**: PostgreSQL configurado, pronto para migrations
**Throttle/Cache**: Redis configurado, pronto para uso
**Performance**: Containers otimizados para desenvolvimento (não produção)
**Segurança**: Secrets via .env, PostgreSQL com credenciais seguras, .gitignore protegendo arquivos sensíveis

## Plano de Testes
**Ambiente**:
- Docker containers sobem sem erro: `docker-compose up -d`
- PostgreSQL aceita conexões: `make db-check`
- Redis aceita conexões: `make redis-check`
- Python dependencies instalam: `pip install -r requirements-dev.txt`

**CI/CD**:
- GitHub Actions executa sem erro em push/PR
- Jobs paralelos executam em tempo < 5min total
- Artifacts (coverage, logs) são gerados

**Comandos**:
- `make setup` configura ambiente completo
- `make test` executa sem falhas
- `make lint` passa sem warnings
- `make format` formata código corretamente

## Observabilidade
- Logs Docker configurados (JSON format)
- Health checks nos containers (PostgreSQL, Redis)
- CI metrics (tempo execução, success rate)
- Coverage reports gerados

## Rollout & Rollback
**Plano de ativação:**
1. Merger PR com configurações
2. Desenvolvedores rodam `make setup`
3. Validar CI executa corretamente

**Critérios de sucesso:**
- Qualquer desenvolvedor pode setup em < 5min
- CI jobs passam consistentemente
- Containers sobem sem configuração manual

**Estratégia de reversão:**
- Reverter PR se CI falhar
- Containers podem ser removidos: `docker-compose down -v`
- Sem impacto em dados (ambiente novo)

## Checklist Operacional (Autor)
- [ ] Docker Compose testado em ambiente local
- [ ] GitHub Actions valida em fork/branch
- [ ] Makefile commands executam sem erro
- [ ] README.md tem instruções claras de setup
- [ ] .env.example tem todas as variáveis necessárias

## Checklist Operacional (Revisor)
- [ ] Dockerfile segue best practices (non-root user, multi-stage se aplicável)
- [ ] docker-compose.yml tem health checks e restart policies
- [ ] GitHub Actions usa caching apropriado
- [ ] Dependências Python fixadas em versões específicas
- [ ] .gitignore cobre todos os arquivos sensíveis/gerados
- [ ] Scripts shell são idempotentes e têm error handling
