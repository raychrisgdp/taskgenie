"""Task API endpoints.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas.task import TaskCreate, TaskListResponse, TaskPriority, TaskResponse, TaskStatus, TaskUpdate
from backend.services.task_service import create_task, delete_task, get_task, list_tasks, update_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task_endpoint(task_data: TaskCreate, session: AsyncSession = Depends(get_db)) -> TaskResponse:
    """Create a new task.

    Args:
        task_data: Task creation data.
        session: Database session.

    Returns:
        TaskResponse: Created task.
    """
    return await create_task(session, task_data)


@router.get("", response_model=TaskListResponse)
async def list_tasks_endpoint(
    status: TaskStatus | None = Query(None, description="Filter by status"),
    priority: TaskPriority | None = Query(None, description="Filter by priority"),
    due_before: datetime | None = Query(None, description="Filter tasks due before this datetime"),
    due_after: datetime | None = Query(None, description="Filter tasks due after this datetime"),
    limit: int = Query(50, ge=1, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    session: AsyncSession = Depends(get_db),
) -> TaskListResponse:
    """List tasks with optional filters and pagination.

    Args:
        status: Filter by status (pending, in_progress, completed).
        priority: Filter by priority (low, medium, high, critical).
        due_before: Filter tasks with eta before this datetime.
        due_after: Filter tasks with eta after this datetime.
        limit: Maximum number of results (default: 50).
        offset: Pagination offset (default: 0).
        session: Database session.

    Returns:
        TaskListResponse: Paginated task list.
    """
    return await list_tasks(
        session=session,
        status=status.value if status else None,
        priority=priority.value if priority else None,
        due_before=due_before,
        due_after=due_after,
        limit=limit,
        offset=offset,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_endpoint(task_id: str, session: AsyncSession = Depends(get_db)) -> TaskResponse:
    """Get a task by ID.

    Args:
        task_id: Task ID.
        session: Database session.

    Returns:
        TaskResponse: Task data.

    Raises:
        TaskNotFoundError: If task is not found (handled by FastAPI exception handler).
    """
    return await get_task(session, task_id)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task_endpoint(
    task_id: str, task_data: TaskUpdate, session: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """Update a task.

    Args:
        task_id: Task ID.
        task_data: Task update data.
        session: Database session.

    Returns:
        TaskResponse: Updated task.

    Raises:
        TaskNotFoundError: If task is not found (handled by FastAPI exception handler).
    """
    return await update_task(session, task_id, task_data)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_endpoint(task_id: str, session: AsyncSession = Depends(get_db)) -> None:
    """Delete a task.

    Args:
        task_id: Task ID.
        session: Database session.

    Raises:
        TaskNotFoundError: If task is not found (handled by FastAPI exception handler).
    """
    await delete_task(session, task_id)
