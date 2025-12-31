"""Tests for configuration system.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from pathlib import Path

import pytest

from backend.config import Settings


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
