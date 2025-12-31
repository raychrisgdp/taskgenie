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

### AC1: Fresh Install Creates Database Automatically ✅

**Success Criteria:**
- [ ] No database file exists initially
- [ ] Running `tgenie db upgrade head` creates database at `~/.taskgenie/data/taskgenie.db` (or configured path)
- [ ] All required tables are created: `tasks`, `attachments`, `notifications`, `chat_history`, `config`, `alembic_version`
- [ ] FastAPI startup automatically runs migrations if DB doesn't exist
- [ ] `/health` endpoint returns `200 OK` after startup

**How to Test:**

**Automated:**
```python
def test_fresh_install_creates_db(tmp_path, monkeypatch):
    """Test that fresh install creates DB and tables."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")

    # Verify DB doesn't exist
    assert not db_path.exists()

    # Run upgrade
    runner = CliRunner()
    result = runner.invoke(db_app, ["upgrade", "head"])
    assert result.exit_code == 0

    # Verify DB created with all tables
    assert db_path.exists()
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert "tasks" in tables
    assert "attachments" in tables
    assert "notifications" in tables
    assert "alembic_version" in tables
    conn.close()
```

**Manual:**
```bash
# 1. Remove existing DB (if any)
rm ~/.taskgenie/data/taskgenie.db

# 2. Run upgrade
uv run tgenie db upgrade head

# 3. Verify DB created
ls -la ~/.taskgenie/data/taskgenie.db

# 4. Start API and verify health
uv run python -m backend.main &
sleep 2
curl http://localhost:8080/health
# Expected: {"status": "ok", "version": "0.1.0"}
```

---

### AC2: Migrations Can Be Created and Applied ✅

**Success Criteria:**
- [ ] `tgenie db revision -m "..." --autogenerate` creates new migration file
- [ ] `tgenie db upgrade head` applies all pending migrations
- [ ] `tgenie db downgrade -1` reverts last migration (where feasible)
- [ ] `alembic_version` table tracks current revision
- [ ] Multiple sequential migrations apply correctly

**How to Test:**

**Automated:**
```python
def test_create_and_apply_migration(tmp_path, monkeypatch):
    """Test creating and applying a migration."""
    # Setup: Fresh DB at initial migration
    runner.invoke(db_app, ["upgrade", "head"])

    # Create new migration
    result = runner.invoke(
        db_app,
        ["revision", "-m", "test migration", "--autogenerate"]
    )
    assert result.exit_code == 0

    # Verify migration file created
    versions_dir = Path("backend/migrations/versions")
    migration_files = list(versions_dir.glob("*.py"))
    assert len(migration_files) >= 2  # initial + new

    # Apply migration
    result = runner.invoke(db_app, ["upgrade", "head"])
    assert result.exit_code == 0

    # Verify alembic_version updated
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT version_num FROM alembic_version")
    version = cursor.fetchone()[0]
    assert version is not None
    conn.close()
```

**Manual:**
```bash
# 1. Ensure DB is at head
uv run tgenie db upgrade head

# 2. Create a test migration (add a dummy column to tasks)
# Edit backend/models/task.py to add a test column
# Then generate migration:
uv run tgenie db revision -m "add test column" --autogenerate

# 3. Review generated migration file
cat backend/migrations/versions/*_add_test_column.py

# 4. Apply migration
uv run tgenie db upgrade head

# 5. Verify schema changed
sqlite3 ~/.taskgenie/data/taskgenie.db ".schema tasks"

# 6. (Optional) Test downgrade
uv run tgenie db downgrade -1
sqlite3 ~/.taskgenie/data/taskgenie.db ".schema tasks"  # Verify reverted
```

---

### AC3: Backup and Restore Work Correctly ✅

**Success Criteria:**
- [ ] `tgenie db dump --out backup.sql` creates SQL dump file
- [ ] Dump file contains all table schemas and data
- [ ] `tgenie db restore --in backup.sql` restores database (with confirmation)
- [ ] Restored database has same schema and data as original
- [ ] Foreign key relationships preserved after restore
- [ ] Restore prompts for confirmation before overwriting

