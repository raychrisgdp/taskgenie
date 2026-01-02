"""Tests for Task model.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from pathlib import Path

import alembic.command
import pytest
from sqlalchemy import text

from backend import config
from backend.cli.db import get_alembic_cfg
from backend.database import close_db, get_db, init_db
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
async def test_task_model(temp_settings: None) -> None:
    """Test Task model creation and retrieval."""
    async for session in get_db():
        task = Task(
            id="test-task-1",
            title="Test Task",
            description="Test Description",
            status="pending",
            priority="high",
            tags=["test", "example"],
            meta_data={"key": "value"},
        )
        session.add(task)
        await session.commit()

        # Retrieve task
        result = await session.execute(text("SELECT * FROM tasks WHERE id = 'test-task-1'"))
        row = result.fetchone()
        assert row is not None
        assert row[1] == "Test Task"  # title is second column
        break
    await close_db()


@pytest.mark.asyncio
async def test_task_cascade_delete(temp_settings: None) -> None:
    """Test that deleting a task cascades to attachments and notifications."""
    from backend.models.attachment import Attachment  # noqa: PLC0415
    from backend.models.notification import Notification  # noqa: PLC0415

    async for session in get_db():
        # Create task with attachment and notification
        task = Task(id="task-to-delete", title="Task to Delete", status="pending")
        session.add(task)
        await session.commit()

        attachment = Attachment(
            id="attachment-to-delete", task_id="task-to-delete", type="url", reference="https://example.com"
        )
        session.add(attachment)

        from datetime import datetime  # noqa: PLC0415

        notification = Notification(
            id="notification-to-delete", task_id="task-to-delete", type="reminder", scheduled_at=datetime.now()
        )
        session.add(notification)
        await session.commit()

        # Delete task
        await session.execute(text("DELETE FROM tasks WHERE id = 'task-to-delete'"))
        await session.commit()

        # Verify cascade delete
        result = await session.execute(text("SELECT COUNT(*) FROM attachments WHERE task_id = 'task-to-delete'"))
        attachment_count = result.scalar()
        assert attachment_count == 0

        result = await session.execute(text("SELECT COUNT(*) FROM notifications WHERE task_id = 'task-to-delete'"))
        notification_count = result.scalar()
        assert notification_count == 0
        break
    await close_db()
