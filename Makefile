.PHONY: help install run-dev run-prod run-prod-direct run-test test lint format clean docker-build docker-up docker-down migrate create-project

help: ## Show this help message
	@echo 'Usage:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv pip install -e ".[dev]"

run-dev: ## Run development server
	python run.py dev

run-prod: ## Run production server (using run.py)
	python run.py prod

run-prod-direct: ## Run production server directly with uvicorn
	uvicorn main:app --host 0.0.0.0 --port 8080 --workers $(shell nproc)

run-test: ## Run test server
	python run.py test

test: ## Run tests
	pytest tests/ -v

lint: ## Run linting
	ruff check .

format: ## Format code
	ruff format .

clean: ## Clean up cache files
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".ruff_cache" -exec rm -r {} +
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

migrate: ## Run database migrations
	alembic upgrade head

migrate-create: ## Create new migration
	alembic revision --autogenerate -m "$(message)"

logs: ## View logs
	tail -f logs/app.log

venv: ## Create virtual environment
	uv venv

requirements: ## Generate requirements.txt
	uv pip freeze > requirements.txt

security-check: ## Run security checks
	bandit -r .
	safety check

create-project: ## Create a new project from this boilerplate
	python create_project.py 