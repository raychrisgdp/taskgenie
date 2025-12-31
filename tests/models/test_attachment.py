"""Tests for Attachment model.

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
from backend.models.attachment import Attachment
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
async def test_attachment_model(temp_settings: None) -> None:
    """Test Attachment model creation."""
    async for session in get_db():
        # First create a task
        task = Task(id="task-for-attachment", title="Task with Attachment", status="pending")
        session.add(task)
        await session.commit()

        # Create attachment
        attachment = Attachment(
            id="attachment-1",
            task_id="task-for-attachment",
            type="url",
            reference="https://example.com",
            title="Example Link",
            content="Some content",
            meta_data={"source": "test"},
        )
        session.add(attachment)
        await session.commit()

        # Verify attachment was created
        result = await session.execute(text("SELECT * FROM attachments WHERE id = 'attachment-1'"))
        row = result.fetchone()
        assert row is not None
        assert row[2] == "url"  # type is third column
        break
    await close_db()
