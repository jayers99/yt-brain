.PHONY: help install dev test lint typecheck run clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

install: ## Install core dependencies
	uv sync

dev: ## Install all dependencies including dev and optional AI extras
	uv sync --dev --extra ai

test: ## Run tests
	uv run pytest -v

lint: ## Lint with ruff
	uv run ruff check src/ tests/

typecheck: ## Type-check with mypy
	uv run mypy

run: ## Launch the web dashboard
	uv run yt-brain dashboard

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
