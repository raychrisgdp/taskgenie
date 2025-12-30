# Data Models

## Database Schema (SQLite)

### Core Tables

```sql
-- Tasks
CREATE TABLE tasks (
    id VARCHAR(36) PRIMARY KEY,  -- UUID
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, in_progress, completed
    priority VARCHAR(20) DEFAULT 'medium',  -- low, medium, high, critical
    eta DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tags JSON,  -- Array of tag strings
    metadata JSON  -- Additional flexable fields
);

-- Attachments
CREATE TABLE attachments (
    id VARCHAR(36) PRIMARY KEY,  -- UUID
    task_id VARCHAR(36) NOT NULL,
    type VARCHAR(20) NOT NULL,  -- gmail, github, url, doc
    reference VARCHAR(500) NOT NULL,  -- URL, message ID, etc.
    title VARCHAR(255),
    content TEXT,  -- Cached/fetched content for RAG
    metadata JSON,  -- Additional data (sender, repo, etc.)
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Notifications
CREATE TABLE notifications (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) NOT NULL,
    type VARCHAR(20) NOT NULL,  -- due_24h, due_6h
    scheduled_at DATETIME NOT NULL,
    sent_at DATETIME,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, sent, dismissed
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Chat History (optional, for conversation continuity)
CREATE TABLE chat_history (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    role VARCHAR(10) NOT NULL,  -- user, assistant
    content TEXT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Config (stored in DB, not file)
CREATE TABLE config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## Pydantic Schemas

### Task Models

```python
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

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
    """Schema for creating a task"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    eta: Optional[datetime] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None

class TaskUpdate(BaseModel):
    """Schema for updating a task (all optional)"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    eta: Optional[datetime] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None

class TaskResponse(BaseModel):
    """Schema for task response (includes all fields)"""
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
    """Schema for paginated task list"""
    tasks: List[TaskResponse]
    total: int
    page: int
    page_size: int
```

### Attachment Models

```python
class AttachmentType(str, Enum):
    GMAIL = "gmail"
    GITHUB = "github"
    URL = "url"
    DOC = "doc"

class AttachmentCreate(BaseModel):
    """Schema for creating an attachment"""
    task_id: str
    type: AttachmentType
    reference: str  -- URL, message ID, etc.
    title: Optional[str] = None

class AttachmentResponse(BaseModel):
    """Schema for attachment response"""
    id: str
    task_id: str
    type: AttachmentType
    reference: str
    title: Optional[str] = None
    content: Optional[str] = None  -- Cached content
    metadata: Optional[dict] = None
    created_at: datetime
