"""Extended tests for configuration system.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from pathlib import Path

import pytest

from backend.config import Settings, _get_config_file_path, _load_toml_config


def test_get_config_file_path_from_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test getting config file path from environment variable."""
    config_file = tmp_path / "custom_config.toml"
    config_file.write_text('app_name = "CustomApp"\n')
    monkeypatch.setenv("TASKGENIE_CONFIG_FILE", str(config_file))
    path = _get_config_file_path()
    assert path == config_file


def test_get_config_file_path_nonexistent_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test getting config file path when env var points to nonexistent file."""
    monkeypatch.setenv("TASKGENIE_CONFIG_FILE", "/nonexistent/config.toml")
    path = _get_config_file_path()
    assert path is None


def test_get_config_file_path_default_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test getting default config file path when it exists."""
    default_path = tmp_path / ".taskgenie" / "config.toml"
    default_path.parent.mkdir(parents=True)
    default_path.write_text('app_name = "DefaultApp"\n')
    monkeypatch.delenv("TASKGENIE_CONFIG_FILE", raising=False)
    # Mock home directory

    original_home = Path.home
    Path.home = lambda: tmp_path  # type: ignore[assignment]
    try:
        path = _get_config_file_path()
        assert path == default_path
    finally:
        Path.home = original_home  # type: ignore[assignment]


def test_load_toml_config_valid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test loading valid TOML config."""
    config_file = tmp_path / "config.toml"
    config_file.write_text('app_name = "TOMLApp"\nnotification_schedule = ["12h"]\n')
    monkeypatch.setenv("TASKGENIE_CONFIG_FILE", str(config_file))
    config = _load_toml_config()
    assert config.get("app_name") == "TOMLApp"


def test_load_toml_config_invalid_toml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test loading invalid TOML config."""
    config_file = tmp_path / "invalid.toml"
    config_file.write_text('app_name = "Unclosed string\n')
    monkeypatch.setenv("TASKGENIE_CONFIG_FILE", str(config_file))
    config = _load_toml_config()
    # Should return empty dict on error
    assert config == {}


def test_load_toml_config_nested_structure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test loading TOML config with nested structure."""
    config_file = tmp_path / "nested.toml"
    config_file.write_text('[notifications]\nschedule = ["6h", "12h"]\n')
    monkeypatch.setenv("TASKGENIE_CONFIG_FILE", str(config_file))
    config = _load_toml_config()
    assert config.get("notification_schedule") == ["6h", "12h"]


def test_config_path_expansion(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that paths with ~ are expanded."""
    monkeypatch.setenv("TASKGENIE_DATA_DIR", "~/.test_taskgenie")
    settings = Settings(_env_file=None)
    assert "~" not in str(settings.app_data_dir)
    assert settings.app_data_dir.is_absolute()


def test_config_gmail_credentials_path_expansion(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that Gmail credentials path is expanded."""
    monkeypatch.setenv("GMAIL_CREDENTIALS_PATH", "~/credentials.json")
    settings = Settings(_env_file=None)
    assert settings.gmail_credentials_path is not None
    assert "~" not in str(settings.gmail_credentials_path)
    assert settings.gmail_credentials_path.is_absolute()


def test_config_database_url_resolved_custom_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test database URL resolution with custom path."""
    custom_path = "/custom/path/db.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{custom_path}")
    settings = Settings(_env_file=None)
    assert settings.database_url_resolved == f"sqlite+aiosqlite:///{custom_path}"
    assert settings.database_path == Path(custom_path)


def test_config_database_path_from_url_relative(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test database path extraction from relative URL."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///relative.db")
    settings = Settings(_env_file=None)
    assert settings.database_path == Path("relative.db")


def test_config_database_path_from_url_absolute(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test database path extraction from absolute URL."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:////absolute/path.db")
    settings = Settings(_env_file=None)
    assert settings.database_path == Path("/absolute/path.db")


def test_config_notification_schedule_json_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that NOTIFICATION_SCHEDULE parses JSON list from env var."""
    monkeypatch.setenv("NOTIFICATION_SCHEDULE", '["24h", "6h", "1h"]')
    settings = Settings(_env_file=None)
    assert settings.notification_schedule == ["24h", "6h", "1h"]
