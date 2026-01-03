"""Tests for database initialization and migrations.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import asyncio
import shutil
import sqlite3
import time
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import text

from backend import config, database
from backend.database import _run_migrations_if_needed, _run_migrations_sync, close_db, get_db, init_db, init_db_async


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Create a temporary database path."""
    db_path = tmp_path / "test.db"
    return db_path


@pytest.fixture
def temp_settings(temp_db_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up temporary settings for testing."""
    db_url = f"sqlite+aiosqlite:///{temp_db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    config.get_settings.cache_clear()


@pytest.mark.asyncio
async def test_init_db(temp_settings: None) -> None:
    """Test database initialization."""
    await init_db_async()
    assert database.engine is not None
    await close_db()


# Maximum time allowed for init_db() to complete (in seconds)
_INIT_DB_TIMEOUT_SECONDS = 5.0


@pytest.mark.asyncio
async def test_init_db_runs_migrations_and_completes_promptly(temp_db_path: Path, temp_settings: None) -> None:
    """Test that init_db_async() completes promptly and leaves migrated schema.

    Regression test for DB-1: ensures migrations don't hang and alembic_version table exists.
    Uses async version to match FastAPI lifespan behavior.
    """
    start_time = time.time()
    await init_db_async()
    elapsed = time.time() - start_time

    # Should complete quickly (within timeout)
    assert elapsed < _INIT_DB_TIMEOUT_SECONDS, (
        f"init_db_async() took {elapsed:.2f}s, expected < {_INIT_DB_TIMEOUT_SECONDS}s"
    )

    # Verify alembic_version table exists (proves migrations ran)
    conn = sqlite3.connect(str(temp_db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
    has_version_table = cursor.fetchone() is not None
    conn.close()

    assert has_version_table, "alembic_version table should exist after init_db_async()"

    await close_db()


@pytest.mark.asyncio
async def test_get_db_session(temp_settings: None) -> None:
    """Test getting a database session."""
    await init_db_async()
    async for session in get_db():
        # Test that we can execute a query
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1
        break
    await close_db()


@pytest.mark.asyncio
async def test_get_db_raises_if_not_initialized() -> None:
    """Test that get_db raises if database not initialized."""
    # Ensure database is not initialized
    if database.engine is not None:
        await close_db()

    with pytest.raises(RuntimeError, match="Database not initialized"):
        async for _ in get_db():
            # Should raise RuntimeError before yielding
            ...


@pytest.mark.asyncio
async def test_init_db_idempotent(temp_settings: None) -> None:
    """Test that init_db_async can be called multiple times safely."""
    await init_db_async()
    assert database.engine is not None
    original_engine = database.engine

    # Call again
    await init_db_async()
    # Should be the same engine instance
    assert database.engine is original_engine
    await close_db()


def test_init_db_idempotent_sync(temp_settings: None) -> None:
    """Test that init_db() can be called multiple times safely (synchronous version)."""
    # Reset database state
    database.engine = None
    database.async_session_maker = None

    init_db()
    assert database.engine is not None
    original_engine = database.engine

    # Call again - should return early without reinitializing
    init_db()
    # Should be the same engine instance
    assert database.engine is original_engine

    # Cleanup
    asyncio.run(close_db())


@pytest.mark.asyncio
async def test_get_db_session_commit(temp_settings: None) -> None:
    """Test that database session commits properly."""
    await init_db_async()
    db_session = asynccontextmanager(get_db)

    async with db_session() as session:
        await session.execute(text("CREATE TABLE IF NOT EXISTS test_commit (id INTEGER)"))
        await session.execute(text("INSERT INTO test_commit (id) VALUES (1)"))

    # Verify commit worked by checking in new session
    async with db_session() as session:
        result = await session.execute(text("SELECT id FROM test_commit"))
        row = result.scalar()
        assert row == 1
    await close_db()


@pytest.mark.asyncio
async def test_get_db_session_rollback(temp_settings: None) -> None:
    """Test that database session rolls back on error."""
    await init_db_async()
    db_session = asynccontextmanager(get_db)

    with pytest.raises(ValueError, match="Test error"):
        async with db_session() as session:
            await session.execute(text("CREATE TABLE IF NOT EXISTS test_rollback (id INTEGER)"))
            await session.execute(text("INSERT INTO test_rollback (id) VALUES (1)"))
            # Force an error
            raise ValueError("Test error")

    # Verify rollback worked - table should exist but row should not
    async with db_session() as session:
        # Check if table exists
        result = await session.execute(
            text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='test_rollback'")
        )
        table_exists = result.scalar() == 1
        if table_exists:
            # If table exists, check if row was rolled back
            result = await session.execute(text("SELECT COUNT(*) FROM test_rollback"))
            count = result.scalar()
            # Row should not exist due to rollback
            assert count == 0
    await close_db()


@pytest.mark.asyncio
async def test_close_db_idempotent(temp_settings: None) -> None:
    """Test that close_db can be called multiple times safely."""
    await init_db_async()
    await close_db()
    # Call again - should not raise
    await close_db()


@pytest.mark.asyncio
async def test_get_db_foreign_keys_enabled(temp_settings: None) -> None:
    """Test that foreign keys are enabled in SQLite."""
    await init_db_async()
    async for session in get_db():
        # Check foreign keys are enabled
        result = await session.execute(text("PRAGMA foreign_keys"))
        enabled = result.scalar()
        assert enabled == 1
        break
    await close_db()


@pytest.mark.asyncio
async def test_engine_level_foreign_keys_enabled(temp_settings: None) -> None:
    """Test that foreign keys are enabled at engine connection level (not just session level)."""
    await init_db_async()
    assert database.engine is not None

    # Open a raw connection via engine.connect() (async)
    async with database.engine.connect() as conn:
        result = await conn.execute(text("PRAGMA foreign_keys"))
        enabled = result.scalar()
        assert enabled == 1, "Foreign keys should be enabled at engine connection level"

    await close_db()


def test_run_migrations_if_needed_memory_db(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _run_migrations_if_needed with :memory: database (covers lines 102-103)."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    config.get_settings.cache_clear()
    settings = config.get_settings()

    with patch("backend.database._run_migrations_sync") as mock_run:
        _run_migrations_if_needed(settings, "sqlite+aiosqlite:///:memory:")
        mock_run.assert_called_once()


def test_run_migrations_if_needed_non_sqlite(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _run_migrations_if_needed with non-SQLite database (covers lines 107-108)."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
    config.get_settings.cache_clear()
    settings = config.get_settings()

    with patch("backend.database._run_migrations_sync") as mock_run:
        _run_migrations_if_needed(settings, "postgresql://user:pass@localhost/db")
        mock_run.assert_called_once()


def test_run_migrations_if_needed_no_version_table(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _run_migrations_if_needed when alembic_version table doesn't exist (covers lines 122-126)."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    config.get_settings.cache_clear()
    settings = config.get_settings()

    # Create database file without alembic_version table
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE test (id INTEGER)")
    conn.commit()
    conn.close()

    # This should trigger the path where version table doesn't exist
    with patch("backend.database._run_migrations_sync") as mock_run:
        _run_migrations_if_needed(settings, db_url)
        # Should call _run_migrations_sync when version table doesn't exist
        mock_run.assert_called_once()


def test_run_migrations_if_needed_version_table_exists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _run_migrations_if_needed when alembic_version table exists (covers branch 125->exit)."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    config.get_settings.cache_clear()
    settings = config.get_settings()

    # Create database file with alembic_version table
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
    conn.execute("INSERT INTO alembic_version (version_num) VALUES ('abc123')")
    conn.commit()
    conn.close()

    # This should NOT call _run_migrations_sync when version table exists
    with patch("backend.database._run_migrations_sync") as mock_run:
        _run_migrations_if_needed(settings, db_url)
        # Should NOT call _run_migrations_sync when version table exists
        mock_run.assert_not_called()


def test_run_migrations_if_needed_exception_checking_version(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _run_migrations_if_needed when exception occurs checking alembic_version (covers lines 127-129)."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    config.get_settings.cache_clear()
    settings = config.get_settings()

    # Create database file
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE test (id INTEGER)")
    conn.commit()
    conn.close()

    # Mock cursor.execute to raise an exception AFTER connection is made
    # This ensures lines 118-122 are executed before the exception
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("Query error")
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with patch("backend.database.sqlite3.connect", return_value=mock_conn):
        with patch("backend.database._run_migrations_sync") as mock_run:
            _run_migrations_if_needed(settings, db_url)
            # Should call _run_migrations_sync when exception occurs
            mock_run.assert_called_once()
            # Verify cursor.execute was called (lines 118-122 executed)
            mock_cursor.execute.assert_called_once()


def test_run_migrations_sync_no_alembic_ini(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _run_migrations_sync when alembic.ini doesn't exist (covers line 146)."""
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    config.get_settings.cache_clear()
    settings = config.get_settings()

    # Temporarily move alembic.ini out of the way
    alembic_ini_path = Path("backend/migrations/alembic.ini")
    backup_path = tmp_path / "alembic.ini.backup"

    if alembic_ini_path.exists():
        shutil.move(str(alembic_ini_path), str(backup_path))

    try:
        # Should return early without error when alembic.ini doesn't exist
        _run_migrations_sync(settings, db_url)
        # No exception should be raised
    finally:
        # Restore alembic.ini
        if backup_path.exists():
            shutil.move(str(backup_path), str(alembic_ini_path))


def test_run_migrations_sync_upgrade_exception_debug_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _run_migrations_sync when alembic.command.upgrade raises exception in debug mode.

    In debug mode, should warn and continue (not fail-fast).
    """
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("DEBUG", "true")
    config.get_settings.cache_clear()
    settings = config.get_settings()

    # Mock alembic.command.upgrade to raise an exception
    with patch("backend.database.alembic.command.upgrade", side_effect=Exception("Migration failed")):
        with patch("backend.database.logger") as mock_logger:
            # Should not raise, but should log warning (debug mode)
            _run_migrations_sync(settings, db_url)
            # Verify warning was logged
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert "Failed to run automatic migrations on startup" in call_args[0][0]
            assert call_args[1]["exc_info"] is True


def test_run_migrations_sync_upgrade_exception_production_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _run_migrations_sync when alembic.command.upgrade raises exception in production mode.

    In production mode (debug=False), should fail-fast.
    """
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("DEBUG", "false")
    config.get_settings.cache_clear()
    settings = config.get_settings()

    # Mock alembic.command.upgrade to raise an exception
    with patch("backend.database.alembic.command.upgrade", side_effect=Exception("Migration failed")):
        with patch("backend.database.logger") as mock_logger:
            # Should raise RuntimeError (fail-fast in production)
            with pytest.raises(RuntimeError, match="Database migration failed"):
                _run_migrations_sync(settings, db_url)
            # Verify error was logged
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Failed to run automatic migrations on startup" in call_args[0][0]
            assert call_args[1]["exc_info"] is True
