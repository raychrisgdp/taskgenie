"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2025-01-30 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create tasks table
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("priority", sa.String(20), nullable=True, server_default="medium"),
        sa.Column("eta", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
    )

    # Create attachments table
    op.create_table(
        "attachments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_id", sa.String(36), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("reference", sa.String(500), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
    )

    # Create notifications table
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_id", sa.String(36), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
    )

    # Create chat_history table
    op.create_table(
        "chat_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # Create config table
    op.create_table(
        "config",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # Create indexes for tasks
    op.create_index("idx_tasks_status", "tasks", ["status"])
    op.create_index("idx_tasks_eta", "tasks", ["eta"])
    op.create_index("idx_tasks_priority", "tasks", ["priority"])
    op.create_index("idx_tasks_created", "tasks", ["created_at"])

    # Create indexes for attachments
    op.create_index("idx_attachments_task_id", "attachments", ["task_id"])
    op.create_index("idx_attachments_type", "attachments", ["type"])

    # Create indexes for notifications
    op.create_index("idx_notifications_task_id", "notifications", ["task_id"])
    op.create_index("idx_notifications_scheduled", "notifications", ["scheduled_at"])
    op.create_index("idx_notifications_status", "notifications", ["status"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_notifications_status", table_name="notifications")
    op.drop_index("idx_notifications_scheduled", table_name="notifications")
    op.drop_index("idx_notifications_task_id", table_name="notifications")
    op.drop_index("idx_attachments_type", table_name="attachments")
    op.drop_index("idx_attachments_task_id", table_name="attachments")
    op.drop_index("idx_tasks_created", table_name="tasks")
    op.drop_index("idx_tasks_priority", table_name="tasks")
    op.drop_index("idx_tasks_eta", table_name="tasks")
    op.drop_index("idx_tasks_status", table_name="tasks")

    # Drop tables (in reverse order due to foreign keys)
    op.drop_table("config")
    op.drop_table("chat_history")
    op.drop_table("notifications")
    op.drop_table("attachments")
    op.drop_table("tasks")
