"""Task service layer for business logic.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from backend.models.task import Task
from backend.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate


def _apply_task_filters(
    query: Select[Any],
    status: str | None = None,
    priority: str | None = None,
    due_before: datetime | None = None,
    due_after: datetime | None = None,
) -> Select[Any]:
    """Apply filter conditions to a task query.

    Args:
        query: SQLAlchemy select query to filter.
        status: Filter by status.
        priority: Filter by priority.
        due_before: Filter tasks with eta before this datetime.
        due_after: Filter tasks with eta after this datetime.

    Returns:
        Filtered query.
    """
    if status is not None:
        query = query.where(Task.status == status)
    if priority is not None:
        query = query.where(Task.priority == priority)
    if due_before is not None:
        query = query.where(Task.eta <= due_before)
    if due_after is not None:
        query = query.where(Task.eta >= due_after)
    return query


def _task_to_response_dict(task: Task) -> dict[str, Any]:
    """Convert Task model to dict for TaskResponse validation.

    Args:
        task: Task model instance.

    Returns:
        dict: Task data as dict with metadata mapped correctly.
    """
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "eta": task.eta,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "tags": task.tags,
        "meta_data": task.meta_data,
        "attachments": [],
    }


class TaskNotFoundError(Exception):
    """Exception raised when a task is not found."""

    def __init__(self, task_id: str) -> None:
        """Initialize TaskNotFoundError.

        Args:
            task_id: The ID of the task that was not found.
        """
        self.task_id = task_id
        self.code = "TASK_NOT_FOUND"
        self.message = f"Task not found: {task_id}"
        super().__init__(self.message)


async def create_task(session: AsyncSession, task_data: TaskCreate) -> TaskResponse:
    """Create a new task.

    Args:
        session: Database session.
        task_data: Task creation data.

    Returns:
        TaskResponse: Created task.
    """
    task_id = str(uuid.uuid4())
    task = Task(
        id=task_id,
        title=task_data.title,
        description=task_data.description,
        status=task_data.status.value,
        priority=task_data.priority.value,
        eta=task_data.eta,
        tags=task_data.tags,
        meta_data=task_data.metadata,
    )
    session.add(task)
    await session.flush()
    await session.refresh(task)
    return TaskResponse.model_validate(_task_to_response_dict(task))


async def get_task(session: AsyncSession, task_id: str) -> TaskResponse:
    """Get a task by ID.

    Args:
        session: Database session.
        task_id: Task ID.

    Returns:
        TaskResponse: Task data.

    Raises:
        TaskNotFoundError: If task is not found.
    """
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise TaskNotFoundError(task_id)
    return TaskResponse.model_validate(_task_to_response_dict(task))


async def list_tasks(
    session: AsyncSession,
    status: str | None = None,
    priority: str | None = None,
    due_before: datetime | None = None,
    due_after: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> TaskListResponse:
    """List tasks with filtering and pagination.

    Args:
        session: Database session.
        status: Filter by status.
        priority: Filter by priority.
        due_before: Filter tasks with eta before this datetime.
        due_after: Filter tasks with eta after this datetime.
        limit: Maximum number of results.
        offset: Pagination offset.

    Returns:
        TaskListResponse: Paginated task list.
    """
    query = select(Task)

    # Apply filters
    query = _apply_task_filters(query, status, priority, due_before, due_after)

    # Get total count with same filters
    # Build count query with same filters but without ordering/pagination
    count_query = select(func.count(Task.id))
    count_query = _apply_task_filters(count_query, status, priority, due_before, due_after)
    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    # Apply ordering and pagination
    query = query.order_by(Task.created_at.desc(), Task.id.asc())
    query = query.limit(limit).offset(offset)

    # Execute query
    result = await session.execute(query)
    tasks = result.scalars().all()

    # Calculate page and page_size
    page = (offset // limit) + 1
    page_size = limit

    # Convert tasks to TaskResponse, excluding relationships
    task_responses = [TaskResponse.model_validate(_task_to_response_dict(task)) for task in tasks]

    return TaskListResponse(tasks=task_responses, total=total, page=page, page_size=page_size)


async def update_task(session: AsyncSession, task_id: str, task_data: TaskUpdate) -> TaskResponse:
    """Update a task.

    Args:
        session: Database session.
        task_id: Task ID.
        task_data: Task update data.

    Returns:
        TaskResponse: Updated task.

    Raises:
        TaskNotFoundError: If task is not found.
    """
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise TaskNotFoundError(task_id)

    # Update fields (only set provided fields)
    update_dict = task_data.model_dump(exclude_unset=True)
    if "status" in update_dict and update_dict["status"] is not None:
        task.status = update_dict["status"].value
    if "priority" in update_dict and update_dict["priority"] is not None:
        task.priority = update_dict["priority"].value
    if "title" in update_dict:
        task.title = update_dict["title"]
    if "description" in update_dict:
        task.description = update_dict["description"]
    if "eta" in update_dict:
        task.eta = update_dict["eta"]
    if "tags" in update_dict:
        task.tags = update_dict["tags"]
    if "metadata" in update_dict:
        task.meta_data = update_dict["metadata"]

    await session.flush()
    await session.refresh(task)
    return TaskResponse.model_validate(_task_to_response_dict(task))


async def delete_task(session: AsyncSession, task_id: str) -> None:
    """Delete a task.

    Args:
        session: Database session.
        task_id: Task ID.

    Raises:
        TaskNotFoundError: If task is not found.
    """
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise TaskNotFoundError(task_id)
    await session.delete(task)
    await session.flush()
