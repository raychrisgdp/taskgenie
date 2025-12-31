"""Tests for Notification model.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from datetime import datetime
from pathlib import Path

import alembic.command
import pytest
from sqlalchemy import text

from backend import config
from backend.cli.db import get_alembic_cfg
from backend.database import close_db, get_db, init_db
from backend.models.notification import Notification
from backend.models.task import Task


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Create a temporary database path."""
    db_path = tmp_path / "test.db"
    return db_path


@pytest.fixture
def temp_settings(temp_db_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up temporary settings for testing."""
    db_url = f"sqlite+aiosqlite:///{temp_db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    # Clear any cached settings
    config.get_settings.cache_clear()
    # Initialize database and run migrations
    init_db()

    cfg = get_alembic_cfg()
    alembic.command.upgrade(cfg, "head")


@pytest.mark.asyncio
async def test_notification_model(temp_settings: None) -> None:
    """Test Notification model creation."""
    async for session in get_db():
        # First create a task
        task = Task(id="task-for-notification", title="Task with Notification", status="pending")
        session.add(task)
        await session.commit()

        # Create notification
        notification = Notification(
            id="notification-1",
            task_id="task-for-notification",
            type="reminder",
            scheduled_at=datetime.now(),
            status="pending",
        )
        session.add(notification)
        await session.commit()

        # Verify notification was created
        result = await session.execute(
            text("SELECT * FROM notifications WHERE id = 'notification-1'")
        )
        row = result.fetchone()
        assert row is not None
        assert row[2] == "reminder"  # type is third column
        break
    await close_db()
