# OpenGov-Pension Development Makefile
# Provides common development, testing, and deployment tasks

.PHONY: help install install-dev install-test clean test test-unit test-integration test-e2e test-coverage lint format type-check security security-scan pre-commit build build-dev docs docs-serve docker-build docker-run docker-compose-up docker-compose-down ci ci-local release help

# Default target
help: ## Show this help message
	@echo "OpenGov-Pension Development Tasks"
	@echo "================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Environment Setup
install: ## Install production dependencies using uv
	uv sync --only-group default

install-dev: ## Install development dependencies using uv
	uv sync

install-test: ## Install test dependencies using uv
	uv sync --group test

# Cleanup
clean: ## Clean up build artifacts and cache
	uv run tox -e clean
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf .coverage*
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

clean-all: clean ## Clean everything including virtual environment
	rm -rf .venv/

# Testing
test: ## Run all tests
	uv run pytest tests/ -v

test-unit: ## Run unit tests only
	uv run pytest tests/unit/ -v -m unit

test-integration: ## Run integration tests only
	uv run pytest tests/integration/ -v -m integration

test-e2e: ## Run end-to-end tests only
	uv run pytest tests/e2e/ -v -m e2e

test-coverage: ## Run tests with coverage report
	uv run pytest tests/ --cov=opengovpension --cov-report=html --cov-report=term-missing --cov-fail-under=85

test-tox: ## Run tests using tox
	uv run tox -e py311

test-tox-all: ## Run tests on all Python versions using tox
	uv run tox

# Code Quality
lint: ## Run linters (ruff, black, isort)
	uv run tox -e lint

format: ## Format code using black and isort
	uv run tox -e format

type-check: ## Run type checking with mypy
	uv run tox -e type

security: ## Run security checks (bandit, safety, pip-audit)
	uv run tox -e security

security-scan: ## Run comprehensive security scan with bandit and trivy
	@echo "Running Bandit security scan..."
	uv run bandit -r src/ -f json -o bandit-report.json
	@echo "Running Trivy filesystem scan..."
	trivy fs . --format json --output trivy-report.json
	@echo "Security scan complete. Reports: bandit-report.json, trivy-report.json"

# Pre-commit
pre-commit: ## Run pre-commit hooks on all files
	uv run pre-commit run --all-files

pre-commit-install: ## Install pre-commit hooks
	uv run pre-commit install --install-hooks

# Building
build: ## Build production artifacts
	uv run hatch build

build-dev: ## Build development artifacts
	uv run hatch build --clean

# Documentation
docs: ## Build documentation
	uv run tox -e docs

docs-serve: ## Serve documentation locally
	uv run mkdocs serve

# Docker
docker-build: ## Build Docker image
	docker build --target runtime -t opengovpension:latest .

docker-run: ## Run Docker container
	docker run --rm -p 8000:8000 opengovpension:latest

docker-compose-up: ## Start services with docker-compose
	docker compose up -d

docker-compose-down: ## Stop services with docker-compose
	docker compose down

# CI/CD
ci: ## Run full CI pipeline locally
	$(MAKE) clean
	$(MAKE) install-dev
	$(MAKE) lint
	$(MAKE) type-check
	$(MAKE) security
	$(MAKE) test-coverage
	$(MAKE) build

ci-local: ## Run CI pipeline with docker-compose
	$(MAKE) docker-compose-up
	@echo "Waiting for services to be ready..."
	@sleep 10
	$(MAKE) test-integration
	$(MAKE) docker-compose-down

# Release
release-patch: ## Release patch version
	uv run hatch version patch
	uv run hatch build
	uv run hatch publish

release-minor: ## Release minor version
	uv run hatch version minor
	uv run hatch build
	uv run hatch publish

release-major: ## Release major version
	uv run hatch version major
	uv run hatch build
	uv run hatch publish

# Development
dev: ## Start development environment
	$(MAKE) install-dev
	@echo "Starting development server..."
	uv run uvicorn opengovpension.web.app:app --reload --host 0.0.0.0 --port 8000

dev-cli: ## Start CLI development session
	$(MAKE) install-dev
	@echo "CLI development session ready"
	uv run opengov-pension --help

# Database
db-init: ## Initialize database
	uv run opengov-pension db init

db-seed: ## Seed database with sample data
	uv run opengov-pension db seed

db-reset: ## Reset database (drop and recreate)
	uv run opengov-pension db init --drop-existing
	$(MAKE) db-seed

# Monitoring
health: ## Check application health
	curl -f http://localhost:8000/health || echo "Application not running"

metrics: ## View application metrics
	curl -f http://localhost:8000/metrics || echo "Application not running"

logs: ## View application logs
	@echo "Application logs:"
	tail -f logs/app.log 2>/dev/null || echo "No log file found"

# Performance
load-test: ## Run load tests
	uv run locust -f tests/performance/locustfile.py --headless -u 100 -r 10 -t 30s

benchmark: ## Run benchmarks
	uv run pytest tests/benchmarks/ -v

# Dependencies
deps-update: ## Update dependencies
	uv lock --upgrade

deps-check: ## Check for dependency vulnerabilities
	uv run safety check
	uv run pip-audit

# Environment Info
info: ## Show environment information
	@echo "=== OpenGov-Pension Environment Info ==="
	@echo "Python version: $$(python --version)"
	@echo "uv version: $$(uv --version)"
	@echo "hatch version: $$(uv run hatch --version)"
	@echo "ruff version: $$(uv run ruff --version)"
	@echo "black version: $$(uv run black --version)"
	@echo "mypy version: $$(uv run mypy --version)"
	@echo "bandit version: $$(uv run bandit --version)"
	@echo "trivy version: $$(trivy --version)"
	@echo "======================================="

# Quick Start
quickstart: ## Quick start for new developers
	$(MAKE) install-dev
	$(MAKE) db-init
	$(MAKE) db-seed
	@echo "Quick start complete! Run 'make dev' to start the development server"

# Validation
validate: ## Validate the entire setup
	$(MAKE) ci
	@echo "All validations passed!"

# Default command
.DEFAULT_GOAL := help
