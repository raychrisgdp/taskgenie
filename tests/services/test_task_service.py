"""Integration tests for task service layer.

These tests call the service functions directly with real database sessions
to ensure coverage tracks properly.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.task import TaskCreate, TaskPriority, TaskStatus, TaskUpdate
from backend.services.task_service import TaskNotFoundError, create_task, delete_task, get_task, list_tasks, update_task


@pytest.fixture
async def db_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AsyncSession:
    """Create a real database session for testing."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    # Clear config cache
    from backend import config  # noqa: PLC0415

    config.get_settings.cache_clear()

    # Initialize database
    from backend.database import init_db_async, get_db  # noqa: PLC0415

    await init_db_async()

    # Get a session
    async for session in get_db():
        yield session
        break


@pytest.mark.asyncio
async def test_create_task_service(db_session: AsyncSession) -> None:
    """Test create_task service function directly."""
    task_data = TaskCreate(
        title="Service Test Task",
        description="Service Test Description",
        status=TaskStatus.PENDING,
        priority=TaskPriority.HIGH,
    )

    result = await create_task(db_session, task_data)
    await db_session.commit()

    assert result.title == "Service Test Task"
    assert result.description == "Service Test Description"
    assert result.status == TaskStatus.PENDING
    assert result.priority == TaskPriority.HIGH
    assert result.id is not None


@pytest.mark.asyncio
async def test_get_task_service(db_session: AsyncSession) -> None:
    """Test get_task service function directly."""
    # Create a task first
    task_data = TaskCreate(title="Get Test Task", status=TaskStatus.PENDING, priority=TaskPriority.MEDIUM)
    created_task = await create_task(db_session, task_data)
    await db_session.commit()

    # Get the task
    result = await get_task(db_session, created_task.id)

    assert result.id == created_task.id
    assert result.title == "Get Test Task"


@pytest.mark.asyncio
async def test_get_task_service_not_found(db_session: AsyncSession) -> None:
    """Test get_task raises TaskNotFoundError when task not found."""
    with pytest.raises(TaskNotFoundError) as exc_info:
        await get_task(db_session, "nonexistent-id")

    assert exc_info.value.task_id == "nonexistent-id"
    assert exc_info.value.code == "TASK_NOT_FOUND"


@pytest.mark.asyncio
async def test_list_tasks_service(db_session: AsyncSession) -> None:
    """Test list_tasks service function directly."""
    # Create multiple tasks
    for i in range(5):
        task_data = TaskCreate(title=f"Task {i}", status=TaskStatus.PENDING, priority=TaskPriority.MEDIUM)
        await create_task(db_session, task_data)
    await db_session.commit()

    # List tasks
    result = await list_tasks(db_session, limit=10, offset=0)

    assert result.total == 5  # noqa: PLR2004
    assert len(result.tasks) == 5  # noqa: PLR2004
    assert result.page == 1
    assert result.page_size == 10  # noqa: PLR2004


@pytest.mark.asyncio
async def test_list_tasks_service_with_filters(db_session: AsyncSession) -> None:
    """Test list_tasks with all filters applied."""
    # Create tasks with different attributes
    now = datetime.now(UTC)
    eta1 = now.replace(hour=10, minute=0, second=0, microsecond=0)
    eta2 = now.replace(hour=14, minute=0, second=0, microsecond=0)
    eta3 = now.replace(hour=11, minute=0, second=0, microsecond=0)

    task1_data = TaskCreate(
        title="Task 1", status=TaskStatus.PENDING, priority=TaskPriority.HIGH, eta=eta1
    )
    task2_data = TaskCreate(
        title="Task 2", status=TaskStatus.COMPLETED, priority=TaskPriority.LOW, eta=eta2
    )
    task3_data = TaskCreate(
        title="Task 3", status=TaskStatus.PENDING, priority=TaskPriority.HIGH, eta=eta3
    )

    await create_task(db_session, task1_data)
    await create_task(db_session, task2_data)
    await create_task(db_session, task3_data)
    await db_session.commit()

    # Filter with all parameters: pending, high priority, due after 10:30am and before noon
    # This will exclude Task 1 (10am) but include Task 3 (11am)
    after_eta1 = now.replace(hour=10, minute=30, second=0, microsecond=0)
    noon = now.replace(hour=12, minute=0, second=0, microsecond=0)
    result = await list_tasks(
        db_session,
        status="pending",
        priority="high",
        due_before=noon,
        due_after=after_eta1,
        limit=10,
        offset=0,
    )

    # Should match Task 3 (pending, high, eta=eta3 which is after 10:30am and before noon)
    assert result.total == 1
    assert len(result.tasks) == 1
    assert result.tasks[0].title == "Task 3"


