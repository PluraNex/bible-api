# Bible API - Development Makefile

.PHONY: help setup-repo check-protection fmt lint test coverage clean install dev migrate migrations schema docker-build docker-logs docker-shell ci-lint ci-test ci-schema ci-all i18n-audit i18n-audit-ci i18n-report release-check ready dev-cycle hooks-setup hooks-run data-setup data-setup-local data-status data-status-local data-cleanup data-cleanup-execute data-validate data-pipeline ci-data-health ci-data-cleanup lang-patterns lang-analyze lang-analyze-detailed lang-analyze-local lang-validate lang-portuguese lang-english lang-german lang-french

# Default target
help: ## Show this help message
	@echo "Bible API - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Repository setup
setup-repo: ## Configure repository with branch protection and labels
	@echo "🔧 Setting up repository..."
	@chmod +x scripts/setup-repo.sh
	@./scripts/setup-repo.sh

check-protection: ## Check current branch protection status
	@echo "🔒 Checking branch protection..."
	@gh api repos/PluraNex/bible-api/branches/main/protection || echo "❌ Branch protection not configured"

# Development commands
install: ## Install dependencies
	@echo "📦 Installing dependencies..."
	@pip install -r requirements-dev.txt

dev: ## Start development environment
	@echo "🚀 Starting development environment..."
	@docker-compose up -d
	@echo "✅ Services started. Django: http://localhost:8000"

# Code quality
fmt: ## Format code with black and ruff
	@echo "🎨 Formatting code..."
	@black .
	@ruff check --fix .

lint: ## Run linting checks
	@echo "🔍 Running linting..."
	@ruff check .
	@black --check .

# Testing
test: ## Run test suite
	@echo "🧪 Running tests..."
	@pytest -v

coverage: ## Run tests with coverage report
	@echo "📊 Running tests with coverage..."
	@pytest --cov=bible --cov=config --cov=common --cov-report=term-missing --cov-report=html
	@echo "📄 Coverage report: htmlcov/index.html"

# Django commands
migrate: ## Apply database migrations
	@echo "🗃️ Applying migrations..."
	@docker-compose exec web python manage.py migrate

migrations: ## Create new migrations
	@echo "📝 Creating migrations..."
	@docker-compose exec web python manage.py makemigrations

schema: ## Generate OpenAPI schema
	@echo "📄 Generating OpenAPI schema..."
	@docker-compose exec web python manage.py spectacular --color --file schema.yml
	@echo "✅ Schema saved to: schema.yml"

# Cleanup
clean: ## Clean up temporary files and caches
	@echo "🧹 Cleaning up..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@rm -rf .pytest_cache
	@rm -rf htmlcov
	@rm -rf .coverage
	@docker system prune -f

# Docker commands
docker-build: ## Build Docker containers
	@echo "🐳 Building Docker containers..."
	@docker-compose build

docker-logs: ## Show Docker logs
	@docker-compose logs -f

docker-shell: ## Open shell in web container
	@docker-compose exec web /bin/bash

# CI/CD validation
ci-lint: ## Run CI linting locally
	@echo "🔍 Running CI lint checks locally..."
	@docker-compose exec web ruff check . --output-format=github
	@docker-compose exec web black --check .

ci-test: ## Run CI tests locally
	@echo "🧪 Running CI tests locally..."
	@docker-compose exec web pytest --cov=bible --cov=config --cov=common --cov-report=xml --cov-fail-under=77 -v

ci-schema: ## Generate CI schema locally
	@echo "📄 Generating CI schema locally..."
	@docker-compose exec web python manage.py spectacular --color --file schema.yml
	@docker-compose exec web python -c "import yaml; schema = yaml.safe_load(open('schema.yml')); assert len(schema['paths']) >= 5; print(f'✅ Schema validation passed: {len(schema[\"paths\"])} endpoints found')"

ci-all: ci-lint ci-test ci-schema i18n-audit-ci ## Run all CI checks locally
	@echo "✅ All CI checks passed locally!"

# Release commands
# I18n governance commands
i18n-audit: ## Run I18n audit (read-only)
	@echo "🌍 Running I18n audit (read-only)..."
	@docker-compose exec web python manage.py audit_i18n --report-only

i18n-audit-ci: ## Run I18n audit for CI/CD
	@echo "🌍 Running I18n audit for CI/CD..."
	@docker-compose exec web python manage.py audit_i18n \
		--report-only \
		--fail-on-missing \
		--min-coverage=90 \
		--languages=pt,en \
		--include-deuterocanon

i18n-report: ## Generate detailed I18n coverage report
	@echo "🌍 Generating detailed I18n coverage report..."
	@mkdir -p reports
	@docker-compose exec web python manage.py audit_i18n \
		--report-file=reports/i18n_coverage_$(shell date +%Y%m%d).json \
		--languages=pt,en

release-check: ## Check if ready for release
	@echo "🔍 Checking release readiness..."
	@make ci-all
	@make check-protection
	@echo "✅ Ready for release!"

# Development workflow
ready: fmt lint test schema ## Prepare code for PR (format, lint, test, schema)
	@echo "✅ Code is ready for PR!"

# Quick development cycle
dev-cycle: ## Quick development cycle: format, test, check
	@make fmt
	@make test
	@echo "✅ Development cycle complete!"

# Database shortcuts
db-reset: ## Reset database (WARNING: destroys all data)
	@echo "🗑️ Resetting database..."
	@docker-compose down -v
	@docker-compose up -d db redis
	@sleep 5
	@make migrate
	@echo "✅ Database reset complete"

