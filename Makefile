.DEFAULT_GOAL := help

.PHONY: help dev hooks precommit lint format typecheck test test-cov docs-check check

help:
	@echo "Usage:"
	@echo "  make dev        Install dev dependencies (includes API for tests)"
	@echo "  make install-all Install all optional dependencies"
	@echo "  make lock       Update uv.lock file after modifying pyproject.toml dependencies"
	@echo "  make hooks      Install pre-commit git hooks"
	@echo "  make precommit  Run docs check + pre-commit on all files"
	@echo "  make lint       Run ruff lint"
	@echo "  make format     Run ruff formatter"
	@echo "  make typecheck  Run mypy"
	@echo "  make test       Run pytest"
	@echo "  make test-cov   Run precommit + pytest with coverage (matches CI)"
	@echo "  make docs-check Validate docs links/naming"
	@echo "  make check      Run lint + typecheck + test"

dev:
	@if [ -f uv.lock ]; then \
		uv sync --extra dev; \
	else \
		uv venv && uv pip install --python .venv/bin/python -e ".[dev]"; \
	fi

install-all:
	@if [ -f uv.lock ]; then \
		uv sync --all-extras; \
	else \
		uv venv && uv pip install --python .venv/bin/python -e ".[all]"; \
	fi

# Update lock file when dependencies change (run this after modifying pyproject.toml)
lock:
	uv lock

hooks: dev
	uv run pre-commit install

precommit: docs-check
	uv run pre-commit run --all-files

lint:
	uv run ruff check backend tests
	uv run ruff format --check backend tests

format:
	uv run ruff format backend/

typecheck:
	uv run mypy backend/

test:
	uv run pytest -n 4

test-cov: precommit
	uv run pytest -n 4 --cov=backend --cov-report=term-missing

docs-check:
	uv run python scripts/check_docs.py

check: lint typecheck test
