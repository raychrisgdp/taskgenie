"""Tests for database CLI commands.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import sqlite3
from pathlib import Path

import pytest
from typer.testing import CliRunner

from backend import config
from backend.cli.db import db_app


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Create a temporary database path."""
    db_path = tmp_path / "test.db"
    # Create a minimal database
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
    conn.execute("INSERT INTO test (id) VALUES (1)")
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def temp_settings(temp_db_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up temporary settings for testing."""
    db_url = f"sqlite+aiosqlite:///{temp_db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    config.get_settings.cache_clear()


def test_db_dump(temp_settings: None, temp_db_path: Path, tmp_path: Path) -> None:
    """Test database dump command."""
    runner = CliRunner()
    output_file = tmp_path / "backup.sql"

    result = runner.invoke(db_app, ["dump", "--out", str(output_file)])

    assert result.exit_code == 0
    assert output_file.exists()
    # Verify SQL file contains our test table
    content = output_file.read_text()
    assert "CREATE TABLE test" in content or "test" in content.lower()


def test_db_restore(
    temp_settings: None, temp_db_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test database restore command."""
    # Create a backup first
    backup_file = tmp_path / "backup.sql"
    conn = sqlite3.connect(str(temp_db_path))
    with backup_file.open("w") as f:
        for line in conn.iterdump():
            f.write(f"{line}\n")
    conn.close()

    # Delete the database
    temp_db_path.unlink()

    # Restore it
    runner = CliRunner()
    # Use input to confirm
    result = runner.invoke(db_app, ["restore", "--in", str(backup_file)], input="y\n")

    assert result.exit_code == 0
    assert temp_db_path.exists()

    # Verify data was restored
    conn = sqlite3.connect(str(temp_db_path))
    cursor = conn.execute("SELECT id FROM test")
    assert cursor.fetchone()[0] == 1
    conn.close()


def test_db_reset_requires_confirmation(
    temp_settings: None, temp_db_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that db reset requires confirmation."""
    runner = CliRunner()
    result = runner.invoke(db_app, ["reset"], input="n\n")

    assert result.exit_code == 0
    assert temp_db_path.exists()  # Database should still exist


def test_db_reset_with_yes_flag(
    temp_settings: None, temp_db_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that db reset works with --yes flag."""
    runner = CliRunner()
    result = runner.invoke(db_app, ["reset", "--yes"])

    assert result.exit_code == 0
    assert not temp_db_path.exists()  # Database should be deleted
