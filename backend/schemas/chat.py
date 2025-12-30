from datetime import datetime

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime | None


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    include_attachments: bool = True


class ChatResponse(BaseModel):
    message: str
    session_id: str
    suggested_actions: list[str] | None = None
    related_tasks: list[str] | None = None
