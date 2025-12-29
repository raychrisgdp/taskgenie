from pydantic import BaseModel, Field
from typing import Optional, List


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime]


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    include_attachments: bool = True


class ChatResponse(BaseModel):
    message: str
    session_id: str
    suggested_actions: Optional[List[str]] = None
    related_tasks: Optional[List[str]] = None