**How to Test:**

**Automated:**
```python
async def test_backup_restore_preserves_data(tmp_path, temp_settings):
    """Test that backup/restore preserves all data and relationships."""
    # Create task with attachment
    async for session in get_db():
        task = Task(id="test-1", title="Test", status="pending", priority="medium")
        session.add(task)
        await session.flush()
        attachment = Attachment(task_id=task.id, type="file", reference="/test.txt")
        session.add(attachment)
        await session.commit()

    # Backup
    backup_file = tmp_path / "backup.sql"
    result = runner.invoke(db_app, ["dump", "--out", str(backup_file)])
    assert result.exit_code == 0
    assert backup_file.exists()

    # Delete DB
    settings.db_path.unlink()

    # Restore
    result = runner.invoke(
        db_app, ["restore", "--in", str(backup_file)],
        input="y\n"
    )
    assert result.exit_code == 0

    # Verify data restored
    async for session in get_db():
        task = await session.get(Task, "test-1")
        assert task is not None
        assert len(task.attachments) == 1
```

**Manual:**
```bash
# 1. Create some test data (via SQLAlchemy or direct SQL)
sqlite3 ~/.taskgenie/data/taskgenie.db <<EOF
INSERT INTO tasks (id, title, status, priority)
VALUES ('test-1', 'Test Task', 'pending', 'high');
EOF

# 2. Create backup
uv run tgenie db dump --out backup.sql

# 3. Verify backup file exists and contains data
cat backup.sql | grep "INSERT INTO tasks"

# 4. Delete original DB
rm ~/.taskgenie/data/taskgenie.db

# 5. Restore (will prompt for confirmation)
uv run tgenie db restore --in backup.sql
# Type 'y' when prompted

# 6. Verify data restored
sqlite3 ~/.taskgenie/data/taskgenie.db "SELECT * FROM tasks WHERE id='test-1'"
# Expected: test-1 | Test Task | pending | high | ...
```

---

### AC4: Configuration Precedence Works Correctly ✅

**Success Criteria:**
- [ ] Environment variables override `.env` file
- [ ] `.env` file overrides `config.toml`
- [ ] `config.toml` overrides built-in defaults
- [ ] `DATABASE_URL` env var correctly sets database path
- [ ] `TASKGENIE_CONFIG_FILE` env var overrides default config path
- [ ] App data directories created at configured paths

**How to Test:**

**Automated:**
```python
def test_config_precedence_env_overrides_toml(tmp_path, monkeypatch):
    """Test that env vars override config.toml."""
    # Create config.toml with one DB path
    config_file = tmp_path / "config.toml"
    config_file.write_text('[app]\ndatabase_url = "sqlite+aiosqlite:///config.db"\n')
    monkeypatch.setenv("TASKGENIE_CONFIG_FILE", str(config_file))

    # Set env var to different path
    env_db_path = tmp_path / "env.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{env_db_path}")

    # Clear cache and get settings
    config.get_settings.cache_clear()
    settings = config.get_settings()

    # Verify env var path used
    assert str(env_db_path) in settings.database_url_resolved
```

**Manual:**
```bash
# 1. Create config.toml with custom DB path
mkdir -p ~/.taskgenie
cat > ~/.taskgenie/config.toml <<EOF
[app]
database_url = "sqlite+aiosqlite:///tmp/config_db.db"
EOF

# 2. Set env var to override
export DATABASE_URL="sqlite+aiosqlite:///tmp/env_db.db"

# 3. Run upgrade and verify env var path used
uv run tgenie db upgrade head
ls -la /tmp/env_db.db  # Should exist
ls -la /tmp/config_db.db  # Should NOT exist

# 4. Unset env var and verify config.toml used
unset DATABASE_URL
rm /tmp/env_db.db
uv run tgenie db upgrade head
ls -la /tmp/config_db.db  # Should exist
```

