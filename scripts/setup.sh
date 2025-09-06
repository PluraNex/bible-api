#!/bin/bash

# Bible API Development Setup Script
# This script sets up the complete development environment

set -e  # Exit on any error

echo "🚀 Bible API Development Setup"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker and Docker Compose first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_status "Checking Docker daemon..."
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running. Please start Docker first."
    exit 1
fi

print_success "Docker is ready!"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating .env file from .env.example..."
    cp .env.example .env
    
    # Generate a random secret key
    SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
    sed -i "s/your-secret-key-change-in-production/$SECRET_KEY/" .env
    
    print_success ".env file created with random secret key"
else
    print_warning ".env file already exists, skipping..."
fi

# Build Docker containers
print_status "Building Docker containers..."
docker-compose build

# Start database and Redis services
print_status "Starting database and Redis services..."
docker-compose up -d db redis

# Wait for services to be healthy
print_status "Waiting for database to be ready..."
timeout 120 bash -c 'until docker-compose exec -T db pg_isready -U bible_user -d bible_api; do sleep 2; done' || {
    print_error "Database failed to start within 2 minutes"
    exit 1
}

print_status "Waiting for Redis to be ready..."
timeout 60 bash -c 'until docker-compose exec -T redis redis-cli ping | grep -q PONG; do sleep 2; done' || {
    print_error "Redis failed to start within 1 minute"
    exit 1
}

print_success "All services are ready!"

# Install Python dependencies locally (for IDE support)
if command -v pip &> /dev/null; then
    print_status "Installing Python dependencies locally..."
    pip install -r requirements-dev.txt
    print_success "Python dependencies installed"
else
    print_warning "pip not found. Skipping local Python dependencies installation."
    print_warning "You can still develop using Docker containers."
fi

# Install pre-commit hooks if pre-commit is available
if command -v pre-commit &> /dev/null; then
    print_status "Installing pre-commit hooks..."
    pre-commit install
    print_success "Pre-commit hooks installed"
fi

print_success "Setup completed successfully!"
echo ""
echo "Next steps:"
echo "  1. Run 'make up' to start all services"
echo "  2. Visit http://localhost:8000/health to check API health"
echo "  3. Run 'make test' to run the test suite"
echo "  4. Run 'make help' to see all available commands"
echo ""
echo "Happy coding! 🎉"