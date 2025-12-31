.DEFAULT_GOAL := help

.PHONY: help dev hooks precommit lint format typecheck test test-cov docs-check check

help:
	@echo "Usage:"
	@echo "  make dev        Install dev dependencies (PR-001 core)"
	@echo "  make pr002      Install PR-002 API dependencies"
	@echo "  make pr003      Install PR-003 LLM dependencies"
	@echo "  make pr005      Install PR-005 RAG dependencies"
	@echo "  make pr006      Install PR-006 Gmail dependencies"
	@echo "  make pr007      Install PR-007 GitHub dependencies"
	@echo "  make pr011      Install PR-011 notifications dependencies"
	@echo "  make install-all Install all dependencies"
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
	uv pip install -e ".[dev]"

pr002: dev
	uv pip install -e ".[pr002_api]"

pr003: dev
	uv pip install -e ".[pr003_llm]"

pr005: dev
	uv pip install -e ".[pr005_rag]"

pr006: dev
	uv pip install -e ".[pr006_gmail]"

pr007: dev
	uv pip install -e ".[pr007_github]"

pr011: dev
	uv pip install -e ".[pr011_notifications]"

install-all:
	uv pip install -e ".[all]"

hooks: dev
	pre-commit install

precommit:
	pre-commit run --all-files

lint:
	ruff check backend/

format:
	ruff format backend/

typecheck:
	mypy backend/

test:
	pytest

test-cov:
	pytest --cov=backend --cov-report=term-missing

docs-check:
	python scripts/check_docs.py

check: lint typecheck test
