.DEFAULT_GOAL := help

.PHONY: help dev hooks precommit lint format typecheck test test-cov docs-check check

help:
	@echo "Usage:"
	@echo "  make dev        Install dev dependencies (includes API for tests)"
	@echo "  make install-all Install all optional dependencies"
	@echo "  make hooks      Install pre-commit git hooks"
	@echo "  make precommit  Run pre-commit on all files"
	@echo "  make lint       Run ruff lint"
	@echo "  make format     Run ruff formatter"
	@echo "  make typecheck  Run mypy"
	@echo "  make test       Run pytest"
	@echo "  make test-cov   Run pytest with coverage"
	@echo "  make docs-check Validate docs links/naming"
	@echo "  make check      Run lint + typecheck + test"

dev:
	uv pip install -e ".[dev,pr002_api]"

install-all:
	uv pip install -e ".[all]"

hooks: dev
	uv run pre-commit install

precommit:
	uv run pre-commit run --all-files

lint:
	uv run ruff check backend/

format:
	uv run ruff format backend/

typecheck:
	uv run mypy backend/

test:
	uv run pytest -n 4

test-cov:
	uv run pytest -n 4 --cov=backend --cov-report=term-missing

docs-check:
	uv run python scripts/check_docs.py

check: lint typecheck test
