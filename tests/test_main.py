"""Tests for FastAPI main application.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import asyncio
import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from backend.main import app as backend_app
from backend.main import lifespan, main


def test_backend_main_lifespan() -> None:
    """Test backend main lifespan context manager."""
    app_mock = MagicMock()

    # Test that lifespan can be entered and exited
    async def test_lifespan() -> None:
        async with lifespan(app_mock):
            # Lifespan context manager should enter and exit without errors
            ...

    asyncio.run(test_lifespan())


def test_backend_main_health_check(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test backend health check endpoint."""

    # Set up temporary database
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    client = TestClient(backend_app)
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_backend_main_startup_runs_migrations_fresh_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that FastAPI startup automatically runs migrations on fresh DB.

    This explicitly verifies AC1: migrations run automatically when DB doesn't exist.
    Uses init_db_async() to match FastAPI lifespan behavior.
    """
    import sqlite3  # noqa: PLC0415

    from backend.config import get_settings  # noqa: PLC0415

    # Set up temporary database (fresh, doesn't exist yet)
    db_path = tmp_path / "fresh.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    # Clear settings cache to pick up new DATABASE_URL
    get_settings.cache_clear()

    # Ensure DB doesn't exist
    assert not db_path.exists(), "Database should not exist before startup"

    # Call init_db_async() (same as lifespan does on startup)
    from backend.database import init_db_async  # noqa: PLC0415

    asyncio.run(init_db_async())

    # Get actual database path from settings (may differ from db_path due to resolution)
    settings = get_settings()
    actual_db_path = settings.database_path

    # Verify database was created (check both paths)
    assert db_path.exists() or actual_db_path.exists(), (
        f"Database should be created after startup. Expected: {db_path}, Actual: {actual_db_path}"
    )

    # Use the actual path that exists
    check_path = actual_db_path if actual_db_path.exists() else db_path

    # Verify alembic_version table exists (migrations ran)
    conn = sqlite3.connect(str(check_path))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
    version_table = cursor.fetchone()
    conn.close()

    assert version_table is not None, "alembic_version table should exist after migrations"
    assert version_table[0] == "alembic_version"

    # Verify version is set (migrations actually ran)
    conn = sqlite3.connect(str(check_path))
    cursor = conn.cursor()
    cursor.execute("SELECT version_num FROM alembic_version")
    version = cursor.fetchone()
    conn.close()

    assert version is not None, "Migration version should be set"
    assert len(version[0]) > 0, "Migration version should not be empty"


@patch("backend.main.uvicorn.run")
def test_backend_main_function(mock_uvicorn: MagicMock) -> None:
    """Test backend main function."""
    main()
    mock_uvicorn.assert_called_once()
    # Verify it was called with correct parameters
    call_args = mock_uvicorn.call_args
    assert call_args[0][0] == "backend.main:app"


def test_backend_main_name_main() -> None:
    """Test backend main module when run as __main__ (covers line 53)."""
    # Load the module and execute it as __main__ to trigger line 53
    main_path = Path("backend/main.py")
    spec = importlib.util.spec_from_file_location("__main__", main_path)
    assert spec is not None and spec.loader is not None

    # Mock uvicorn.run before executing
    with patch("backend.main.uvicorn.run") as mock_run:
        module = importlib.util.module_from_spec(spec)
        # Set __name__ to __main__ to trigger the if block
        module.__name__ = "__main__"
        sys.modules["__main__"] = module
        spec.loader.exec_module(module)
        # Verify uvicorn.run was called (indirectly through main())
        mock_run.assert_called_once()
