## Issue Title
[infra] Setup Development Environment — Docker, Dependencies & Tooling

## Labels
- area/infra
- type/feat

## Milestone
Fase 0 - Boot

## Description

### Contexto
- **Problema**: Projeto precisa de ambiente de desenvolvimento padronizado e reproduzível para todos os desenvolvedores e agentes IA
- **Valor**: Garante consistência entre ambientes, facilita onboarding e elimina "funciona na minha máquina"
- **Hipóteses**: Docker como padrão para containerização; PostgreSQL e Redis como dependências principais
- **Restrições**: Deve funcionar em Windows, macOS e Linux; setup simples em poucos comandos

### Objetivo e Critérios de Aceite
- [ ] CA1 — Docker Compose configurado com PostgreSQL, Redis e aplicação Django
- [ ] CA2 — Dependências Python gerenciadas (pyproject.toml + requirements.txt)
- [ ] CA3 — Makefile com comandos de desenvolvimento (setup, test, lint, format)
- [ ] CA4 — GitHub Actions workflow configurado (4 jobs obrigatórios)
- [ ] CA5 — Configuração de ambiente (.env.example, .gitignore, .editorconfig)
- [ ] CA6 — Scripts de inicialização (migrations, superuser, dados base)
- [ ] CA7 — Documentação de setup no README.md
- [ ] CA8 — Validação funciona: `make setup && make test` executa sem erros

### Impacto Técnico
**OpenAPI**: Nenhum impacto (pré-código)
**Database**: PostgreSQL configurado, pronto para migrations
**Performance**: Containers otimizados para desenvolvimento
**Security**: Secrets via .env, PostgreSQL com credenciais seguras

### Acceptance Tests
- [ ] Docker containers sobem sem erro: `docker-compose up -d`
- [ ] PostgreSQL aceita conexões: `make db-check`
- [ ] Redis aceita conexões: `make redis-check`
- [ ] GitHub Actions executa sem erro em push/PR
- [ ] `make setup` configura ambiente completo
- [ ] `make test` executa sem falhas

---
**Task Local**: `tasks/2025-09-06--infra--dev-environment-setup.md`
**Epic**: Fase 0 - Boot
**Priority**: urgent
**Effort**: M
