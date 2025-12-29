from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional, List


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    eta: Optional[datetime] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    eta: Optional[datetime] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None


class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    eta: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None
    attachments: List["AttachmentResponse"] = []


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int
