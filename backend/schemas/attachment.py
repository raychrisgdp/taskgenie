from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class AttachmentType(str, Enum):
    GMAIL = "gmail"
    GITHUB = "github"
    URL = "url"
    DOC = "doc"


class AttachmentCreate(BaseModel):
    task_id: str
    type: AttachmentType
    reference: str
    title: str | None = None


class AttachmentResponse(BaseModel):
    id: str
    task_id: str
    type: AttachmentType
    reference: str
    title: str | None
    content: str | None
    metadata: dict | None
    created_at: datetime
