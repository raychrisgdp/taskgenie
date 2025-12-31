# AGENTS.md (Repo Instructions for Agents)

This file is the repo-level “how to work here” guide for AI agents. Keep it short and
actionable. Put deep explanations and long examples in `docs/`.

If you are working in a subdirectory, check for additional `AGENTS.md` files; the most
specific one wins for that subtree.

## What This Repo Is

TaskGenie (`personal-todo`) is a CLI-first personal task manager with a FastAPI backend.

- CLI entrypoint: `tgenie` → `backend/cli/main.py`
- API app: `backend/main.py`
- Python: `>=3.11` (see `pyproject.toml`)

## Quickstart (Common Agent Commands)

- Install dev deps: `make dev`
- Format: `make format`
- Lint: `make lint`
- Typecheck: `make typecheck`
- Tests: `make test`
- Full check: `make check`

Prefer `uv run ...` when invoking project tooling directly (e.g., `uv run pytest`,
`uv run tgenie ...`).

## Coding Conventions (Enforced)

- Type hints required for all functions (mypy strict-ish; see `[tool.mypy]`)
- Docstrings: Google style (ruff pydocstyle)
- Line length: 100 (ruff)
- Quotes: double quotes (ruff formatter)
- Imports: standard → third-party → local; use `from __future__ import annotations`

## Configuration & Paths (Don’t Break These)

Settings are in `backend/config.py` (Pydantic Settings) with this precedence:

1. Environment variables
2. `.env` (repo root; dev convenience)
3. User TOML config (defaults under `~/.taskgenie/`)
4. Defaults in code

Key env vars:
- `TASKGENIE_DATA_DIR` (override app data directory)
- `TASKGENIE_CONFIG_FILE` (override config TOML path)
- `DATABASE_URL` (override DB URL)

Avoid creating directories at import time; create lazily in functions / settings helpers.

## Database & Migrations (SQLite + Async SQLAlchemy)

- DB/session: `backend/database.py`
- Models: `backend/models/`
- Alembic: `backend/migrations/`

Rules of thumb:
- Always enable SQLite foreign keys (`PRAGMA foreign_keys=ON`) on every session/connection.
- Don’t hardcode database paths; use settings-resolved paths/URLs.
- Review Alembic autogenerate output; SQLite downgrades/ALTER TABLE are limited.

Common migration commands:
- `uv run tgenie db upgrade head`
- `uv run tgenie db revision -m "..." --autogenerate`

## Tests

- Test runner: `pytest` (see `[tool.pytest.ini_options]`)
- Async tests: `pytest-asyncio` with `asyncio_mode = "auto"`
- Use `tmp_path` + `monkeypatch` to isolate `TASKGENIE_DATA_DIR`
- In tests, prefer `Settings(_env_file=None)` to avoid `.env` coupling

## Where To Read More

- Setup: `docs/SETUP.md`
- Dev quickstart: `docs/DEVELOPER_QUICKSTART.md`
- Testing guide: `docs/02-implementation/TESTING_GUIDE.md`
- Migrations guide: `docs/02-implementation/MIGRATIONS.md`
- Detailed patterns (legacy long-form): `docs/02-implementation/AGENT_GUIDE.md`