---

### AC5: FastAPI Lifespan Integration ✅

**Success Criteria:**
- [ ] FastAPI startup automatically initializes database
- [ ] Migrations run automatically on startup if needed
- [ ] Database connections properly closed on shutdown
- [ ] `/health` endpoint accessible after startup
- [ ] No errors in logs during startup/shutdown

**How to Test:**

**Automated:**
```python
def test_fastapi_lifespan_initializes_db(tmp_path, monkeypatch):
    """Test that FastAPI lifespan initializes DB and runs migrations."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")

    # TestClient triggers lifespan automatically
    client = TestClient(app)

    # Verify DB created
    assert db_path.exists()

    # Verify tables exist
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert "tasks" in tables
    assert "alembic_version" in tables
    conn.close()

    # Verify health endpoint works
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}
```

**Manual:**
```bash
# 1. Remove existing DB
rm ~/.taskgenie/data/taskgenie.db

# 2. Start FastAPI (will auto-create DB and run migrations)
uv run python -m backend.main

# 3. In another terminal, verify health endpoint
curl http://localhost:8080/health
# Expected: {"status": "ok", "version": "0.1.0"}

# 4. Verify DB was created
ls -la ~/.taskgenie/data/taskgenie.db

# 5. Check logs for any errors
# Should see: "Database initialized" or similar
```

---

## Test Plan

### Automated Tests

**Unit Tests:**
- ✅ Config precedence and validation (`tests/test_config.py`, `tests/test_config_extended.py`)
- ✅ Database initialization (`tests/test_database.py`, `tests/test_database_extended.py`)
- ✅ Model relationships (`tests/test_models.py`)
- ✅ CLI commands (`tests/test_cli_db.py`, `tests/test_cli_db_extended.py`)

**Integration Tests:**
- ✅ FastAPI lifespan integration (`tests/test_main.py`)
- ✅ End-to-end workflows (see `TEST_PLAN_POST_PR001.md`)

**Run all tests:**
```bash
make test
# or
pytest -v
```

### Manual Test Checklist

**Before marking PR-001 complete, verify:**

- [ ] **Fresh Install Test**
  - [ ] Delete `~/.taskgenie/data/taskgenie.db`
  - [ ] Run `uv run tgenie db upgrade head`
  - [ ] Verify DB created with all tables
  - [ ] Start API, verify `/health` returns 200

- [ ] **Migration Test**
  - [ ] Create a test migration: `uv run tgenie db revision -m "test" --autogenerate`
  - [ ] Apply: `uv run tgenie db upgrade head`
  - [ ] Verify schema changed
  - [ ] Test downgrade: `uv run tgenie db downgrade -1`

- [ ] **Backup/Restore Test**
  - [ ] Create test data (at least 1 task)
  - [ ] Dump: `uv run tgenie db dump --out backup.sql`
  - [ ] Delete DB
  - [ ] Restore: `uv run tgenie db restore --in backup.sql`
  - [ ] Verify data restored correctly

- [ ] **Configuration Test**
  - [ ] Test env var override: `export DATABASE_URL=...`
  - [ ] Test config.toml: Create `~/.taskgenie/config.toml`
  - [ ] Verify precedence: env > .env > config.toml > defaults

---

## Related Test Documentation

- **Comprehensive Test Plan:** [`TEST_PLAN_POST_PR001.md`](../TEST_PLAN_POST_PR001.md) - Full E2E test scenarios
- **Quick Win Tests:** [`TESTING_QUICK_WINS.md`](../TESTING_QUICK_WINS.md) - High-value, low-effort tests
- **Migrations Guide:** [`MIGRATIONS.md`](../MIGRATIONS.md) - How to create and manage migrations

## Notes / Risks / Open Questions

- SQLite downgrade support can be limited depending on migration operations; keep early migrations simple.
- If `tgenie` CLI wiring isn’t available yet, these commands can be exposed via `uv run ...` as an interim step, but the end state should be `tgenie db ...`.
