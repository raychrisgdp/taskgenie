"""Extended tests for database initialization and session management.

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
