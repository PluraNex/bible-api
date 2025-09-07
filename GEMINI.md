# Gemini Project Context: bible-api

## Project Overview

This project is a comprehensive RESTful Bible API built with the Django REST Framework. It provides access to biblical data, including books, verses, themes, and cross-references. A key feature is its AI integration, which offers agent-based tools for biblical analysis. The project is containerized using Docker, ensuring a consistent development and deployment environment.

### Key Technologies

*   **Backend:** Django, Django REST Framework
*   **Database:** PostgreSQL
*   **Caching:** Redis
*   **Containerization:** Docker, Docker Compose
*   **Testing:** Pytest
*   **Linting & Formatting:** Ruff, Black

### Architecture

The project follows a modular architecture, with the core logic organized into Django apps:

*   `bible`: The main application containing the core models and business logic.
*   `bible.ai`: Handles the AI agent and tool integration.
*   `bible.apps.auth`: Manages API key authentication.
*   `config`: Contains the Django project settings and main URL configuration.

## Building and Running

The project uses a `Makefile` to simplify common development tasks.

### Initial Setup

1.  **Clone the repository.**
2.  **Run the setup script:**
    ```bash
    make dev-setup
    ```
    This command (defined in the `Makefile`) likely sets up the environment, including creating a `.env` file and building the Docker containers.

### Running the Application

*   **Start all services:**
    ```bash
    make up
    ```
*   **Stop all services:**
    ```bash
    make down
    ```
*   **View logs:**
    ```bash
    make logs
    ```

### Running Tests

*   **Run all tests with coverage:**
    ```bash
    make test
    ```
*   **Run tests without coverage:**
    ```bash
    make test-fast
    ```
*   **Run all CI checks locally:**
    ```bash
    make ci
    ```

## Development Conventions

### Code Style

*   **Formatting:** The project uses `black` for code formatting and `ruff` for linting and import sorting.
*   **Linting:** Run `make lint` to check for code quality issues.
*   **Formatting:** Run `make format` to automatically format the code.

### Testing

*   Tests are written using `pytest` and are located in the `tests/` directory.
*   The project aims for high test coverage. Run `make coverage` to generate a coverage report.

### Pre-commit Hooks

The project uses pre-commit hooks to enforce code quality standards before committing.

*   **Install hooks:**
    ```bash
    pre-commit install
    ```
*   **Run hooks on all files:**
    ```bash
    pre-commit run --all-files
    ```

### API Documentation

The API is documented using the OpenAPI standard (Swagger).

*   **View API documentation:** [http://localhost:8000/api/v1/docs/](http://localhost:8000/api/v1/docs/)
*   **Generate OpenAPI schema:**
    ```bash
    make schema
    ```
