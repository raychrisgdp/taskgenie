from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from datetime import datetime
import uuid
from ..database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)
    type = Column(String(20), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    action_taken = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    retry_count = Column(Integer, nullable=False, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "type": self.type,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "clicked_at": self.clicked_at.isoformat() if self.clicked_at else None,
            "action_taken": self.action_taken,
            "status": self.status,
            "retry_count": self.retry_count,
        }
