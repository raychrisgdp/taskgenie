# Review: `c/pr-001-db-config`

## Review Summary

- **Decision:** ✅ Ready (with the staged `backend/migrations/env.py` fix included)
- **Risk:** Medium (foundational config/DB/migrations wiring)
- **Scope:** PR-001 spec (`docs/02-implementation/pr-specs/PR-001-db-config.md`)
- **Baseline:** Branch tip `3dc7b98` + staged fixes in working tree

## What This PR Delivers

- Settings + precedence (`backend/config.py`)
  - env vars → `.env` → `~/.taskgenie/config.toml` → defaults
  - canonical app paths (DB, cache, logs, vector store)
- Async SQLite lifecycle (`backend/database.py`)
- Alembic migrations (`backend/migrations/` + initial revision)
- DB CLI (`backend/cli/db.py`): `upgrade`, `downgrade`, `revision`, `dump`, `restore`, `reset`
- Docs (`docs/SETUP.md`, `docs/02-implementation/MIGRATIONS.md`)
- CI + coverage (`.github/workflows/ci.yml`, `pytest-cov`, `[tool.coverage.*]`)

## Findings (Merged + Updated)

### Critical

- **[Critical][Fix] Alembic downgrade broken (stamping missing)** – After `upgrade`, the DB had an empty `alembic_version` table, making `downgrade --rev -1` fail with “Relative revision -1 didn't produce 1 migrations”.
  - **Fix (staged):** `backend/migrations/env.py` uses `async with connectable.begin()` so version stamping is committed.
  - **Validate:** `tgenie db upgrade` then `tgenie db downgrade --rev -1` succeeds; `tests/test_cli_db_extended.py::test_db_downgrade` passes.

### High

- **[High][Resolved] Unstaged `pyproject.toml` cleanup** – No longer applicable; `pyproject.toml` is clean in the current branch state.

### Medium

- **[Medium][Resolved] Downgrade test was too permissive** – `tests/test_cli_db_extended.py::test_db_downgrade` now asserts `upgrade` succeeds before `downgrade` and expects deterministic success (now enabled by the Alembic stamping fix).

- **[Medium][Resolved] `.cursor` commands were gitignored** – `.gitignore` now keeps `.cursor/commands/**` tracked while still ignoring other `.cursor/*` artifacts.

- **[Medium][Optional] TOML flattening special case** – `_load_toml_config()` still has a `notifications.schedule` → `notification_schedule` mapping. It’s acceptable for now, but consider a small mapping table if additional nested TOML keys are expected.

- **[Medium][Optional] SQLite URL parsing robustness** – `database_path` uses simple string splitting; current tests cover absolute/relative paths. Add `:memory:` and query-param cases if we expect them in real usage.

### Low

- **[Low][Resolved] Migration guide troubleshooting** – `docs/02-implementation/MIGRATIONS.md` includes troubleshooting content now.

## Validation

- Lint: `ruff check backend tests`
- Format: `ruff format --check backend tests`
- Tests: `pytest` → **51 passed**
- Coverage: `make test-cov` → **89%** total coverage (term-missing report)

## Notes

- `pyproject.toml` includes `[tool.hatch.build.targets.wheel] packages = ["backend"]` so built wheels include the `backend/` package.
- Tests are hermetic (they disable implicit `.env` + local `~/.taskgenie/config.toml` via fixtures); no committed `.env` is required for CI/tests.
