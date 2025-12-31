"""Tests for database CLI commands.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import importlib
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

import backend.cli.db as cli_db
from backend import config, database
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


@pytest.fixture
def temp_settings_with_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up temporary settings with initialized database."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    config.get_settings.cache_clear()
    # Initialize database
    database.init_db()


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


def test_db_get_alembic_cfg_missing_ini(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_alembic_cfg when alembic.ini doesn't exist."""
    # Mock the migrations directory to not have alembic.ini
    original_resolve = Path.resolve

    def mock_resolve(self: Path) -> Path:
        if "db.py" in str(self):
            # Return a path that doesn't have alembic.ini
            fake_backend = tmp_path / "backend"
            fake_backend.mkdir()
            (fake_backend / "migrations").mkdir()
            return fake_backend / "cli" / "db.py"
        return original_resolve(self)

    monkeypatch.setattr(Path, "resolve", mock_resolve)
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

    # Reload module to pick up new path
    importlib.reload(cli_db)
    cfg = cli_db.get_alembic_cfg()
    assert cfg is not None


def test_db_upgrade_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upgrade command error handling."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    config.get_settings.cache_clear()

    runner = CliRunner()

    # Mock alembic.command.upgrade to raise an error
    with patch("backend.cli.db.alembic.command.upgrade") as mock_upgrade:
        mock_upgrade.side_effect = Exception("Migration error")
        result = runner.invoke(db_app, ["upgrade"])
        assert result.exit_code == 1
        assert "Upgrade failed" in result.stdout or "✗" in result.stdout


def test_db_downgrade_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test downgrade command error handling."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    config.get_settings.cache_clear()

    runner = CliRunner()

    # Mock alembic.command.downgrade to raise an error
    with patch("backend.cli.db.alembic.command.downgrade") as mock_downgrade:
        mock_downgrade.side_effect = Exception("Downgrade error")
        result = runner.invoke(db_app, ["downgrade"])
        assert result.exit_code == 1
        assert "Downgrade failed" in result.stdout or "✗" in result.stdout


def test_db_revision_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test revision command error handling."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    config.get_settings.cache_clear()

    runner = CliRunner()

    # Mock alembic.command.revision to raise an error
    with patch("backend.cli.db.alembic.command.revision") as mock_revision:
        mock_revision.side_effect = Exception("Revision error")
        result = runner.invoke(db_app, ["revision", "--message", "test"])
        assert result.exit_code == 1
        assert "Revision creation failed" in result.stdout or "✗" in result.stdout


def test_db_dump_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test dump command error handling."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    config.get_settings.cache_clear()

    # Create DB file
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_text("test")

    runner = CliRunner()
    output_file = tmp_path / "backup.sql"

    # Mock sqlite3.connect to raise an error
    with patch("backend.cli.db.sqlite3.connect") as mock_connect:
        mock_connect.side_effect = Exception("Connection error")
        result = runner.invoke(db_app, ["dump", "--out", str(output_file)])
        assert result.exit_code == 1
        assert "Dump failed" in result.stdout or "✗" in result.stdout


def test_db_restore_confirmation_cancelled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test restore command when user cancels confirmation."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    config.get_settings.cache_clear()

    # Create DB file and backup file
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_text("test")
    backup_file = tmp_path / "backup.sql"
    backup_file.write_text("CREATE TABLE test (id INTEGER);")

    runner = CliRunner()
    # User cancels (input "n")
    result = runner.invoke(db_app, ["restore", "--in", str(backup_file)], input="n\n")
    assert result.exit_code == 0
    assert "cancelled" in result.stdout.lower() or "Restore cancelled" in result.stdout


def test_db_restore_confirmation_accepted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test restore command when user accepts confirmation."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    config.get_settings.cache_clear()

    # Create DB file and backup file
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_text("old data")
    backup_file = tmp_path / "backup.sql"
    backup_file.write_text("CREATE TABLE test (id INTEGER);")

    runner = CliRunner()
    # User accepts (input "y")
    result = runner.invoke(db_app, ["restore", "--in", str(backup_file)], input="y\n")
    assert result.exit_code == 0
    assert "restored" in result.stdout.lower() or "✓" in result.stdout
    # Verify old DB was deleted and new one created
    assert db_path.exists()


def test_db_restore_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test restore command error handling."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    config.get_settings.cache_clear()

    backup_file = tmp_path / "backup.sql"
    backup_file.write_text("CREATE TABLE test (id INTEGER);")

    runner = CliRunner()
    # Mock sqlite3.connect to raise an error during restore
    with patch("backend.cli.db.sqlite3.connect") as mock_connect:
        mock_connect.side_effect = Exception("Restore error")
        result = runner.invoke(db_app, ["restore", "--in", str(backup_file)], input="y\n")
        assert result.exit_code == 1
        assert "Restore failed" in result.stdout or "✗" in result.stdout


def test_db_reset_confirmation_cancelled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test reset command when user cancels confirmation."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    config.get_settings.cache_clear()

    # Create DB file
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_text("test")

    runner = CliRunner()
    # User cancels (input "n")
    result = runner.invoke(db_app, ["reset"], input="n\n")
    assert result.exit_code == 0
    assert "cancelled" in result.stdout.lower() or "Reset cancelled" in result.stdout
    assert db_path.exists()  # DB should still exist


def test_db_reset_confirmation_accepted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test reset command when user accepts confirmation."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    config.get_settings.cache_clear()

    # Create DB file
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_text("test")

    runner = CliRunner()
    # User accepts (input "y")
    result = runner.invoke(db_app, ["reset"], input="y\n")
    assert result.exit_code == 0
    assert "reset" in result.stdout.lower() or "✓" in result.stdout
    assert not db_path.exists()  # DB should be deleted


def test_db_reset_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test reset command error handling."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    config.get_settings.cache_clear()

    # Create DB file
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_text("test")

    runner = CliRunner()

    # Mock Path.unlink to raise an error
    original_unlink = Path.unlink

    def failing_unlink(self: Path) -> None:
        if self == db_path:
            raise PermissionError("Cannot delete")
        original_unlink(self)

    monkeypatch.setattr(Path, "unlink", failing_unlink)
    result = runner.invoke(db_app, ["reset", "--yes"])
    assert result.exit_code == 1
    assert "Reset failed" in result.stdout or "✗" in result.stdout
