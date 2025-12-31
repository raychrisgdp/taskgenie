"""Extended tests for database CLI commands.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

import backend.cli.db as cli_db
from backend import config, database
from backend.cli.db import db_app


@pytest.fixture
def temp_settings_with_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up temporary settings with initialized database."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    config.get_settings.cache_clear()
    # Initialize database
    database.init_db()


def test_db_upgrade(temp_settings_with_db: None) -> None:
    """Test database upgrade command."""
    runner = CliRunner()
    result = runner.invoke(db_app, ["upgrade"])

    assert result.exit_code == 0
    assert "upgraded" in result.stdout.lower() or "✓" in result.stdout


def test_db_upgrade_with_revision(temp_settings_with_db: None) -> None:
    """Test database upgrade with specific revision."""
    runner = CliRunner()
    result = runner.invoke(db_app, ["upgrade", "--rev", "head"])

    assert result.exit_code == 0


def test_db_downgrade(temp_settings_with_db: None) -> None:
    """Test database downgrade command."""
    runner = CliRunner()
    # First upgrade to head
    upgrade_result = runner.invoke(db_app, ["upgrade"])
    assert upgrade_result.exit_code == 0, "Upgrade should succeed before downgrade test"
    # Then downgrade one step
    result = runner.invoke(db_app, ["downgrade", "--rev", "-1"])

    # After upgrade to head, downgrade should succeed
    assert result.exit_code == 0, f"Downgrade should succeed after upgrade. Output: {result.stdout}"


def test_db_revision(
    temp_settings_with_db: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test database revision creation."""

    def fake_revision(*_args: object, **kwargs: object) -> None:
        assert kwargs.get("message") == "test_migration"
        assert kwargs.get("autogenerate") is False

    # Avoid creating migration files in the repo during tests.
    monkeypatch.setattr(cli_db.alembic.command, "revision", fake_revision)

    runner = CliRunner()
    result = runner.invoke(db_app, ["revision", "--message", "test_migration"])

    # Revision creation should succeed
    assert result.exit_code == 0
    assert "test_migration" in result.stdout.lower() or "✓" in result.stdout


def test_db_revision_autogenerate(
    temp_settings_with_db: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test database revision with autogenerate."""

    def fake_revision(*_args: object, **kwargs: object) -> None:
        assert kwargs.get("message") == "auto_migration"
        assert kwargs.get("autogenerate") is True

    # Avoid creating migration files in the repo during tests.
    monkeypatch.setattr(cli_db.alembic.command, "revision", fake_revision)

    runner = CliRunner()
    result = runner.invoke(db_app, ["revision", "--message", "auto_migration", "--autogenerate"])

    # Should succeed (even if no changes detected)
    assert result.exit_code == 0


def test_db_dump_file_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test dump command when database file doesn't exist."""
    # Set database URL to point to non-existent file
    nonexistent_db = tmp_path / "nonexistent.db"
    db_url = f"sqlite+aiosqlite:///{nonexistent_db}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    config.get_settings.cache_clear()

    runner = CliRunner()
    result = runner.invoke(db_app, ["dump", "--out", str(tmp_path / "backup.sql")])

    # Should fail gracefully
    assert result.exit_code == 1
    assert "not found" in result.stdout.lower() or "⚠" in result.stdout


def test_db_restore_file_not_found(temp_settings_with_db: None, tmp_path: Path) -> None:
    """Test restore command when input file doesn't exist."""
    runner = CliRunner()
    result = runner.invoke(db_app, ["restore", "--in", str(tmp_path / "nonexistent.sql")])

    assert result.exit_code == 1
    assert "not found" in result.stdout.lower() or "✗" in result.stdout


def test_db_reset_no_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test reset command when database doesn't exist."""
    # Set database URL to point to non-existent file
    nonexistent_db = tmp_path / "nonexistent_test.db"
    db_url = f"sqlite+aiosqlite:///{nonexistent_db}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    config.get_settings.cache_clear()

    runner = CliRunner()
    result = runner.invoke(db_app, ["reset", "--yes"])

    # Should exit gracefully with warning
    assert result.exit_code == 0
    assert "does not exist" in result.stdout.lower() or "⚠" in result.stdout
