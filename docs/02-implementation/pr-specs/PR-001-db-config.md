# PR-001: Database & Configuration (Spec)

**Status:** Spec Only  
**Depends on:** -  
**Last Reviewed:** 2025-12-30

## Goal

Establish a reliable local-first foundation:
- configuration loading (env + config file)
- SQLite database initialization
- repeatable schema migrations
- safe backup/restore workflows

## User Value

- The app starts consistently on any machine.
- Schema changes are safe (no “delete DB and hope”).
- Users can backup/restore with one or two commands.

## Scope

### In

- Standardize config sources and precedence (e.g., `.env` → env vars → `~/.taskgenie/config.toml`).
- Introduce migrations (recommended: Alembic) for SQLite schema evolution.
- Add a simple DB CLI surface (either under `tgenie db ...` or a dedicated script):
  - upgrade/downgrade migrations
  - dump to `.sql`
  - restore from `.sql` (with clear warnings)
- Define canonical data paths (DB file, vector store, attachments cache).

### Out

- Building a full “admin console” for DB management.
- Cross-database support (Postgres/MySQL). SQLite-first only.

## Mini-Specs

- Config:
  - precedence and validation (env + `.env` + `~/.taskgenie/config.toml`).
- Paths:
  - canonical app data dir and subpaths (DB, cache, logs, vector store).
- Migrations:
  - Alembic initialized and runnable for SQLite.
  - wrapper CLI surface (`tgenie db upgrade|downgrade|revision`).
- Backup/restore:
  - dump to `.sql` and restore from `.sql` with explicit overwrite confirmation.
- Docs:
  - backup/restore + migration commands documented with examples.

## References

- `docs/01-design/DESIGN_DATA.md` (schema + backup/migration notes)
- `docs/01-design/DESIGN_BACKGROUND_JOBS.md` (job persistence patterns)
- `docs/01-design/DECISIONS.md` (TUI-first and migration approach)

## User Stories

- As a user, I can install/run the app and it creates its DB automatically.
- As a user, I can upgrade the app and migrate the DB safely.
- As a user, I can dump my data to `backup.sql` and restore it on a new machine.
- As a developer, I can reset my local DB quickly during iteration.

## Technical Design

### Config precedence

- Use **Pydantic Settings** for validation and environment management.
- Recommended precedence (highest wins):
  1. env vars
  2. `.env` file (dev convenience)
  3. config file (default: `~/.taskgenie/config.toml`)
  4. built-in defaults

### Data locations

- Define a canonical “app data dir” (configurable) for:
  - DB file
  - vector store
  - attachment cache
  - logs
- Default to `~/.taskgenie/` to match the rest of the design docs.
- (Optional) On Linux, consider XDG mappings later (config/data/state) if we want to be a better citizen.

### Migrations (Alembic)

- Add Alembic configuration in `backend/migrations/`.
- Ensure `env.py` is configured for SQLite (handling `PRAGMA foreign_keys=ON`).
- Support:
  - `tgenie db upgrade [--rev head]` (wraps `alembic upgrade head`)
  - `tgenie db downgrade --rev <rev>|-1`
  - `tgenie db revision -m "..." --autogenerate`

### Backup/restore

- Support the standard SQLite `.dump` workflow.
- If wrapped in CLI, require explicit confirmation on restore.

### DB CLI surface

- Provide (or plan) these commands:
  - `tgenie db dump --out backup.sql`
  - `tgenie db restore --in backup.sql` (confirm overwrite)
  - `tgenie db reset --yes` (dev-only convenience)

## Acceptance Criteria

- [ ] Fresh install creates/runs with a clean SQLite DB (no manual steps beyond config).
- [ ] Migrations can be created and applied via a single command.
- [ ] Backup to `.sql` and restore from `.sql` are documented and verified.

## Test Plan

### Automated

- Unit: config precedence and validation.
- Integration: DB initialization creates expected tables; migrations apply cleanly.

### Manual

1. **Fresh start**
   - Delete local DB file.
   - Run `tgenie db upgrade` (or equivalent).
   - Start the API; hit `/health`; verify app boot completes.
2. **Backup + restore**
   - Create at least 1 task.
   - Dump DB to `backup.sql`.
   - Restore into a new DB file.
   - Start API pointing at the restored DB and verify the task exists.
3. **Migration forward/back**
   - Create a migration (dummy column or table).
   - Upgrade to head; verify schema changes.
   - Downgrade one step; verify schema reverts (where feasible in SQLite).

## Notes / Risks / Open Questions

- SQLite downgrade support can be limited depending on migration operations; keep early migrations simple.
- If `tgenie` CLI wiring isn’t available yet, these commands can be exposed via `uv run ...` as an interim step, but the end state should be `tgenie db ...`.
