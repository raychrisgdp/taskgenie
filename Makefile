.DEFAULT_GOAL := help

.PHONY: help dev hooks precommit lint format typecheck test check

help:
	@echo "Usage:"
	@echo "  make dev        Install dev dependencies"
	@echo "  make hooks      Install pre-commit git hooks"
	@echo "  make precommit  Run pre-commit on all files"
	@echo "  make lint       Run ruff lint"
	@echo "  make format     Run ruff formatter"
	@echo "  make typecheck  Run mypy"
	@echo "  make test       Run pytest"
	@echo "  make check      Run lint + typecheck + test"

dev:
	uv pip install -e ".[dev]"

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

check: lint typecheck test
