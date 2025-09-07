# Bible API - Development Makefile

.PHONY: help setup-repo check-protection fmt lint test coverage clean install dev migrate migrations schema docker-build docker-logs docker-shell ci-lint ci-test ci-schema ci-all release-check ready dev-cycle hooks-setup hooks-run

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
	@docker-compose exec web pytest --cov=bible --cov=config --cov=common --cov-report=xml --cov-fail-under=80 -v

ci-schema: ## Generate CI schema locally
	@echo "📄 Generating CI schema locally..."
	@docker-compose exec web python manage.py spectacular --color --file schema.yml
	@docker-compose exec web python -c "import yaml; schema = yaml.safe_load(open('schema.yml')); assert len(schema['paths']) >= 5; print(f'✅ Schema validation passed: {len(schema[\"paths\"])} endpoints found')"

ci-all: ci-lint ci-test ci-schema ## Run all CI checks locally
	@echo "✅ All CI checks passed locally!"

# Release commands
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
