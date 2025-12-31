"""Tests for configuration system.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from pathlib import Path

import pytest

from backend import config
from backend.config import Settings, _flatten_toml_data, _get_config_file_path, _load_toml_config


def test_config_precedence_env_var_overrides_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that environment variables override defaults."""
    monkeypatch.setenv("APP_NAME", "TestApp")
    settings = Settings(_env_file=None)
    assert settings.app_name == "TestApp"


def test_config_precedence_toml_overrides_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that TOML config file overrides defaults."""
    config_file = tmp_path / "config.toml"
    config_file.write_text('app_name = "TOMLApp"\n')

    monkeypatch.setenv("TASKGENIE_CONFIG_FILE", str(config_file))
    settings = Settings(_env_file=None)
    assert settings.app_name == "TOMLApp"


def test_config_precedence_env_overrides_toml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that environment variables override TOML config."""
    config_file = tmp_path / "config.toml"
    config_file.write_text('app_name = "TOMLApp"\n')

    monkeypatch.setenv("TASKGENIE_CONFIG_FILE", str(config_file))
    monkeypatch.setenv("APP_NAME", "EnvApp")
    settings = Settings(_env_file=None)
    assert settings.app_name == "EnvApp"


def test_app_data_dir_creation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that app data directories can be created explicitly."""
    data_dir = tmp_path / "test_taskgenie"
    monkeypatch.setenv("TASKGENIE_DATA_DIR", str(data_dir))
    settings = Settings(_env_file=None)
    settings.ensure_app_dirs()
    assert settings.app_data_dir.exists()
    assert (settings.app_data_dir / "data").exists()
    assert (settings.app_data_dir / "logs").exists()
    assert (settings.app_data_dir / "cache" / "attachments").exists()


def test_database_url_resolved_default() -> None:
    """Test that database URL is resolved with default path."""
    settings = Settings(_env_file=None)
    assert settings.database_url_resolved.startswith("sqlite+aiosqlite:///")
    assert "taskgenie.db" in settings.database_url_resolved


def test_database_url_resolved_custom(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that custom database URL is used if provided."""
    custom_url = "sqlite+aiosqlite:///custom.db"
    monkeypatch.setenv("DATABASE_URL", custom_url)
    settings = Settings(_env_file=None)
    assert settings.database_url_resolved == custom_url


def test_path_properties() -> None:
    """Test that path properties return correct Path objects."""
    settings = Settings(_env_file=None)
    assert isinstance(settings.database_path, Path)
    assert isinstance(settings.vector_store_path, Path)
    assert isinstance(settings.attachment_cache_path, Path)
    assert isinstance(settings.logs_path, Path)


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


def test_config_get_config_file_path_nonexistent_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _get_config_file_path when env var points to nonexistent file."""
    monkeypatch.setenv("TASKGENIE_CONFIG_FILE", "/nonexistent/path.toml")
    from backend.config import _get_config_file_path  # noqa: PLC0415

    path = _get_config_file_path()
    assert path is None


def test_config_get_config_file_path_no_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _get_config_file_path when no config file exists."""
    monkeypatch.delenv("TASKGENIE_CONFIG_FILE", raising=False)
    from backend.config import _get_config_file_path  # noqa: PLC0415

    # Mock Path.home to return a path without config.toml
    original_home = Path.home
    tmp_path = Path("/tmp/test_no_config")
    Path.home = lambda: tmp_path  # type: ignore[assignment]
    try:
        path = _get_config_file_path()
        assert path is None
    finally:
        Path.home = original_home  # type: ignore[assignment]


def test_config_flatten_toml_with_mapping() -> None:
    """Test _flatten_toml_data with mapping."""

    data = {"notifications": {"schedule": ["6h", "12h"]}}
    flattened = _flatten_toml_data(data)
    assert flattened["notification_schedule"] == ["6h", "12h"]


def test_config_flatten_toml_without_mapping() -> None:
    """Test _flatten_toml_data without mapping."""

    data = {"app": {"name": "Test"}}
    flattened = _flatten_toml_data(data)
    assert flattened["app_name"] == "Test"


def test_config_load_toml_os_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _load_toml_config with OSError (covers lines 89-91)."""
    from unittest.mock import patch

    config_file = tmp_path / "config.toml"
    config_file.write_text('app_name = "Test"')  # Create file first
    monkeypatch.setenv("TASKGENIE_CONFIG_FILE", str(config_file))

    # Mock Path.open to raise OSError when reading
    with patch.object(Path, "open", side_effect=OSError("Permission denied")):
        config = _load_toml_config()
        assert config == {}


def test_config_expand_gmail_credentials_path_path_object(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test expand_gmail_credentials_path when v is a Path object (line 179)."""
    from pathlib import Path  # noqa: PLC0415

    from backend.config import Settings  # noqa: PLC0415

    # Test that when a Path object is passed, validator calls Path(v).expanduser()
    # This covers line 179: return Path(v).expanduser()
    path_obj = Path("~/test_credentials.json")
    # Pass Path object directly to constructor - validator should be called
    settings = Settings(_env_file=None, gmail_credentials_path=path_obj)
    # The validator at line 179 should expand the Path
    assert settings.gmail_credentials_path is not None
    # Verify it was expanded (the validator should call expanduser on the Path)
    expected_expanded = Path("~/test_credentials.json").expanduser()
    # The validator converts Path to Path and calls expanduser, so ~ should be expanded
    assert settings.gmail_credentials_path == expected_expanded