@pytest.mark.asyncio
async def test_list_tasks_service_pagination(db_session: AsyncSession) -> None:
    """Test list_tasks pagination calculation."""
    # Create 10 tasks
    for i in range(10):  # noqa: PLR2004
        task_data = TaskCreate(title=f"Task {i}", status=TaskStatus.PENDING, priority=TaskPriority.MEDIUM)
        await create_task(db_session, task_data)
    await db_session.commit()

    # Test pagination: offset=6, limit=3 -> page 3
    result = await list_tasks(db_session, limit=3, offset=6)

    assert result.total == 10  # noqa: PLR2004
    assert result.page == 3  # (6 // 3) + 1 = 3
    assert result.page_size == 3  # noqa: PLR2004


@pytest.mark.asyncio
async def test_update_task_service(db_session: AsyncSession) -> None:
    """Test update_task service function directly."""
    # Create a task
    task_data = TaskCreate(
        title="Original Title",
        description="Original Description",
        status=TaskStatus.PENDING,
        priority=TaskPriority.LOW,
    )
    created_task = await create_task(db_session, task_data)
    await db_session.commit()

    # Update the task
    update_data = TaskUpdate(
        title="Updated Title",
        description="Updated Description",
        status=TaskStatus.COMPLETED,
        priority=TaskPriority.HIGH,
    )
    result = await update_task(db_session, created_task.id, update_data)
    await db_session.commit()

    assert result.title == "Updated Title"
    assert result.description == "Updated Description"
    assert result.status == TaskStatus.COMPLETED
    assert result.priority == TaskPriority.HIGH


@pytest.mark.asyncio
async def test_update_task_service_all_fields(db_session: AsyncSession) -> None:
    """Test update_task with all fields updated."""
    # Create a task
    task_data = TaskCreate(
        title="Original",
        description="Original Desc",
        status=TaskStatus.PENDING,
        priority=TaskPriority.LOW,
        tags=["old_tag"],
        metadata={"old": "value"},
    )
    created_task = await create_task(db_session, task_data)
    await db_session.commit()

    # Update all fields
    eta_dt = datetime.now(UTC)
    update_data = TaskUpdate(
        title="Updated",
        description="Updated Desc",
        status=TaskStatus.IN_PROGRESS,
        priority=TaskPriority.CRITICAL,
        eta=eta_dt,
        tags=["new_tag1", "new_tag2"],
        metadata={"new": "value"},
    )
    result = await update_task(db_session, created_task.id, update_data)
    await db_session.commit()

    assert result.title == "Updated"
    assert result.description == "Updated Desc"
    assert result.status == TaskStatus.IN_PROGRESS
    assert result.priority == TaskPriority.CRITICAL
    assert result.tags == ["new_tag1", "new_tag2"]
    assert result.metadata == {"new": "value"}


@pytest.mark.asyncio
async def test_update_task_service_not_found(db_session: AsyncSession) -> None:
    """Test update_task raises TaskNotFoundError when task not found."""
    update_data = TaskUpdate(title="Updated Title")

    with pytest.raises(TaskNotFoundError) as exc_info:
        await update_task(db_session, "nonexistent-id", update_data)

    assert exc_info.value.task_id == "nonexistent-id"
    assert exc_info.value.code == "TASK_NOT_FOUND"


@pytest.mark.asyncio
async def test_update_task_service_only_optional_fields(db_session: AsyncSession) -> None:
    """Test update_task with only optional fields (eta, tags, metadata) to cover branch paths."""
    # Create a task with initial values
    task_data = TaskCreate(
        title="Original Title",
        description="Original Description",
        status=TaskStatus.PENDING,
        priority=TaskPriority.LOW,
    )
    created_task = await create_task(db_session, task_data)
    await db_session.commit()

    # Update only optional fields (not status, priority, title, or description)
    # This covers the False branches of those conditionals
    eta_dt = datetime.now(UTC)
    update_data = TaskUpdate(eta=eta_dt, tags=["tag1"], metadata={"key": "value"})
    result = await update_task(db_session, created_task.id, update_data)
    await db_session.commit()

    # Verify optional fields updated
    assert result.eta is not None
    assert result.tags == ["tag1"]
    assert result.metadata == {"key": "value"}
    # Verify required fields unchanged
    assert result.title == "Original Title"
    assert result.description == "Original Description"
    assert result.status == TaskStatus.PENDING
    assert result.priority == TaskPriority.LOW


@pytest.mark.asyncio
async def test_delete_task_service(db_session: AsyncSession) -> None:
    """Test delete_task service function directly."""
    # Create a task
    task_data = TaskCreate(title="Task to Delete", status=TaskStatus.PENDING, priority=TaskPriority.MEDIUM)
    created_task = await create_task(db_session, task_data)
    await db_session.commit()

    # Delete the task
    await delete_task(db_session, created_task.id)
    await db_session.commit()

    # Verify task is deleted
    with pytest.raises(TaskNotFoundError):
        await get_task(db_session, created_task.id)


@pytest.mark.asyncio
async def test_delete_task_service_not_found(db_session: AsyncSession) -> None:
    """Test delete_task raises TaskNotFoundError when task not found."""
    with pytest.raises(TaskNotFoundError) as exc_info:
        await delete_task(db_session, "nonexistent-id")

    assert exc_info.value.task_id == "nonexistent-id"
    assert exc_info.value.code == "TASK_NOT_FOUND"