db-shell: ## Open database shell
	@echo "🗃️ Opening database shell..."
	@docker-compose exec db psql -U bible_user -d bible_api

# Logs and debugging
logs: ## Show all container logs
	@docker-compose logs -f

logs-web: ## Show web container logs only
	@docker-compose logs -f web

logs-db: ## Show database logs only
	@docker-compose logs -f db

# Health checks
health: ## Check service health
	@echo "🏥 Checking service health..."
	@curl -s http://localhost:8000/health/ | python -m json.tool || echo "❌ Health check failed"
	@curl -s http://localhost:8000/metrics/ | python -m json.tool || echo "❌ Metrics check failed"

# API testing
api-test: ## Test API endpoints
	@echo "🔍 Testing API endpoints..."
	@curl -s http://localhost:8000/health/ && echo " ✅ Health"
	@curl -s http://localhost:8000/metrics/ && echo " ✅ Metrics"
	@curl -s http://localhost:8000/api/v1/schema/ | head -1 && echo " ✅ Schema"
	@curl -s http://localhost:8000/api/v1/ai/agents/ && echo " ✅ AI Agents"
	@curl -s http://localhost:8000/api/v1/ai/tools/ && echo " ✅ AI Tools"

# RAG tasks
embeddings-generate: ## Generate embeddings for Fase 0 versions (requires OPENAI_API_KEY)
	@echo "🧠 Generating embeddings (Fase 0)..."
	@docker-compose exec web python manage.py generate_embeddings --versions=$${RAG_ALLOWED_VERSIONS:-PT_NAA,PT_ARA,PT_NTLH,EN_KJV} --batch-size=$${EMBEDDING_BATCH_SIZE:-128}

# Observability stack
prometheus-up: ## Start Prometheus server (scrapes Django metrics)
	@echo "📈 Starting Prometheus on http://localhost:9090 ..."
	@docker-compose up -d prometheus
	@echo "🔎 Scraping target: http://localhost:8000/metrics/prometheus/"

grafana-up: ## Start Grafana (admin/admin) with Prometheus datasource
	@echo "📊 Starting Grafana on http://localhost:3000 ... (admin/admin)"
	@docker-compose up -d grafana
	@echo "🔗 Default datasource: Prometheus (http://prometheus:9090)"

# Data pipeline commands
data-setup: ## Initialize data pipeline directory structure
	@echo "📁 Setting up data pipeline structure..."
	@docker-compose exec web python manage.py data setup

data-setup-local: ## Initialize data pipeline locally (no Docker)
	@echo "📁 Setting up data pipeline structure locally..."
	@python manage.py data setup

data-status: ## Show data pipeline status
	@echo "📊 Checking data pipeline status..."
	@docker-compose exec web python manage.py data status

data-status-local: ## Show data pipeline status locally
	@echo "📊 Checking data pipeline status locally..."
	@python manage.py data status

data-cleanup: ## Clean temporary files (dry-run preview)
	@echo "🧹 Previewing data cleanup..."
	@docker-compose exec web python manage.py data cleanup --dry-run

data-cleanup-execute: ## Execute cleanup (removes files)
	@echo "🧹 Executing data cleanup..."
	@docker-compose exec web python manage.py data cleanup --retention-days 7

data-validate: ## Validate data files against schemas
	@echo "✅ Available schemas:"
	@docker-compose exec web python manage.py data validate --schema manifest-v1

data-pipeline: ## Complete pipeline setup and status check
	@make data-setup
	@make data-status
	@echo "✅ Data pipeline ready!"

# CI/CD data pipeline checks
ci-data-health: ## CI health check for data pipeline (fast)
	@echo "🏥 Checking data pipeline health for CI..."
	@docker-compose exec web python manage.py data status --report-file reports/data-health.json

ci-data-cleanup: ## CI cleanup preview (conservative)
	@echo "🧹 CI data cleanup preview..."
	@docker-compose exec web python manage.py data cleanup --retention-days 30 --dry-run

# Language detection and analysis
lang-patterns: ## Show supported language detection patterns
	@echo "🌍 Showing supported language patterns..."
	@python scripts/analyze_languages.py --show-patterns

lang-analyze: ## Analyze multilingual Bible files by language
	@echo "🔍 Analyzing multilingual Bible files..."
	@python scripts/analyze_languages.py data/datasets/json --summary-only

lang-analyze-detailed: ## Generate detailed language analysis report
	@echo "📊 Generating detailed language analysis..."
	@mkdir -p reports
	@python scripts/analyze_languages.py data/datasets/json --output reports/language-analysis.json

lang-analyze-docker: ## Analyze languages via Docker (external use)
	@echo "🔍 Analyzing languages via Docker..."
	@docker-compose exec web python scripts/analyze_languages.py data/datasets/json --summary-only

lang-validate: ## Validate language detection accuracy (high confidence files)
	@echo "✅ Validating language detection accuracy..."
	@python scripts/analyze_languages.py data/datasets/json --min-confidence 0.8

# Language-specific analysis
lang-portuguese: ## Show Portuguese Bible files detected
	@echo "🇵🇹 Showing Portuguese Bible files..."
	@python scripts/analyze_languages.py data/datasets/json --language pt

lang-english: ## Show English Bible files detected
	@echo "🇺🇸 Showing English Bible files..."
	@python scripts/analyze_languages.py data/datasets/json --language en

lang-german: ## Show German Bible files detected
	@echo "🇩🇪 Showing German Bible files..."
	@python scripts/analyze_languages.py data/datasets/json --language de

lang-french: ## Show French Bible files detected
	@echo "🇫🇷 Showing French Bible files..."
	@python scripts/analyze_languages.py data/datasets/json --language fr
