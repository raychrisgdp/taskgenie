from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "pending"
    priority: str = "medium"
    eta: Optional[datetime] = None
    tags: Optional[list] = None
    metadata: Optional[dict] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    eta: Optional[datetime] = None
    tags: Optional[list] = None
    metadata: Optional[dict] = None


class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: str
    priority: str
    eta: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    tags: Optional[list]
    metadata: Optional[dict]
    attachments: list = []


class TaskListResponse(BaseModel):
    tasks: list
    total: int
