# Agent Guide (Detailed / Archived)

This document preserves the original long-form guidance that previously lived in the repo
root `AGENTS.md`. The repo root `AGENTS.md` is now intentionally short and actionable for
agents; refer here for deeper background, examples, and rationale.

---

# Agent Guide: TaskGenie Development Patterns

**Purpose:** This document helps AI agents (and human developers) understand the codebase structure, established patterns, conventions, and important learnings from implementation work.

**Last Updated:** 2025-01-30  
**Based on:** PR-001 (Database & Configuration) implementation

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Code Conventions](#code-conventions)
3. [Configuration Patterns](#configuration-patterns)
4. [Database Patterns](#database-patterns)
5. [CLI Patterns](#cli-patterns)
6. [Testing Patterns](#testing-patterns)
7. [Common Pitfalls](#common-pitfalls)
8. [Key Learnings](#key-learnings)

---

## Project Structure

### Directory Layout

```
personal-todo/
├── backend/              # Main application code
│   ├── cli/             # CLI commands (Typer)
│   │   ├── db.py        # Database subcommands
│   │   └── main.py      # Main CLI entry point
│   ├── models/          # SQLAlchemy ORM models
│   │   ├── __init__.py  # Base + model imports
│   │   ├── task.py
│   │   ├── attachment.py
│   │   ├── notification.py
│   │   ├── chat_history.py
│   │   └── config.py
│   ├── migrations/       # Alembic migrations
│   │   ├── alembic.ini
│   │   ├── env.py       # Alembic environment config
│   │   ├── script.py.mako
│   │   └── versions/    # Migration scripts
│   ├── config.py         # Pydantic Settings
│   ├── database.py       # DB initialization & session management
│   └── main.py           # FastAPI app
├── tests/                # Test suite
│   ├── test_config.py
│   ├── test_database.py
│   └── test_cli_db.py
├── docs/                 # Documentation
│   ├── 00-research/
│   ├── 01-design/
│   └── 02-implementation/
└── pyproject.toml        # Project config & dependencies
```

### Key Principles

1. **Local-first**: All data stored in `~/.taskgenie/` by default
2. **Async-first**: Use `async`/`await` for database operations
3. **Type-safe**: Use type hints everywhere (mypy strict mode)
4. **Test-driven**: Write tests alongside implementation
5. **Documentation**: Update docs when adding features

---

## Code Conventions

### Python Style

- **Line length**: 100 characters (configured in `ruff`)
- **Type hints**: Required for all functions (mypy strict mode)
- **Docstrings**: Google style (configured in `ruff`)
- **Imports**: Use `from __future__ import annotations` for forward references
- **String quotes**: Double quotes (`"`) by default

### Naming Conventions

- **CLI command**: `tgenie` (not `taskgenie` or `tg`)
- **Modules**: `snake_case` (e.g., `chat_history.py`)
- **Classes**: `PascalCase` (e.g., `Task`, `Settings`)
- **Functions**: `snake_case` (e.g., `get_db`, `init_db`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `APP_NAME`)
- **Private functions**: Prefix with `_` (e.g., `_load_toml_config`)

### Import Organization

```python
# Standard library
from __future__ import annotations
from pathlib import Path
from typing import Any

# Third-party
from pydantic import Field
from sqlalchemy import String
from typer import Typer

# Local imports
from backend.config import settings
from backend.models import Task
```

### Type Annotations

- Use `str | None` instead of `Optional[str]` (Python 3.10+)
- Use `collections.abc` types (e.g., `AsyncGenerator`, `Sequence`)
- Use `Mapped[T]` for SQLAlchemy model fields
- Use `Annotated` for SQLAlchemy type hints (e.g., `Annotated[str, 36]`)

---

## Configuration Patterns

### Settings Precedence

Configuration loads in this order (highest wins):

1. **Environment variables** (e.g., `export APP_NAME="MyApp"`)
2. **`.env` file** (project root, for dev convenience)
3. **`~/.taskgenie/config.toml`** (user config, persistent)
4. **Built-in defaults** (defined in `backend/config.py`)

### Configuration Implementation

**File:** `backend/config.py`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import PydanticBaseSettingsSource

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @classmethod
    def settings_customise_sources(cls, ...) -> tuple[PydanticBaseSettingsSource, ...]:
        """Set precedence: env → .env → TOML → defaults"""
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            TaskGenieTomlSettingsSource(settings_cls),
            file_secret_settings,
        )

# Singleton pattern with caching
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

### TOML Config Structure

**File:** `~/.taskgenie/config.toml`

```toml
[app]
name = "My TaskGenie"
debug = false

[database]
url = "sqlite+aiosqlite:///custom/path.db"

[llm]
provider = "openrouter"
model = "anthropic/claude-3-opus"

[notifications]
enabled = true
schedule = ["24h", "6h"]
```

**Note:** TOML sections are flattened to `{section}_{key}` for Pydantic (e.g., `app_name`, `database_url`).

### Path Management

- **App data dir**: `~/.taskgenie/` (configurable via `TASKGENIE_DATA_DIR`)
- **Database**: `{app_data_dir}/data/taskgenie.db`
- **Vector store**: `{app_data_dir}/data/chroma/`
- **Attachments cache**: `{app_data_dir}/cache/attachments/`
- **Logs**: `{app_data_dir}/logs/`

**Pattern:** Use `@property` methods for computed paths:

```python
@property
def database_path(self) -> Path:
    """Get canonical database file path.

    Automatically strips query parameters (e.g., ?mode=ro) from SQLite URLs
    before extracting the file path. This prevents invalid file paths when
    URLs include query parameters.
    """
    if self.database_url and self.database_url.startswith("sqlite"):
        # Strip query parameters before extracting path
        url = self.database_url.split("?")[0] if "?" in self.database_url else self.database_url
        # Extract path from sqlite:///path/to/db or sqlite+aiosqlite:///path/to/db
        # ... path extraction logic ...
    return self.app_data_dir / "data" / "taskgenie.db"
```

**Important:** The `database_path` property automatically strips query parameters from SQLite URLs (e.g., `sqlite:///db.sqlite?mode=ro` → `db.sqlite`). This ensures file system operations work correctly with URLs that include query parameters.

---

## Database Patterns

### SQLAlchemy Models

**Pattern:** Use `Mapped[T]` with `mapped_column()`:

```python
from __future__ import annotations
from sqlalchemy import String, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models import Base

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    attachments: Mapped[list[Attachment]] = relationship(
        "Attachment", back_populates="task", cascade="all, delete-orphan"
    )
```

**Key Points:**
- Use `String(36)` for UUID primary keys
- Use `Text` for long text fields (not `String`)
- Use `JSON` for JSON columns (SQLite supports this)
- Use `server_default` for database-level defaults
- Use `back_populates` for bidirectional relationships
- Use `cascade="all, delete-orphan"` for parent-child relationships

### Database Initialization

**File:** `backend/database.py`

**Pattern:** Use `init_db_async()` in FastAPI lifespan, `init_db()` for sync contexts:

```python
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker

# Global state
engine: AsyncEngine | None = None
async_session_maker: async_sessionmaker[AsyncSession] | None = None

def init_db() -> None:
    """Initialize database synchronously (for CLI, tests, etc.)."""
    global engine, async_session_maker
    # ... creates engine and runs migrations synchronously ...

async def init_db_async() -> None:
    """Initialize database asynchronously (for FastAPI lifespan).

    Runs migrations in a threadpool using asyncio.to_thread() to avoid
    blocking the event loop.
    """
    global engine, async_session_maker
    # ... creates engine and runs migrations in threadpool ...

# FastAPI lifespan example:
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_db_async()  # ✅ Use async version
    yield
    await close_db()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get a database session."""
    if async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() or init_db_async() first.")

    async with async_session_maker() as session:
        # Enable foreign keys for SQLite
        await session.execute(text("PRAGMA foreign_keys=ON"))
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

**Key Points:**
- **FastAPI lifespan**: Always use `init_db_async()` to avoid blocking the event loop
- **Sync contexts**: Use `init_db()` for CLI commands and synchronous test code
- Always enable `PRAGMA foreign_keys=ON` for SQLite
- Use `async_sessionmaker` for session management
- Use `expire_on_commit=False` to avoid lazy loading issues
- Migrations run automatically if database doesn't exist or `alembic_version` table is missing

### Alembic Migrations

**Pattern:** Use Alembic for schema migrations:

```bash
# Create migration
uv run tgenie db revision -m "Add new column" --autogenerate

# Apply migrations
uv run tgenie db upgrade head

# Rollback
uv run tgenie db downgrade -1
```

**Migration File Structure:**

```python
\"\"\"Add new column

Revision ID: 002_add_column
Revises: 001_initial
Create Date: 2025-01-30 12:00:00.000000
\"\"\"
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "002_add_column"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.add_column("tasks", sa.Column("new_field", sa.String(100), nullable=True))

def downgrade() -> None:
    op.drop_column("tasks", "new_field")
```

**Key Points:**
- Always review autogenerated migrations
- SQLite has limited `ALTER TABLE` support (some downgrades may fail)
- Use `server_default` for defaults in migrations
- Test migrations on a copy of production data
- **Sync URL conversion**: Migrations always use sync URLs (`sqlite://`) even when runtime uses async URLs (`sqlite+aiosqlite://`). The CLI and startup code automatically convert URLs to avoid asyncio conflicts (see `docs/02-implementation/MIGRATIONS.md` for details).

---

## CLI Patterns

### Typer Command Structure

**File:** `backend/cli/db.py`

```python
from typer import Typer
from rich.console import Console

console = Console()
db_app = Typer(help="Database management commands")

@db_app.command(name="upgrade")
def upgrade(
    revision: str = typer.Option("head", "--rev", help="Revision to upgrade to"),
) -> None:
    \"\"\"Upgrade database to a specific revision.\"\"\"
    try:
        cfg = get_alembic_cfg()
        alembic.command.upgrade(cfg, revision)
        console.print("[green]✓[/green] Database upgraded")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)
```

**Key Points:**
- Use `Typer()` for subcommand groups
- Use `rich.Console` for colored output
- Use `typer.Option()` for flags, `typer.Argument()` for positional args
- Always handle errors gracefully with user-friendly messages
- Use `typer.Exit(1)` for error exits

### CLI Registration

**File:** `backend/cli/main.py`

```python
from typer import Typer
from backend.cli.db import db_app

app = Typer(help="TaskGenie CLI")
app.add_typer(db_app, name="db")
```

**Entry Point:** `pyproject.toml`

```toml
[project.scripts]
tgenie = "backend.cli.main:app"
```

---

## Testing Patterns

### Test Structure

**File:** `tests/test_config.py`

```python
import pytest
from pathlib import Path
from backend.config import Settings

@pytest.fixture(autouse=True)
def setup_test_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    \"\"\"Set up temporary environment for tests.\"\"\"
    monkeypatch.setenv("TASKGENIE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(backend.config, "settings", Settings(_env_file=None))

def test_config_precedence_env_var_overrides_default(monkeypatch: pytest.MonkeyPatch) -> None:
    \"\"\"Test that environment variables override defaults.\"\"\"
    monkeypatch.setenv("APP_NAME", "TestApp")
    settings = Settings(_env_file=None)
    assert settings.app_name == "TestApp"
```

**Key Points:**
- Use `pytest.fixture(autouse=True)` for common setup
- Use `monkeypatch` to modify environment variables
- Use `tmp_path` for temporary files
- Use `Settings(_env_file=None)` to skip `.env` file loading in tests
- Use descriptive test names: `test_{what}_{condition}_{expected_result}`

### Async Test Pattern

**File:** `tests/test_database.py`

```python
import pytest
from backend.database import init_db, get_db, close_db

@pytest.mark.asyncio
async def test_db_initialization() -> None:
    \"\"\"Test database initialization.\"\"\"
    await init_db(run_migrations=True)

    async with get_db() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar_one() == 1

    await close_db()
```

**Key Points:**
- Use `@pytest.mark.asyncio` for async tests
- Use `pytest-asyncio` with `asyncio_mode = "auto"` in `pyproject.toml`
- Always clean up resources (call `close_db()`)

### CLI Test Pattern

**File:** `tests/test_cli_db.py`

```python
from typer.testing import CliRunner
from backend.cli.main import app

runner = CliRunner()

def test_db_upgrade_command() -> None:
    \"\"\"Test the 'tgenie db upgrade' command.\"\"\"
    result = runner.invoke(app, ["db", "upgrade", "head"])
    assert result.exit_code == 0
    assert "Database upgraded" in result.stdout
```

**Key Points:**
- Use `CliRunner` from `typer.testing`
- Check `exit_code` and `stdout` content
- Use descriptive assertions

---

## Common Pitfalls

### 1. Configuration Precedence

**❌ Wrong:** Loading TOML before `.env` file
```python
# Wrong precedence
return (env_settings, toml_settings, dotenv_settings)  # TOML overrides .env!
```

**✅ Correct:** Load TOML after `.env` but before defaults
```python
# Correct precedence
return (env_settings, dotenv_settings, toml_settings, file_secret_settings)
```

### 2. SQLite Foreign Keys

**❌ Wrong:** Forgetting to enable foreign keys
```python
async with get_db() as session:
    # Foreign keys are OFF by default!
    await session.execute(text("INSERT INTO ..."))
```

**✅ Correct:** Always enable foreign keys
```python
async with get_db() as session:
    await session.execute(text("PRAGMA foreign_keys=ON"))
    await session.execute(text("INSERT INTO ..."))
```

### 3. Database Path Resolution

**❌ Wrong:** Hardcoding database path
```python
database_url = "sqlite+aiosqlite:///./data/taskgenie.db"  # Relative path!
```

**✅ Correct:** Use canonical path from settings
```python
database_url = f"sqlite+aiosqlite:///{settings.database_path}"
```

### 4. Model Field Naming

**❌ Wrong:** Using Python keyword as column name
```python
metadata: Mapped[dict | None] = mapped_column(JSON)  # 'metadata' is a keyword!
```

**✅ Correct:** Use different Python name, map to SQL column
```python
meta_data: Mapped[dict | None] = mapped_column("metadata", JSON)
```

### 5. Settings Singleton

**❌ Wrong:** Creating new Settings instance every time
```python
def get_db():
    settings = Settings()  # New instance every time!
    url = settings.database_url
```

**✅ Correct:** Use cached singleton
```python
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

settings = get_settings()  # Use singleton
```

### 6. Async Context Managers

**❌ Wrong:** Not using async context manager
```python
session = async_session_maker()
result = await session.execute(...)  # Session not properly closed!
```

**✅ Correct:** Use async context manager
```python
async with async_session_maker() as session:
    result = await session.execute(...)
    # Session automatically closed
```

---

## Precommit Workflow & Code Quality

### Always Run `make precommit` Before Committing

The `make precommit` command runs all code quality checks:
- Formatting (ruff format)
- Linting (ruff check)
- Type checking (mypy)
- Test syntax validation
- Docs validation (scripts/check_docs.py)

**Workflow:**
```bash
# 1. Make your changes
# 2. Run precommit
make precommit

# 3. Fix any issues reported
# 4. Commit
```

### Common Precommit Issues & Fixes

#### 1. Duplicate Test Functions (F811)

**Error:** `F811 redefinition of unused 'test_function_name'`

**Fix:** Remove duplicate test functions. Check for duplicate function names:
```bash
grep -n "^def test_" tests/test_*.py | sort | uniq -d
```

#### 2. Incomplete Test Functions

**Error:** Syntax error with `async` without `def`

**Fix:** Complete the function definition:
```python
# ❌ Wrong
@pytest.mark.asyncio
async

def test_something():
    ...

# ✅ Correct
@pytest.mark.asyncio
async def test_something():
    ...
```

#### 3. Unused Variables (F841)

**Error:** `F841 local variable 'result' is assigned to but never used`

**Fix:** Prefix with `_` if intentionally unused:
```python
# ❌ Wrong
result = subprocess.run(...)

# ✅ Correct
_ = subprocess.run(...)
```

#### 4. Import Inside Function (PLC0415)

**Error:** `PLC0415 Import used inside function or method`

**Fix:** Add `# noqa: PLC0415` if intentional (common in tests):
```python
def test_something():
    # Intentional import to avoid circular dependency
    from backend.config import _load_toml_config  # noqa: PLC0415
    ...
```

#### 5. Type Errors with Mocks

**Error:** `Argument of type "object" cannot be assigned to parameter ...`

**Fix:** Use specific type ignore comment:
```python
# ❌ Wrong
def failing_open(self: Path, *args: object, **kwargs: object) -> object:
    return original_open(self, *args, **kwargs)

# ✅ Correct
def failing_open(self: Path, *args: object, **kwargs: object) -> object:
    return original_open(self, *args, **kwargs)  # type: ignore[call-overload]
```

#### 6. Mutable Default Arguments

**Error:** `B006 Mutable default argument`

**Fix:** Use `default_factory`:
```python
# ❌ Wrong
notification_schedule: list[str] = Field(default=["24h", "6h"])

# ✅ Correct
notification_schedule: list[str] = Field(default_factory=lambda: ["24h", "6h"])
```

### Async Migration Handling

When calling synchronous Alembic commands from async context (e.g., FastAPI startup), use threading to avoid blocking:

```python
def _run_migrations_sync(database_url: str) -> None:
    """Synchronously run Alembic migrations."""
    def _upgrade() -> None:
        try:
            alembic.command.upgrade(cfg, "head")
        except Exception:
            logger.warning("Failed to run automatic migrations", exc_info=True)

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # No event loop, run directly
        _upgrade()
    else:
        # Event loop exists, run in thread
        thread = threading.Thread(target=_upgrade, name="taskgenie-alembic-upgrade")
        thread.start()
        thread.join()
```

---

## Key Learnings

### From PR-001 Implementation

1. **Pydantic Settings Customization**
   - Use `settings_customise_sources()` to control precedence
   - Create custom `PydanticBaseSettingsSource` for TOML loading
   - Use `@lru_cache` for singleton pattern

2. **Alembic with Async SQLAlchemy**
   - Use `async_engine_from_config()` in `env.py`
   - Use `connection.run_sync()` to run migrations
   - Always enable foreign keys before migrations

3. **SQLite-Specific Considerations**
   - Foreign keys are OFF by default (enable in every session)
   - Limited `ALTER TABLE` support (plan migrations carefully)
   - Use `JSON` type for JSON columns (works with SQLite 3.38+)

4. **Path Management**
   - Use `pathlib.Path` everywhere (not `str`)
   - Use `@property` for computed paths
   - Use `expanduser()` for `~` expansion
   - Create directories lazily (not at import time)

5. **Testing Configuration**
   - Use `monkeypatch` for environment variables
   - Use `tmp_path` for temporary files
   - Use `Settings(_env_file=None)` to skip `.env` loading
   - Use `autouse=True` fixtures for common setup

6. **CLI Error Handling**
   - Always catch exceptions and show user-friendly messages
   - Use `rich.Console` for colored output
   - Use `typer.Exit(1)` for error exits
   - Confirm destructive operations (e.g., `db reset`)

### Best Practices

1. **Always review autogenerated migrations** - Alembic can make mistakes
2. **Test migrations on a copy** - Never test on production data
3. **Use type hints everywhere** - Helps catch errors early
4. **Write tests alongside code** - Don't defer testing
5. **Update documentation** - Keep docs in sync with code
6. **Follow existing patterns** - Consistency is key
7. **Use descriptive names** - Code should be self-documenting
8. **Handle errors gracefully** - Always provide helpful error messages

---

## Quick Reference

### Common Commands

```bash
# Database migrations
uv run tgenie db upgrade head          # Apply all migrations
uv run tgenie db downgrade -1          # Rollback one migration
uv run tgenie db revision -m "..." --autogenerate  # Create migration

# Database backup/restore
uv run tgenie db dump --out backup.sql      # Backup
uv run tgenie db restore --in backup.sql   # Restore
uv run tgenie db reset --yes                # Reset (dev only)

# Testing
uv run pytest                              # Run all tests
uv run pytest tests/test_config.py         # Run specific test file
uv run pytest -v                           # Verbose output
uv run pytest --cov=backend                # With coverage

# Linting & Code Quality
make precommit                              # Run all checks (format, lint, typecheck)
uv run ruff check .                        # Check code
uv run ruff format .                       # Format code
uv run mypy backend                        # Type checking
```

### File Locations

- **Config**: `backend/config.py`
- **Database**: `backend/database.py`
- **Models**: `backend/models/`
- **Migrations**: `backend/migrations/versions/`
- **CLI**: `backend/cli/`
- **Tests**: `tests/`
- **Docs**: `docs/`

### Environment Variables

- `TASKGENIE_DATA_DIR` - Override app data directory
- `TASKGENIE_CONFIG_FILE` - Override config file path
- `DATABASE_URL` - Override database URL
- `APP_NAME` - Override app name
- `DEBUG` - Enable debug mode

---

## Contributing Guidelines

When implementing new features:

1. **Read the PR spec** - Understand requirements before coding
2. **Follow existing patterns** - Consistency is important
3. **Write tests** - Test coverage should increase, not decrease
4. **Update documentation** - Keep docs in sync with code
5. **Run linters** - Fix all linting errors before committing
6. **Check type hints** - Run `mypy` to catch type errors
7. **Test migrations** - Always test migrations on a copy of data
8. **Update this guide** - Add new patterns and learnings here

---

**Last Updated:** 2025-01-30  
**Maintained by:** Development team  
**Questions?** Check `docs/` directory or PR specs in `docs/02-implementation/pr-specs/`
