# PR-017: DB Config Follow-ups (Spec)

**Status:** Spec Only  
**Depends on:** PR-001  
**Last Reviewed:** 2025-12-30

## Goal

Close gaps discovered after PR-001 by tightening directory creation, restore safety,
SQLite FK enforcement, and docs alignment.

## User Value

- App data directories are consistent and complete across machines.
- Restore confirmations prevent accidental overwrites while supporting automation.
- SQLite foreign keys are enforced for all connections.
- Troubleshooting docs reflect current behavior.

## References

- `docs/02-implementation/pr-specs/PR-001-db-config.md`
- `docs/01-design/DESIGN_DATA.md`
- `docs/02-implementation/MIGRATIONS.md`

## Docs Links

- `README.md`
- `docs/INDEX.md`
- `docs/USER_GUIDE.md`
- `docs/02-implementation/pr-specs/PR-001-db-config.md`
- `docs/01-design/DESIGN_DATA.md`
- `docs/02-implementation/MIGRATIONS.md`

## Scope

### In

- Ensure `ensure_app_dirs()` creates the vector store directory (`data/chroma`).
- Keep confirmation when `tgenie db restore` would overwrite an existing DB,
  and add a `--yes` flag to skip the prompt for automation.
- Enforce SQLite foreign keys on every SQLAlchemy connection (not just sessions).
- Update `docs/TROUBLESHOOTING.md` to remove PR-001 "planned" wording and align
  default DB path guidance with current settings.

### Out

- Non-SQLite databases or new backup/retention policies.
- Changes to migration scripts or schema.

## Mini-Specs

- Add vector store directory creation to settings dir bootstrap.
- Add a restore confirmation bypass flag for overwrite prompts.
- Add engine-level SQLite FK enforcement hook.
- Align troubleshooting docs with actual DB/config behavior.

## User Stories

- As a user, I see my vector store directory created alongside the DB.
- As a user, I must explicitly confirm a restore before it overwrites data.
- As a developer, I can rely on SQLite foreign keys for any connection.

## UX Notes (if applicable)

- Restore prompts should be explicit about the target DB path.
- The `--yes` flag should be consistent with `db reset`.

## Technical Design

### Architecture

- In `Settings.ensure_app_dirs()`, create `data/chroma` using the same root as
  `database_path`.
- For SQLite, attach a SQLAlchemy engine `connect` event that runs
  `PRAGMA foreign_keys=ON` on every new DBAPI connection (sync + async engines).
- Keep `get_db()` PRAGMA as a secondary guard.

### Data Model / Migrations

- No schema changes.

### API Contract

- `tgenie db restore --in <file>` prompts when the target DB exists, unless
  `--yes` is provided.

### Background Jobs

- N/A.

### Security / Privacy

- Do not log SQL contents during restore.

### Error Handling

- Restore failures should remain actionable and exit non-zero.

## Acceptance Criteria

### AC1: App Dir Completeness

**Success Criteria:**
- [ ] `ensure_app_dirs()` creates `data/chroma` under the resolved app data dir.
- [ ] No directories are created at import time.

### AC2: Restore Confirmation

**Success Criteria:**
- [ ] `tgenie db restore` prompts for confirmation only when the target DB exists.
- [ ] `--yes` skips the prompt when an existing DB would be overwritten.

### AC3: SQLite FK Enforcement

**Success Criteria:**
- [ ] SQLite `PRAGMA foreign_keys=ON` is executed for every engine connection.

### AC4: Docs Alignment

**Success Criteria:**
- [ ] `docs/TROUBLESHOOTING.md` reflects current DB wiring and default paths.

## Test Plan

### Automated

- Unit: `ensure_app_dirs()` creates `data/chroma`.
- CLI: `tgenie db restore` prompts only when the DB exists; `--yes` skips.
- Integration: engine-level FK PRAGMA is applied for a fresh connection.

### Manual

- Run `tgenie db restore --in backup.sql` on an existing DB and confirm prompt.
- Run `tgenie db restore --in backup.sql` on a missing DB and confirm no prompt.
- Start the API and confirm `~/.taskgenie/data/chroma` is created.

## Notes / Risks / Open Questions

- N/A.
