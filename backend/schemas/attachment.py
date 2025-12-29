from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional


class AttachmentType(str, Enum):
    GMAIL = "gmail"
    GITHUB = "github"
    URL = "url"
    DOC = "doc"


class AttachmentCreate(BaseModel):
    task_id: str
    type: AttachmentType
    reference: str
    title: Optional[str] = None


class AttachmentResponse(BaseModel):
    id: str
    task_id: str
    type: AttachmentType
    reference: str
    title: Optional[str]
    content: Optional[str]
    metadata: Optional[dict]
    created_at: datetime
