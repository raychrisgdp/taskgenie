"""Tests for database initialization and migrations.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from sqlalchemy import text

from backend import config, database
from backend.database import close_db, get_db, init_db


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
    init_db()
    assert database.engine is not None
    await close_db()


@pytest.mark.asyncio
async def test_get_db_session(temp_settings: None) -> None:
    """Test getting a database session."""
    init_db()
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
            pass


@pytest.mark.asyncio
async def test_init_db_idempotent(temp_settings: None) -> None:
    """Test that init_db can be called multiple times safely."""
    init_db()
    assert database.engine is not None
    original_engine = database.engine

    # Call again
    init_db()
    # Should be the same engine instance
    assert database.engine is original_engine
    await close_db()


@pytest.mark.asyncio
async def test_get_db_session_commit(temp_settings: None) -> None:
    """Test that database session commits properly."""
    init_db()
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
    init_db()
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
    init_db()
    await close_db()
    # Call again - should not raise
    await close_db()


@pytest.mark.asyncio
async def test_get_db_foreign_keys_enabled(temp_settings: None) -> None:
    """Test that foreign keys are enabled in SQLite."""
    init_db()
    async for session in get_db():
        # Check foreign keys are enabled
        result = await session.execute(text("PRAGMA foreign_keys"))
        enabled = result.scalar()
        assert enabled == 1
        break
    await close_db()


def test_run_migrations_if_needed_memory_db(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _run_migrations_if_needed with :memory: database (covers lines 102-103)."""
    from unittest.mock import patch

    from backend.database import _run_migrations_if_needed

    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    config.get_settings.cache_clear()
    settings = config.get_settings()

    with patch("backend.database._run_migrations_sync") as mock_run:
        _run_migrations_if_needed(settings, "sqlite+aiosqlite:///:memory:")
        mock_run.assert_called_once()


def test_run_migrations_if_needed_non_sqlite(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _run_migrations_if_needed with non-SQLite database (covers lines 107-108)."""
    from unittest.mock import patch

    from backend.database import _run_migrations_if_needed

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
    config.get_settings.cache_clear()
    settings = config.get_settings()

    with patch("backend.database._run_migrations_sync") as mock_run:
        _run_migrations_if_needed(settings, "postgresql://user:pass@localhost/db")
        mock_run.assert_called_once()


def test_run_migrations_if_needed_exception_checking_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _run_migrations_if_needed when exception occurs checking alembic_version (covers lines 116-129)."""
    import sqlite3
    from unittest.mock import patch

    from backend.database import _run_migrations_if_needed

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

    # Mock sqlite3.connect to raise an exception
    with patch("backend.database.sqlite3.connect", side_effect=Exception("Connection error")):
        with patch("backend.database._run_migrations_sync") as mock_run:
            _run_migrations_if_needed(settings, db_url)
            # Should call _run_migrations_sync when exception occurs
            mock_run.assert_called_once()


def test_run_migrations_sync_no_alembic_ini(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test _run_migrations_sync when alembic.ini doesn't exist (covers line 146)."""
    import shutil

    from backend.database import _run_migrations_sync

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
