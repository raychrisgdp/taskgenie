# PR-001: Database & Configuration (Spec)

**Status:** Spec Only  
**Depends on:** -  
**Last Reviewed:** 2025-12-30

## Goal

Establish the local-first foundation: config loading, SQLite initialization,
migrations, and backup/restore workflows.

## User Value

- The app starts consistently on any machine.
- Schema changes are safe and repeatable.
- Users can back up and restore data with clear commands.

## References

- `docs/01-design/DESIGN_DATA.md`
- `docs/01-design/DESIGN_BACKGROUND_JOBS.md`
- `docs/01-design/DECISIONS.md`

## Scope

### In

- Configuration sources and precedence (env vars, `.env`, user config, defaults).
- Canonical app data directory and subpaths (DB, cache, vector store, attachments, logs).
- Alembic migrations for SQLite and CLI wrappers for upgrade/downgrade/revision.
- Backup and restore commands with explicit confirmation on restore.
- FastAPI startup initializes the database and runs migrations when needed.

### Out

- Admin UI for DB management.
- Non-SQLite databases.

## Mini-Specs

- Implement Pydantic Settings in `backend/config.py` with defined precedence.
- Add path helpers for data directory resolution without creating directories at import time.
- Initialize Alembic in `backend/migrations/` with SQLite-safe config and FK enforcement.
- Provide `tgenie db` commands: upgrade, downgrade, revision, dump, restore (reset optional).
- Document backup/restore and migration usage in `docs/`.

## User Stories

- As a user, I can install/run the app and it creates its DB automatically.
- As a user, I can upgrade the app and migrate the DB safely.
- As a user, I can dump my data to `backup.sql` and restore it on a new machine.
- As a developer, I can reset my local DB quickly during iteration.

## UX Notes (if applicable)

- Destructive actions (restore/reset) require explicit confirmation.

## Technical Design

### Architecture

- Use Pydantic Settings with cached `get_settings()` and explicit precedence:
  env vars > `.env` > `~/.taskgenie/config.toml` > defaults.
- Provide a single resolver for app data paths (configurable via `TASKGENIE_DATA_DIR`).
- FastAPI lifespan calls `init_db_async()` to avoid blocking the event loop.

### Data Model / Migrations

- Initialize Alembic under `backend/migrations/`.
- Ensure SQLite foreign keys are enabled on every connection.
- Migrations use `sqlite://` for Alembic even when runtime uses `sqlite+aiosqlite://`.

### API Contract

- CLI surface under `tgenie db`:
  `upgrade`, `downgrade`, `revision`, `dump`, `restore` (and optional `reset`).

### Background Jobs

- N/A.

### Security / Privacy

- Backup/restore commands do not log SQL contents.
- Restore and reset require confirmation before overwrite.

### Error Handling

- Missing optional config files are non-fatal with clear defaults.
- Migration and backup/restore failures surface actionable CLI errors.

## Acceptance Criteria

### AC1: Config Precedence and Paths

**Success Criteria:**
- [ ] Env vars override `.env`, which overrides user config, which overrides defaults.
- [ ] App data directories resolve to configurable, stable paths.
- [ ] No directories are created at import time.

### AC2: Migrations and DB Initialization

**Success Criteria:**
- [ ] Alembic is configured for SQLite with FK enforcement.
- [ ] `tgenie db upgrade head` creates the DB and applies migrations.
- [ ] `tgenie db revision --autogenerate` produces a migration file.

### AC3: Backup and Restore

**Success Criteria:**
- [ ] `tgenie db dump --out backup.sql` writes a valid SQL dump.
- [ ] `tgenie db restore --in backup.sql` restores data after confirmation.

### AC4: FastAPI Startup Integration

**Success Criteria:**
- [ ] FastAPI startup initializes the DB and applies pending migrations.
- [ ] `/health` returns OK after startup.

## Test Plan

### Automated

- Unit: settings precedence and path resolution.
- Integration: Alembic upgrade/downgrade paths against temp DB.
- CLI: `tgenie db` commands (upgrade, dump, restore).

### Manual

- Run `tgenie db upgrade head` on a clean machine; confirm DB created.
- Create data, dump/restore, and confirm data persists.
- Start API and verify `/health` returns OK.

## Notes / Risks / Open Questions

- SQLite downgrade support is limited; keep early migrations simple.
- Structured logging and telemetry are handled in PR-016.
