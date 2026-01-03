"""Task schemas for API request/response validation.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TaskStatus(str, Enum):
    """Task status enum."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(str, Enum):
    """Task priority enum."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskCreate(BaseModel):
    """Schema for creating a task."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    eta: datetime | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


class TaskUpdate(BaseModel):
    """Schema for updating a task (all fields optional)."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    eta: datetime | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_title_not_null(cls, data: dict[str, Any] | Any) -> dict[str, Any] | Any:
        """Reject title=None to prevent database integrity errors.

        This validator runs before Pydantic's type coercion, so it can detect
        when title is explicitly set to None in the input JSON.

        Args:
            data: Raw input data (dict or model instance).

        Returns:
            Data unchanged if valid.

        Raises:
            ValueError: If title is explicitly set to None.
        """
        if isinstance(data, dict) and "title" in data and data["title"] is None:
            msg = "title cannot be null"
            raise ValueError(msg)
        return data


class TaskResponse(BaseModel):
    """Schema for task response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    eta: datetime | None
    created_at: datetime
    updated_at: datetime
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = Field(None, alias="meta_data", serialization_alias="metadata")
    attachments: list[dict[str, Any]] = Field(default_factory=list)


class TaskListResponse(BaseModel):
    """Schema for paginated task list response."""

    tasks: list[TaskResponse]
    total: int
    page: int
    page_size: int


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    error: str
    code: str
