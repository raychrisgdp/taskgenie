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
- **Precommit**: `make precommit` (run before every commit)

Prefer `uv run ...` when invoking project tooling directly (e.g., `uv run pytest`,
`uv run tgenie ...`).

## Coding Conventions (Enforced)

**📚 See `docs/02-implementation/AGENT_GUIDE.md` for detailed patterns, examples, and common pitfalls.**

- Type hints required for all functions (mypy strict-ish; see `[tool.mypy]`)
- Docstrings: Google style (ruff pydocstyle)
- Line length: 100 (ruff)
- Quotes: double quotes (ruff formatter)
- Imports: standard → third-party → local; use `from __future__ import annotations`
- **Mutable defaults**: Use `default_factory` for lists/dicts (e.g., `Field(default_factory=lambda: [])`)
- **Type ignores**: Use specific error codes (e.g., `# type: ignore[call-overload]`) when needed

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

**📚 See `docs/02-implementation/AGENT_GUIDE.md` for database patterns, migration examples, and SQLite-specific considerations.**

- DB/session: `backend/database.py`
- Models: `backend/models/`
- Alembic: `backend/migrations/`

Rules of thumb:
- Always enable SQLite foreign keys (`PRAGMA foreign_keys=ON`) on every session/connection.
- Don't hardcode database paths; use settings-resolved paths/URLs.
- Review Alembic autogenerate output; SQLite downgrades/ALTER TABLE are limited.
- **FastAPI lifespan**: Use `init_db_async()` (not `init_db()`) to avoid blocking the event loop.
- **Query parameters**: `database_path` automatically strips query parameters (e.g., `?mode=ro`) from SQLite URLs.
- **Migration URLs**: CLI and startup migrations convert `sqlite+aiosqlite://` to `sqlite://` to avoid asyncio conflicts (see `docs/02-implementation/MIGRATIONS.md`).

Common migration commands:
- `uv run tgenie db upgrade head`
- `uv run tgenie db revision -m "..." --autogenerate`

## Tests

**📚 See `docs/02-implementation/TESTING_GUIDE.md` for comprehensive testing patterns and examples.**

- Test runner: `pytest` (see `[tool.pytest.ini_options]`)
- Async tests: `pytest-asyncio` with `asyncio_mode = "auto"`
- Use `tmp_path` + `monkeypatch` to isolate `TASKGENIE_DATA_DIR`
- In tests, prefer `Settings(_env_file=None)` to avoid `.env` coupling
- **Test organization**: Avoid duplicate tests; fix incomplete test functions
- **Intentional imports**: Use `# noqa: PLC0415` for imports inside functions (common in tests)
- **Unused variables**: Prefix with `_` (e.g., `_ = subprocess.run(...)`) if intentionally unused

## Code Quality & Precommit

**Always run `make precommit` before committing.** It checks:
- Formatting (ruff format)
- Linting (ruff check)
- Type checking (mypy)
- Test syntax
- Import organization

**Common fixes:**
- Duplicate tests → Remove duplicates
- Incomplete test functions → Complete function definitions
- Unused variables → Prefix with `_` or remove
- Type errors → Add `# type: ignore[error-code]` with specific code
- Import warnings → Add `# noqa: PLC0415` for intentional imports inside functions

## Where To Read More

**Essential References:**
- **Testing patterns & examples**: `docs/02-implementation/TESTING_GUIDE.md` - Comprehensive testing guide with unit/integration/E2E patterns
- **Code patterns & best practices**: `docs/02-implementation/AGENT_GUIDE.md` - Detailed development patterns, common pitfalls, and learnings

**Additional Resources:**
- Setup: `docs/SETUP.md`
- Dev quickstart: `docs/DEVELOPER_QUICKSTART.md`
- Migrations guide: `docs/02-implementation/MIGRATIONS.md`
