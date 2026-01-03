"""Application configuration settings.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import logging
import os
import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import PydanticBaseSettingsSource

logger = logging.getLogger(__name__)


def _get_config_file_path() -> Path | None:
    """Get config file path from env var or default location.

    Returns:
        Path to config file if it exists, None otherwise.
    """
    config_file = os.getenv("TASKGENIE_CONFIG_FILE")
    if config_file:
        path = Path(config_file).expanduser()
        if path.exists():
            return path
        return None

    default_path = Path.home() / ".taskgenie" / "config.toml"
    if default_path.exists():
        return default_path

    return None


def _flatten_toml_data(data: dict[str, Any]) -> dict[str, Any]:
    """Flatten nested TOML structure for Pydantic Settings.

    TOML files can have nested structures (e.g., `[notifications] schedule = [...]`),
    but Pydantic Settings expects flat field names (e.g., `notification_schedule`).

    This function handles the mapping:
    - Uses explicit mapping table for known nested keys
      (e.g., `notifications.schedule` → `notification_schedule`)
    - Falls back to underscore-separated keys for other nested structures
      (e.g., `app.name` → `app_name`)

    Args:
        data: Nested TOML data dictionary.

    Returns:
        Flattened dictionary with underscore-separated keys.

    Note:
        The `field_name_mapping` dictionary is intentionally hardcoded for MVP.
        If more nested TOML keys are needed, add them to this mapping table.
    """
    # Explicit mapping of TOML nested keys to Settings field names.
    # This is intentional and documented. If more nested keys are needed,
    # add them here rather than relying on automatic underscore flattening.
    # Example: {"notifications": {"schedule": [...]}} → {"notification_schedule": [...]}
    field_name_mapping: dict[str, dict[str, str]] = {"notifications": {"schedule": "notification_schedule"}}

    flattened: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                # Use mapping if available, otherwise flatten with underscore
                mapped_key = field_name_mapping.get(key, {}).get(subkey)
                if mapped_key:
                    flattened[mapped_key] = subvalue
                else:
                    flattened[f"{key}_{subkey}"] = subvalue
        else:
            flattened[key] = value
    return flattened


def _load_toml_config() -> dict[str, Any]:
    """Load TOML config file if it exists.

    Returns:
        Dictionary of config values from TOML file, empty dict if not found.
    """
    config_path = _get_config_file_path()
    if not config_path:
        return {}

    try:
        with config_path.open("rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        logger.warning("Failed to parse TOML config at %s: %s", config_path, exc)
        return {}
    except OSError as exc:
        logger.warning("Failed to read TOML config at %s: %s", config_path, exc)
        return {}

    return _flatten_toml_data(data)


class TaskGenieTomlSettingsSource(PydanticBaseSettingsSource):
    """Settings source for ~/.taskgenie/config.toml (lowest precedence)."""

    def get_field_value(self, field: Any, field_name: str) -> tuple[Any, str, bool]:
        # Nothing to do here; __call__ returns the pre-loaded dict.
        return None, "", False

    def __call__(self) -> dict[str, Any]:
        return _load_toml_config()


class Settings(BaseSettings):
    """Application settings.

    Precedence order: init_settings → env vars → .env → config.toml →
    file_secret_settings → defaults.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", populate_by_name=True)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Set settings source precedence (highest to lowest)."""
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            TaskGenieTomlSettingsSource(settings_cls),
            file_secret_settings,
        )

    # App metadata
    app_name: str = Field(default="TaskGenie", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")

    # App data directory (canonical location)
    app_data_dir: Path = Field(default_factory=lambda: Path.home() / ".taskgenie", alias="TASKGENIE_DATA_DIR")

    # Database
    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    # Server
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8080, alias="PORT")

    # LLM
    llm_provider: str = Field(default="openrouter", alias="LLM_PROVIDER")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")
    llm_model: str = Field(default="anthropic/claude-3-haiku", alias="LLM_MODEL")

    # Integrations
    gmail_enabled: bool = Field(default=False, alias="GMAIL_ENABLED")
    gmail_credentials_path: Path | None = Field(default=None, alias="GMAIL_CREDENTIALS_PATH")

    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")
    github_username: str | None = Field(default=None, alias="GITHUB_USERNAME")

    # Notifications
    notifications_enabled: bool = Field(default=True, alias="NOTIFICATIONS_ENABLED")
    notification_schedule: list[str] = Field(default_factory=lambda: ["24h", "6h"], alias="NOTIFICATION_SCHEDULE")

    @field_validator("app_data_dir", mode="before")
    @classmethod
    def expand_app_data_dir(cls, v: str | Path) -> Path:
        """Expand user home directory in app_data_dir path."""
        if isinstance(v, str):
            return Path(v).expanduser()
        return Path(v).expanduser()

    @field_validator("gmail_credentials_path", mode="before")
    @classmethod
    def expand_gmail_credentials_path(cls, v: str | Path | None) -> Path | None:
        """Expand user home directory in gmail_credentials_path."""
        if v is None:
            return None
        if isinstance(v, str):
            return Path(v).expanduser()
        return Path(v).expanduser()

    def ensure_app_dirs(self) -> None:
        """Create canonical app directories (data/logs/cache).

        Avoid calling this at import time; prefer calling once at app/CLI startup.
        """
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        (self.app_data_dir / "data").mkdir(parents=True, exist_ok=True)
        (self.app_data_dir / "logs").mkdir(parents=True, exist_ok=True)
        (self.app_data_dir / "cache").mkdir(parents=True, exist_ok=True)
        (self.app_data_dir / "cache" / "attachments").mkdir(parents=True, exist_ok=True)
        self.vector_store_path.mkdir(parents=True, exist_ok=True)

        database_path = self.database_path
        if str(database_path) != ":memory:":
            database_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def database_path(self) -> Path:
        """Get canonical database file path.

        Strips query parameters (e.g., ?mode=ro) from the URL before extracting the path.
        """
        if self.database_url and self.database_url.startswith("sqlite"):
            # Strip query parameters (e.g., ?mode=ro) before extracting path
            url = self.database_url.split("?")[0] if "?" in self.database_url else self.database_url
            # Extract path from sqlite:///path/to/db or sqlite+aiosqlite:///path/to/db
            if "://" in url:
                url_path = url.split(":///", 1)[-1] if ":///" in url else url.split("://", 1)[-1]
                if url_path.startswith("/") or (len(url_path) > 1 and url_path[1] == ":"):
                    return Path(url_path)
                return Path(url_path)
        # Default to app_data_dir/data/taskgenie.db
        return self.app_data_dir / "data" / "taskgenie.db"

    @property
    def database_url_resolved(self) -> str:
        """Get resolved database URL (with default if not set)."""
        if self.database_url:
            return self.database_url
        # Default: use canonical path
        db_path = self.database_path
        return f"sqlite+aiosqlite:///{db_path}"

    @property
    def vector_store_path(self) -> Path:
        """Get canonical vector store (ChromaDB) path."""
        return self.app_data_dir / "data" / "chroma"

    @property
    def attachment_cache_path(self) -> Path:
        """Get canonical attachment cache path."""
        return self.app_data_dir / "cache" / "attachments"

    @property
    def logs_path(self) -> Path:
        """Get canonical logs directory path."""
        return self.app_data_dir / "logs"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Note: Changing TASKGENIE_ENV_FILE environment variable between calls
    will return cached settings. Use cache_clear() to force reinitialization.

    Implementation note:
        This function uses `_env_file`, which is an internal parameter in
        pydantic-settings that allows overriding the env file path at runtime.
        This is not part of the public API but is the only way to dynamically
        set the env file based on TASKGENIE_ENV_FILE. If pydantic-settings
        adds a supported public API for this in the future, we should migrate
        to that approach.
    """
    env_file = os.getenv("TASKGENIE_ENV_FILE", ".env")
    # _env_file is a valid internal parameter in pydantic-settings but not recognized by mypy
    return Settings(_env_file=env_file or None)  # type: ignore[call-arg]


def __getattr__(name: str) -> Any:
    """Lazy attribute access for backward compatibility."""
    if name == "settings":
        return get_settings()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
