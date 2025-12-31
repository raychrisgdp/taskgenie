"""Tests for main entrypoints.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from backend.cli.main import app
from backend.main import app as backend_app
from backend.main import lifespan, main


def test_cli_list_command() -> None:
    """Test CLI list command."""
    runner = CliRunner()
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Not implemented" in result.stdout


def test_cli_list_command_with_filters() -> None:
    """Test CLI list command with filters."""
    runner = CliRunner()
    result = runner.invoke(app, ["list", "--status", "pending", "--priority", "high"])
    assert result.exit_code == 0
    assert "Not implemented" in result.stdout


def test_cli_add_command() -> None:
    """Test CLI add command."""
    runner = CliRunner()
    result = runner.invoke(app, ["add", "Test Task"])
    assert result.exit_code == 0
    assert "Not implemented" in result.stdout


def test_cli_add_command_with_options() -> None:
    """Test CLI add command with options."""
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "add",
            "Test Task",
            "--description",
            "Test description",
            "--eta",
            "2025-01-15",
            "--priority",
            "high",
        ],
    )
    assert result.exit_code == 0
    assert "Not implemented" in result.stdout


def test_cli_chat_command() -> None:
    """Test CLI chat command."""
    runner = CliRunner()
    result = runner.invoke(app, ["chat"])
    assert result.exit_code == 0
    assert "Not implemented" in result.stdout


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
