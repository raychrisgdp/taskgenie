"""Tests for database initialization and migrations.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

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
