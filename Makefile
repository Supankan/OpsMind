.PHONY: help install lint format format-check typecheck test test-unit test-integration docker-up docker-down migrate run check

help: ## Show help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install project dependencies with uv
	uv sync

lint: ## Run linting checks with Ruff
	uv run ruff check .

format: ## Format codebase with Ruff
	uv run ruff format .

format-check: ## Check formatting with Ruff
	uv run ruff format --check .

typecheck: ## Run static type checking with Mypy
	uv run mypy opsmind apps tests

test: ## Run full test suite
	uv run pytest -v

test-unit: ## Run unit tests only
	uv run pytest -v tests/unit

test-integration: ## Run integration tests only (requires PostgreSQL)
	uv run pytest -v tests/integration

docker-up: ## Start local PostgreSQL container
	docker compose up -d postgres

docker-down: ## Stop local PostgreSQL container
	docker compose down

migrate: ## Apply database migrations with Alembic
	uv run alembic upgrade head

run: ## Start FastAPI application in development mode
	uv run uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

check: lint format-check typecheck test ## Run all linting, typing, and tests in sequence
