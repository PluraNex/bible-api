.PHONY: help setup build up down logs shell test lint format clean db-reset db-check redis-check

# Default target
help: ## Show this help message
	@echo "Bible API Development Commands"
	@echo "============================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Setup commands
setup: ## Complete development environment setup
	@echo "🚀 Setting up Bible API development environment..."
	@docker-compose build
	@docker-compose up -d db redis
	@echo "⏳ Waiting for database to be ready..."
	@$(MAKE) db-check
	@echo "⏳ Waiting for Redis to be ready..."
	@$(MAKE) redis-check
	@echo "📦 Installing Python dependencies..."
	@pip install -r requirements-dev.txt
	@echo "✅ Setup complete! Use 'make up' to start all services."

build: ## Build Docker containers
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## Show logs from all services
	docker-compose logs -f

shell: ## Open Django shell
	docker-compose exec web python manage.py shell

# Testing commands
test: ## Run all tests with coverage
	@echo "🧪 Running tests with coverage..."
	pytest

test-fast: ## Run tests without coverage
	@echo "🏃 Running fast tests..."
	pytest --no-cov

test-verbose: ## Run tests with verbose output
	@echo "🔍 Running tests with verbose output..."
	pytest -v

# Coverage commands
coverage: ## Run tests with coverage report
	@echo "📊 Running tests with coverage..."
	pytest --cov=bible --cov=config --cov=common --cov-report=term-missing --cov-report=html --cov-report=xml

coverage-html: ## Generate HTML coverage report
	@echo "🌐 Generating HTML coverage report..."
	pytest --cov=bible --cov=config --cov=common --cov-report=html
	@echo "📊 Coverage report generated at htmlcov/index.html"

coverage-xml: ## Generate XML coverage report for CI
	@echo "📄 Generating XML coverage report..."
	pytest --cov=bible --cov=config --cov=common --cov-report=xml

# Code quality commands
lint: ## Run linter (ruff)
	@echo "🔍 Running linter..."
	ruff check .
	ruff check . --output-format=github

format: ## Format code with black and ruff
	@echo "🎨 Formatting code..."
	black .
	ruff check . --fix

format-check: ## Check code formatting without making changes
	@echo "✅ Checking code formatting..."
	black --check .
	ruff check .

# Database commands
db-check: ## Check database connectivity
	@echo "🔍 Checking database connectivity..."
	@timeout 60 bash -c 'until docker-compose exec -T db pg_isready -U bible_user -d bible_api; do sleep 1; done'
	@echo "✅ Database is ready!"

redis-check: ## Check Redis connectivity
	@echo "🔍 Checking Redis connectivity..."
	@timeout 60 bash -c 'until docker-compose exec -T redis redis-cli ping | grep -q PONG; do sleep 1; done'
	@echo "✅ Redis is ready!"

db-reset: ## Reset database (remove all data)
	@echo "⚠️  Resetting database..."
	docker-compose down
	docker volume rm bible-api_postgres_data || true
	docker-compose up -d db
	@$(MAKE) db-check

# Utility commands
clean: ## Clean up containers, volumes, and cache
	@echo "🧹 Cleaning up..."
	docker-compose down -v
	docker system prune -f
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

install-hooks: ## Install pre-commit hooks
	@echo "🪝 Installing pre-commit hooks..."
	pre-commit install

# CI simulation
ci: format-check lint coverage ## Run all CI checks locally

# Development helpers
dev-setup: setup install-hooks ## Complete setup for new developers
	@echo "🎉 Development environment ready!"
	@echo "Next steps:"
	@echo "  1. Run 'make up' to start services"
	@echo "  2. Create Django project in next task"

# Status check
status: ## Show status of all services
	@echo "📊 Service Status:"
	@docker-compose ps