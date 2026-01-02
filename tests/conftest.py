"""Pytest configuration and shared fixtures.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import os
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest

from backend import config, database


@pytest.fixture(autouse=True)
def isolate_settings_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Isolate tests from developer machine config (.env and ~/.taskgenie/config.toml)."""

    # Disable implicit config file lookup.
    monkeypatch.setenv("TASKGENIE_CONFIG_FILE", str(tmp_path / "does-not-exist.toml"))

    # Disable .env loading via get_settings().
    monkeypatch.setenv("TASKGENIE_ENV_FILE", "")

    # Ensure anything that creates directories does so under tmp.
    monkeypatch.setenv("TASKGENIE_DATA_DIR", str(tmp_path / "taskgenie-data"))
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()


@pytest.fixture(autouse=True)
async def cleanup_db() -> AsyncGenerator[None, None]:
    """Ensure database is closed after each test."""
    yield
    # Cleanup after test - only if database was initialized
    if database.engine is not None:
        await database.close_db()


# Make sure any import-time Settings construction during tests doesn't read local files.
os.environ.setdefault("TASKGENIE_CONFIG_FILE", "/nonexistent/taskgenie/config.toml")
os.environ.setdefault("TASKGENIE_ENV_FILE", "")