def test_config_toml_settings_source_get_field_value() -> None:
    """Test TaskGenieTomlSettingsSource.get_field_value."""
    from backend.config import Settings, TaskGenieTomlSettingsSource  # noqa: PLC0415

    source = TaskGenieTomlSettingsSource(Settings)
    result = source.get_field_value(None, "test")
    assert result == (None, "", False)


def test_config_settings_ensure_app_dirs_memory_db(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test ensure_app_dirs with :memory: database."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    from backend.config import Settings  # noqa: PLC0415

    settings = Settings(_env_file=None)
    settings.ensure_app_dirs()
    # Should not raise error even with :memory: DB
    assert settings.app_data_dir.exists()


def test_config_get_settings_with_env_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test get_settings with custom env file."""
    env_file = tmp_path / ".env.test"
    env_file.write_text("APP_NAME=TestApp\n")
    monkeypatch.setenv("TASKGENIE_ENV_FILE", str(env_file))
    config.get_settings.cache_clear()

    settings = config.get_settings()
    assert settings.app_name == "TestApp"


def test_config_database_path_memory() -> None:
    """Test database_path property with :memory: URL."""
    from backend.config import Settings  # noqa: PLC0415

    settings = Settings(_env_file=None)
    # Set database_url to :memory:
    settings.database_url = "sqlite+aiosqlite:///:memory:"
    db_path = settings.database_path
    # The current implementation returns :memory: as-is, which is correct
    # The ensure_app_dirs method checks for :memory: and skips directory creation
    assert db_path == Path(":memory:")


def test_config_database_url_resolved_with_url() -> None:
    """Test database_url_resolved when database_url is set."""
    from backend.config import Settings  # noqa: PLC0415

    custom_url = "sqlite+aiosqlite:///custom.db"
    settings = Settings(_env_file=None)
    settings.database_url = custom_url
    assert settings.database_url_resolved == custom_url


def test_config_database_path_without_sqlite() -> None:
    """Test database_path property when URL is not sqlite (covers line 201->211)."""
    from backend.config import Settings  # noqa: PLC0415

    settings = Settings(_env_file=None)
    settings.database_url = "postgresql://user:pass@localhost/db"
    # Should return default path when not sqlite (covers the else branch)
    db_path = settings.database_path
    assert "taskgenie.db" in str(db_path)


def test_config_database_path_sqlite_without_url() -> None:
    """Test database_path when database_url starts with sqlite but has no ://."""
    from backend.config import Settings  # noqa: PLC0415

    settings = Settings(_env_file=None)
    # Set a sqlite URL without :// (should hit the else branch at line 201->211)
    settings.database_url = "sqlite+aiosqlite"
    db_path = settings.database_path
    # Should return default path
    assert "taskgenie.db" in str(db_path)


def test_config_database_path_url_without_triple_slash() -> None:
    """Test database_path with sqlite URL without triple slash."""
    from backend.config import Settings  # noqa: PLC0415

    settings = Settings(_env_file=None)
    settings.database_url = "sqlite://relative.db"
    db_path = settings.database_path
    assert db_path == Path("relative.db")


def test_config_database_path_absolute_windows() -> None:
    """Test database_path with Windows absolute path."""
    from backend.config import Settings  # noqa: PLC0415

    settings = Settings(_env_file=None)
    settings.database_url = "sqlite+aiosqlite:///C:/path/to/db.sqlite"
    db_path = settings.database_path
    assert db_path == Path("C:/path/to/db.sqlite")


def test_config_expand_gmail_credentials_path_with_path() -> None:
    """Test expand_gmail_credentials_path when v is already a Path."""
    from pathlib import Path  # noqa: PLC0415

    from backend.config import Settings  # noqa: PLC0415

    settings = Settings(_env_file=None)
    # Set gmail_credentials_path to a Path object
    path_obj = Path("/absolute/path/credentials.json")
    settings.gmail_credentials_path = path_obj
    # Should expand user if needed, but Path objects are already expanded
    assert settings.gmail_credentials_path == path_obj


def test_config_module_getattr_settings() -> None:
    """Test config module __getattr__ returns settings (line 252)."""
    import backend.config  # noqa: PLC0415

    # Clear any cached settings attribute if it exists
    try:
        delattr(backend.config, "settings")
    except AttributeError:
        pass  # Attribute doesn't exist yet, which is fine

    # Access settings via __getattr__ (covers line 252)
    settings = backend.config.settings
    assert settings is not None
    assert hasattr(settings, "app_name")


def test_config_module_getattr_error() -> None:
    """Test config module __getattr__ raises AttributeError for invalid attribute (line 253)."""
    import backend.config  # noqa: PLC0415

    with pytest.raises(AttributeError, match="module 'backend.config' has no attribute 'invalid'"):
        _ = backend.config.invalid  # noqa: F841
