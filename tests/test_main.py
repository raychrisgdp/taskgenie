"""Tests for FastAPI main application.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import asyncio
import importlib.util
import subprocess
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
            pass

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
    import importlib.util
    from unittest.mock import patch

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
