.PHONY: help install dev build test clean docker up down lint format check docs

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)HireMind Development Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install all dependencies (backend + frontend)
	@echo "$(BLUE)Installing Python dependencies...$(NC)"
	python -m venv .venv
	. .venv/Scripts/activate && pip install -r backend/requirements.txt
	@echo "$(GREEN)✓ Backend dependencies installed$(NC)"
	@echo ""
	@echo "$(BLUE)Installing Node dependencies...$(NC)"
	cd frontend && npm install
	@echo "$(GREEN)✓ Frontend dependencies installed$(NC)"

dev: ## Run both backend and frontend in development mode
	@echo "$(BLUE)Starting development servers...$(NC)"
	@echo "Backend: http://127.0.0.1:8000"
	@echo "Frontend: http://localhost:5173"
	@echo "API Docs: http://127.0.0.1:8000/docs"
	@echo ""
	@echo "$(YELLOW)Press Ctrl+C in each terminal to stop$(NC)"
	@echo ""
	makefiber backend frontend

backend: ## Run backend development server
	@echo "$(BLUE)Starting FastAPI backend...$(NC)"
	. .venv/Scripts/activate && uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

frontend: ## Run frontend development server
	@echo "$(BLUE)Starting React frontend...$(NC)"
	cd frontend && npm run dev

build: build-backend build-frontend ## Build both backend and frontend for production

build-backend: ## Build backend
	@echo "$(BLUE)Building backend...$(NC)"
	. .venv/Scripts/activate && python -c "from backend.app.main import app; print('✓ Backend build successful')"

build-frontend: ## Build frontend
	@echo "$(BLUE)Building frontend...$(NC)"
	cd frontend && npm run build
	@echo "$(GREEN)✓ Frontend build successful$(NC)"

test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests
	@echo "$(BLUE)Running backend tests...$(NC)"
	. .venv/Scripts/activate && pytest backend/tests/ -v --cov=backend.app --cov-report=html
	@echo "$(GREEN)✓ Backend tests completed$(NC)"

test-frontend: ## Run frontend tests
	@echo "$(BLUE)Running frontend tests...$(NC)"
	cd frontend && npm run test -- --coverage
	@echo "$(GREEN)✓ Frontend tests completed$(NC)"

lint: lint-backend lint-frontend ## Run linters

lint-backend: ## Lint Python code
	@echo "$(BLUE)Linting Python code...$(NC)"
	. .venv/Scripts/activate && flake8 backend/app --max-line-length=120
	@echo "$(GREEN)✓ Python linting passed$(NC)"

lint-frontend: ## Lint JavaScript code
	@echo "$(BLUE)Linting JavaScript code...$(NC)"
	cd frontend && npm run lint
	@echo "$(GREEN)✓ JavaScript linting passed$(NC)"

format: format-backend format-frontend ## Format all code

format-backend: ## Format Python code
	@echo "$(BLUE)Formatting Python code...$(NC)"
	. .venv/Scripts/activate && black backend/
	@echo "$(GREEN)✓ Python code formatted$(NC)"

format-frontend: ## Format JavaScript code
	@echo "$(BLUE)Formatting JavaScript code...$(NC)"
	cd frontend && npm run format
	@echo "$(GREEN)✓ JavaScript code formatted$(NC)"

check: lint test ## Run all checks (lint + test)
	@echo "$(GREEN)✓ All checks passed!$(NC)"

clean: ## Clean up build artifacts, caches, and logs
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete
	rm -rf backend/.coverage backend/htmlcov backend/dist backend/build
	rm -rf frontend/dist frontend/build frontend/.next
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

docker-build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker build -f Dockerfile.backend -t hiremind-api:latest .
	docker build -f Dockerfile.frontend -t hiremind-frontend:latest .
	@echo "$(GREEN)✓ Docker images built$(NC)"

docker-up: ## Start Docker containers
	@echo "$(BLUE)Starting Docker containers...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Containers started$(NC)"
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:80"
	@echo "Database: localhost:5432"

docker-down: ## Stop Docker containers
	@echo "$(BLUE)Stopping containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Containers stopped$(NC)"

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-shell-backend: ## Open shell in backend container
	docker-compose exec backend /bin/bash

docker-shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend /bin/sh

db-init: ## Initialize database
	@echo "$(BLUE)Initializing database...$(NC)"
	. .venv/Scripts/activate && python database/init_db.py
	@echo "$(GREEN)✓ Database initialized$(NC)"

db-migrate: ## Run migrations
	@echo "$(BLUE)Running migrations...$(NC)"
	. .venv/Scripts/activate && python database/migrate.py
	@echo "$(GREEN)✓ Migrations complete$(NC)"

docs: ## Generate documentation
	@echo "$(BLUE)Generating docs...$(NC)"
	@echo "$(YELLOW)Docs locations:$(NC)"
	@echo "  - Main: README.md"
	@echo "  - Backend API: http://127.0.0.1:8000/docs (when running)"
	@echo "  - Contributing: CONTRIBUTING.md"
	@echo "  - Deployment: DEPLOYMENT.md"

security: ## Check for security vulnerabilities
	@echo "$(BLUE)Running security checks...$(NC)"
	. .venv/Scripts/activate && pip-audit --desc
	@echo ""
	cd frontend && npm audit
	@echo "$(GREEN)✓ Security check complete$(NC)"

requirements: ## Update requirements files
	@echo "$(BLUE)Updating requirements...$(NC)"
	. .venv/Scripts/activate && pip freeze > backend/requirements.txt
	cd frontend && npm update && npm audit fix
	@echo "$(GREEN)✓ Requirements updated$(NC)"

version: ## Show project version and info
	@echo "$(BLUE)HireMind Project Info$(NC)"
	@echo ""
	@grep '"version"' frontend/package.json | head -1
	@grep 'version' README.md | head -1
	@echo ""
	@echo "Python: $$(python --version 2>&1)"
	@echo "Node: $$(node --version 2>&1)"
	@echo "npm: $$(npm --version 2>&1)"

setup-pre-commit: ## Setup pre-commit hooks
	@echo "$(BLUE)Setting up pre-commit hooks...$(NC)"
	pip install pre-commit
	pre-commit install
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"

log-level: ## Set log level (DEBUG/INFO/WARNING/ERROR)
	@read -p "Enter log level (DEBUG/INFO/WARNING/ERROR): " level; \
	echo "LOG_LEVEL=$$level" >> .env

# Help for all commands
about: ## Show project information
	@echo "$(BLUE)HireMind - AI-Powered Recruitment Platform$(NC)"
	@echo ""
	@echo "An intelligent recruitment system with:"
	@echo "  • CV analysis and parsing"
	@echo "  • Semantic skill matching"
	@echo "  • AI-powered interviews"
	@echo "  • Candidate & company portals"
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  make install    # Install dependencies"
	@echo "  make dev        # Start development servers"
	@echo "  make check      # Run tests and linting"
	@echo ""
	@echo "$(YELLOW)Docker:$(NC)"
	@echo "  make docker-up  # Start containers"
	@echo "  make docker-down # Stop containers"
	@echo ""
	@echo "See 'make help' for all commands"