```

### Chat Models

```python
class ChatMessage(BaseModel):
    """Single chat message"""
    role: str  -- "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    """Chat request with optional context"""
    message: str
    session_id: Optional[str] = None
    include_attachments: bool = True  -- Include RAG from attachments

class ChatResponse(BaseModel):
    """Chat response (can be streaming)"""
    message: str
    session_id: str
    suggested_actions: Optional[List[str]] = None
    related_tasks: Optional[List[TaskResponse]] = None
```

### Search Models

```python
class SearchResult(BaseModel):
    """Search result with relevance score"""
    type: str  -- "task" or "attachment"
    id: str
    title: str
    relevance: float = Field(..., ge=0, le=1)
    snippet: Optional[str] = None
```

## JSON Examples

### Task JSON

```json
{
  "id": "abc123-def456-ghi789",
  "title": "Review PR #123",
  "description": "Fix authentication bug in login flow",
  "status": "pending",
  "priority": "high",
  "eta": "2025-01-15T14:00:00Z",
  "created_at": "2025-01-10T10:00:00Z",
  "updated_at": "2025-01-10T10:00:00Z",
  "tags": ["frontend", "bug", "high-priority"],
  "metadata": {
    "source": "cli",
    "estimated_hours": 2
  },
  "attachments": [
    {
      "id": "att-1",
      "type": "github",
      "reference": "https://github.com/owner/repo/pull/123",
      "title": "GitHub PR #123: Fix authentication",
      "metadata": {
        "repo": "owner/repo",
        "pr_number": 123,
        "author": "johndoe"
      },
      "created_at": "2025-01-10T10:30:00Z"
    }
  ]
}
```

### Attachment JSON

```json
{
  "id": "att-1",
  "task_id": "abc123-def456-ghi789",
  "type": "gmail",
  "reference": "18e4f7a2b3c4d5e",
  "title": "Client meeting request",
  "content": "Hi,\n\nThanks for the great work on Q1...",
  "metadata": {
    "from": "client@company.com",
    "subject": "Q1 Review Meeting",
    "date": "2025-01-11",
    "thread_id": "thread-xyz"
  },
  "created_at": "2025-01-12T09:00:00Z"
}
```

### Chat Session JSON

```json
{
  "session_id": "sess-abc123",
  "messages": [
    {
      "role": "user",
      "content": "What tasks do I have due this week?",
      "timestamp": "2025-01-15T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "You have 3 tasks due this week...",
      "timestamp": "2025-01-15T10:00:01Z",
      "suggested_actions": [
        "Show details for PR #123",
        "Mark project update as in progress"
      ],
      "related_tasks": ["abc123", "def456"]
    }
  ]
}
```

## RAG Document Structure

### Task Document (for vector search)

```json
{
  "id": "task-abc123",
  "content": "Title: Review PR #123\nDescription: Fix authentication bug in login flow\nPriority: High\nStatus: Pending",
  "metadata": {
    "type": "task",
    "task_id": "abc123",
    "priority": "high",
    "status": "pending",
    "created_at": "2025-01-10"
  }
}
```

### Attachment Document (for vector search)

```json
{
  "id": "att-1",
  "content": "From: client@company.com\nSubject: Q1 Review Meeting\n\nHi,\n\nThanks for the great work on Q1...",
  "metadata": {
    "type": "attachment",
    "attachment_type": "gmail",
    "task_id": "abc123",
    "from": "client@company.com"
  }
}
```

## Data Relationships

```
Task (1) ──┐
            ├──> Attachments (0..*)
            │
            ├──> Notifications (0..2)
            │
            └──> Chat Messages (many sessions reference task)
```

## Indexes (for performance)

```sql
-- Task indexes
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_eta ON tasks(eta);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_created ON tasks(created_at);

-- Attachment indexes
CREATE INDEX idx_attachments_task_id ON attachments(task_id);
CREATE INDEX idx_attachments_type ON attachments(type);

-- Notification indexes
CREATE INDEX idx_notifications_task_id ON notifications(task_id);
CREATE INDEX idx_notifications_scheduled ON notifications(scheduled_at);
CREATE INDEX idx_notifications_status ON notifications(status);
```

## Data Migration Strategy

### Version 1 (Initial)
- Basic task table
- Attachments table
- Simple status enum

### Version 2 (Add RAG)
- Add content column to attachments (cache)
- Add chat_history table
- Add RAG integration

### Version 3 (Enhanced metadata)
- Add metadata JSON columns
- Add tags array support
- Add more priority levels

## Storage Locations

### File System
```
~/.taskgenie/
├── config.toml          # Configuration
├── credentials.json      # OAuth credentials (encrypted)
├── data/
│   ├── taskgenie.db     # SQLite database
│   └── chroma/         # ChromaDB vector store
├── logs/
│   └── taskgenie.log    # Application logs
└── cache/
    └── attachments/      # Cached attachment content
```

### Docker Volumes
```
docker volumes:
  - taskgenie-data:/app/data       # Database
  - taskgenie-chroma:/app/chroma   # Vector store
  - taskgenie-config:/app/config   # Configuration
  - taskgenie-logs:/app/logs       # Logs
```

## Data Lifecycle

### Task Lifecycle
```
Created → Pending → In Progress → Completed
                         ↓
                       Deleted
```

### Notification Lifecycle
```
Scheduled → Sent → Dismissed
              ↓
            Failed (retry)
```

### Attachment Content Cache
```
Created → Fetched → Cached → Periodic Refresh
                                 ↓
                            Stale (refetch)
```

## Privacy & Security

### Sensitive Data
- API keys: Store encrypted, never log
- OAuth tokens: Secure storage, auto-refresh
- Email content: Cached locally, never transmitted to third parties
- Task content: Stored locally, never sent to cloud (except LLM for RAG)

### Data Export
```json
{
  "version": "1.0",
  "exported_at": "2025-01-15T10:00:00Z",
  "tasks": [...],
  "attachments": [...],
  "config": {
    "llm_provider": "openrouter",
    "model": "anthropic/claude-3-haiku"
  }
}
```

## Backup Strategy

### SQLite Backup & Restore

**Dump database to SQL file:**
```bash
# Default database location: ~/.taskgenie/data/taskgenie.db (or configured DATABASE_URL)
sqlite3 ~/.taskgenie/data/taskgenie.db .dump > backup.sql

# Or if using custom path
sqlite3 /path/to/taskgenie.db .dump > backup.sql
```

**Restore from SQL file:**
```bash
# Restore into existing database (will overwrite)
sqlite3 ~/.taskgenie/data/taskgenie.db < backup.sql

# Restore into a new database
sqlite3 new_taskgenie.db < backup.sql
```

**Create a backup copy of the database file:**
```bash
# Simple file copy (SQLite supports this while running)
cp ~/.taskgenie/data/taskgenie.db ~/.taskgenie/data/taskgenie_backup_$(date +%Y%m%d).db
```

### Automatic Backups (Planned)
- Daily backup to `~/.taskgenie/backups/taskgenie_YYYYMMDD.db`
- Keep 7 days of backups
- Compress old backups (gzip)

### Manual Backup via CLI (Planned)
```bash
$ tgenie db dump --out backup.sql
✓ Wrote backup.sql
```

### Restore via CLI (Planned)
```bash
$ tgenie db restore --in backup.sql
⚠️  This will overwrite existing data. Continue? [y/N]: y
✓ Restore complete
```

### Database Migrations (Planned)

**Recommended approach: Alembic migrations**

Once implemented, migrations will be managed via:
```bash
# Create a new migration
tgenie db revision -m "Add priority field"

# Apply migrations
tgenie db upgrade

# Rollback one migration
tgenie db downgrade -1
```

**Current status:** Schema changes are manual until migration system is implemented (see PR-001).
