# Bible API

A comprehensive RESTful Bible API with AI integration, built with Django REST Framework.

## Features

- 📖 **Complete Bible Data**: Books, verses, themes, and cross-references
- 🔐 **API Key Authentication**: Secure access with scoped permissions
- 🤖 **AI Integration**: Agent-based AI tools for biblical analysis
- 🎵 **Audio Support**: Text-to-speech for verses and passages
- 📚 **External Resources**: Integration with biblical study materials
- 🔍 **Advanced Search**: Full-text search with filters and ordering
- 📊 **OpenAPI/Swagger**: Complete API documentation
- ⚡ **High Performance**: Optimized queries and caching strategies
- 🐳 **Docker Ready**: Containerized development and deployment

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Python 3.11+](https://www.python.org/downloads/) (optional, for local development)
- [Make](https://www.gnu.org/software/make/) (optional, for convenience commands)

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd bible-api
   ```

2. **Run the setup script**:
   ```bash
   # Option 1: Using the setup script (recommended)
   ./scripts/setup.sh
   
   # Option 2: Using Make
   make dev-setup
   
   # Option 3: Manual setup
   cp .env.example .env
   docker-compose build
   docker-compose up -d db redis
   ```

3. **Start all services**:
   ```bash
   make up
   # or
   docker-compose up -d
   ```

4. **Verify the installation**:
   ```bash
   # Check service health
   curl http://localhost:8000/health
   
   # View API documentation
   open http://localhost:8000/api/v1/schema/swagger-ui/
   ```

## Development Commands

We provide a comprehensive Makefile for common development tasks:

```bash
# Setup and start services
make dev-setup          # Complete setup for new developers
make up                  # Start all services
make down                # Stop all services
make logs                # Show logs from all services

# Testing and quality
make test                # Run all tests with coverage
make test-fast           # Run tests without coverage
make lint                # Run linter (ruff)
make format              # Format code with black and ruff
make ci                  # Run all CI checks locally

# Database operations
make db-check            # Check database connectivity
make redis-check         # Check Redis connectivity
make db-reset            # Reset database (removes all data)

# Utilities
make shell               # Open Django shell
make clean               # Clean up containers and volumes
make status              # Show status of all services
make help                # Show all available commands
```

## Architecture

### Project Structure

```
bible-api/
├── config/              # Django configuration
├── bible/               # Main Django app
│   ├── models/          # Database models
│   ├── apps/            # Feature-specific apps
│   │   ├── auth/        # API key authentication
│   │   ├── audio/       # Text-to-speech functionality
│   │   └── resources/   # External resources integration
│   └── ai/              # AI agents and tools
├── common/              # Shared utilities
├── scripts/             # Setup and utility scripts
├── docs/                # Documentation and API schema
└── tests/               # Test suite
```

### Key Components

- **Django REST Framework**: API framework with OpenAPI/Swagger
- **PostgreSQL**: Primary database for biblical data
- **Redis**: Caching and rate limiting
- **Docker**: Containerization and development environment
- **GitHub Actions**: CI/CD pipeline with automated testing

## API Endpoints

The API is organized into several main domains:

- `/api/v1/bible/` - Core biblical data (books, verses, themes)
- `/api/v1/ai/` - AI agents and tools
- `/api/v1/bible/audio/` - Audio generation and streaming
- `/api/v1/bible/resources/` - External study resources
- `/health` - Health check endpoint
- `/metrics` - Monitoring metrics

### Authentication

The API uses API key authentication. Include your key in the `Authorization` header:

```bash
curl -H "Authorization: Api-Key your-api-key-here" \
     http://localhost:8000/api/v1/bible/overview/
```

## Testing

We maintain comprehensive test coverage across all components:

```bash
# Run all tests
make test

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/api/           # API integration tests
pytest tests/performance/   # Performance tests

# Generate coverage report
pytest --cov --cov-report=html
open htmlcov/index.html
```

## Contributing

1. **Development Setup**: Follow the Quick Start guide
2. **Code Quality**: All code must pass `make ci` before submission
3. **Testing**: Write tests for new functionality
4. **Documentation**: Update API documentation when changing endpoints

### Code Standards

- **Python**: Follow PEP 8 with Black formatting
- **Imports**: Use ruff for import sorting
- **Documentation**: Include docstrings for all public methods
- **Git**: Use conventional commits (e.g., `feat:`, `fix:`, `docs:`)

## Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in production environment
- [ ] Use a secure `SECRET_KEY`
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Set up SSL/TLS certificates
- [ ] Configure production database
- [ ] Set up Redis for caching
- [ ] Configure static file serving
- [ ] Set up monitoring and logging

### Environment Variables

See `.env.example` for all available configuration options.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [API Documentation](http://localhost:8000/api/v1/schema/swagger-ui/)
- **Issues**: [GitHub Issues](https://github.com/bible-api/bible-api/issues)
- **Discussions**: [GitHub Discussions](https://github.com/bible-api/bible-api/discussions)

---

Made with ❤️ for the global church and biblical study community.