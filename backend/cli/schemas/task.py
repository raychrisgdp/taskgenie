from datetime import datetime

from pydantic import BaseModel


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    status: str = "pending"
    priority: str = "medium"
    eta: datetime | None = None
    tags: list | None = None
    metadata: dict | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    eta: datetime | None = None
    tags: list | None = None
    metadata: dict | None = None


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str | None
    status: str
    priority: str
    eta: datetime | None
    created_at: datetime
    updated_at: datetime
    tags: list | None
    metadata: dict | None
    attachments: list = []


class TaskListResponse(BaseModel):
    tasks: list
    total: int
