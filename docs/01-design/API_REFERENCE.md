# API Reference

## Overview

This document provides a complete reference for all REST and WebSocket APIs in the Personal TODO system.

**Base URL:** `http://localhost:8080/api/v1` (configurable)

**Authentication:** Optional API key header for local use
```python
headers = {"Authorization": "Bearer YOUR_API_KEY"}
```

---

## Endpoints

### Tasks

#### POST `/api/v1/tasks`
Create a new task.

**Request:**
```json
{
  "title": "Review PR #123",
  "description": "Fix authentication bug in login flow",
  "status": "pending",
  "priority": "high",
  "eta": "2025-01-15T14:00:00Z",
  "tags": ["frontend", "bug"],
  "metadata": {"estimated_hours": 2}
}
```

**Response (201):**
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
  "tags": ["frontend", "bug"],
  "metadata": {"estimated_hours": 2},
  "attachments": []
}
```

---

#### GET `/api/v1/tasks`
List tasks with optional filters.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|--------|----------|----------|-------------|
| `status` | string | No | All | Filter by status: `pending`, `in_progress`, `completed` |
| `priority` | string | No | All | Filter by priority: `low`, `medium`, `high`, `critical` |
| `due_before` | datetime | No | - | Tasks due before this date |
| `due_after` | datetime | No | - | Tasks due after this date |
| `limit` | integer | No | 50 | Maximum number of results |
| `offset` | integer | No | 0 | Pagination offset |

**Response (200):**
```json
{
  "tasks": [...],
  "total": 42,
  "page": 1,
  "page_size": 50
}
```

---

#### GET `/api/v1/tasks/{id}`
Get task by ID.

**Response (200):**
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
  "tags": ["frontend", "bug"],
  "attachments": [
    {
      "id": "att-1",
      "type": "github",
      "reference": "https://github.com/owner/repo/pull/123",
      "title": "GitHub PR #123"
    }
  ]
}
```

**Error (404):**
```json
{
  "error": "Task not found",
  "code": "TASK_NOT_FOUND"
}
```

---

#### PATCH `/api/v1/tasks/{id}`
Update task fields (all optional).

**Request:**
```json
{
  "title": "Updated title",
  "status": "in_progress",
  "priority": "critical",
  "eta": "2025-01-20T14:00:00Z"
}
```

**Response (200):**
```json
{
  "id": "abc123-def456-ghi789",
  "title": "Updated title",
  "status": "in_progress",
  "updated_at": "2025-01-10T12:00:00Z"
}
```

**Error (404):** Same as GET

---

#### DELETE `/api/v1/tasks/{id}`
Delete a task.

**Response (204):** No content

**Error (404):** Same as GET

---

### Chat

#### POST `/api/v1/chat`
Send a chat message and get a streaming response.

**Request:**
```json
{
  "message": "What tasks do I have due this week?",
  "session_id": "sess-abc123",
  "include_attachments": true
}
```

**Response:** Server-Sent Events (SSE) stream

```
data: You have 3 tasks due this week:

📅 Wednesday, January 15:
  1. abc123 ⏰ 2:00 PM • Review PR #123 [high]
     Description: Fix authentication bug in login flow
     Attachment: GitHub PR #123

...

data: [DONE]
```

**Suggested Actions (in metadata):**
```json
{
  "suggested_actions": [
    "Show PR #123 details",
    "Mark PR #123 as in progress",
    "Send project update"
  ],
  "related_tasks": ["abc123", "def456"]
}
```

---

#### GET `/api/v1/chat/history/{session_id}`
Get chat history for a session.

**Response (200):**
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
      "timestamp": "2025-01-15T10:01:00Z",
      "suggested_actions": [...],
      "related_tasks": [...]
    }
  ]
}
```

---

### Search

#### GET `/api/v1/search`
Keyword search across tasks.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|--------|----------|----------|-------------|
| `q` | string | Yes | - | Search query |
| `include_attachments` | boolean | No | false | Include attachment content in search |
| `limit` | integer | No | 10 | Maximum results |

**Response (200):**
```json
{
  "results": [
    {
      "type": "task",
      "id": "abc123",
      "title": "Review PR #123",
      "relevance": 1.0,
      "snippet": "Fix authentication bug in login flow"
    },
    {
      "type": "attachment",
      "id": "att-1",
      "title": "GitHub PR #123",
      "relevance": 0.89,
      "snippet": "The current JWT token validation..."
    }
  ],
  "query": "authentication"
}
```

---

#### GET `/api/v1/search/semantic`
Semantic/RAG search across tasks and attachments.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|--------|----------|-------------|
| `q` | string | Yes | - | Search query |
| `limit` | integer | No | 5 | Maximum results |

**Response (200):**
```json
{
  "results": [
    {
      "type": "task",
      "id": "abc123",
      "title": "Fix authentication bug",
      "relevance": 0.95,
      "reasoning": "Task title and description discuss authentication issues",
      "snippet": "Users unable to log in after token expiration"
    },
    {
      "type": "attachment",
      "id": "att-1",
      "title": "GitHub PR #123",
      "relevance": 0.89,
      "reasoning": "PR description contains JWT token validation issues",
      "snippet": "The current JWT token validation doesn't properly handle expired tokens"
    }
  ],
  "query_embedding": [0.23, 0.45, 0.67, ...]
}
```

---

### Attachments

#### POST `/api/v1/attachments`
Create an attachment for a task.

**Request:**
```json
{
  "task_id": "abc123-def456-ghi789",
  "type": "github",
  "reference": "https://github.com/owner/repo/pull/123"
}
```

**Response (201):**
```json
{
  "id": "att-1",
  "task_id": "abc123-def456-ghi789",
  "type": "github",
  "reference": "https://github.com/owner/repo/pull/123",
  "title": "GitHub PR #123: Fix authentication",
  "content": "Fetched content from GitHub...",
  "metadata": {"repo": "owner/repo", "pr_number": 123},
  "created_at": "2025-01-12T09:30:00Z"
}
```

---

#### GET `/api/v1/attachments/{id}`
Get attachment by ID.

**Response (200):** Similar to POST response

**Error (404):**
```json
{
  "error": "Attachment not found",
  "code": "ATTACHMENT_NOT_FOUND"
}
```

---

#### DELETE `/api/v1/attachments/{id}`
Delete an attachment.

**Response (204):** No content

**Error (404):** Same as GET

---

## Error Codes

| Code | Meaning | Retry | HTTP Status |
|-------|----------|-------|--------------|
| `TASK_NOT_FOUND` | No | 404 |
| `ATTACHMENT_NOT_FOUND` | No | 404 |
| `INVALID_STATUS` | No | 400 |
| `INVALID_PRIORITY` | No | 400 |
| `INVALID_DATE` | No | 400 |
| `SESSION_NOT_FOUND` | No | 404 |
| `LLM_UNAVAILABLE` | Yes | 503 |
| `RATE_LIMITED` | Yes | 429 |
| `INTERNAL_ERROR` | Yes | 500 |

**Rate Limiting:**
- 100 requests per minute
- 1000 requests per hour
- Retry after `Retry-After` header

---

## Schemas

### TaskCreate
```python
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    eta: Optional[datetime] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None
```

### TaskUpdate
```python
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    eta: Optional[datetime] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None
```

### TaskResponse
All fields from TaskCreate plus:
```python
id: str
created_at: datetime
updated_at: datetime
attachments: List[AttachmentResponse]
```

### ChatRequest
```python
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    include_attachments: bool = True
```

### ChatResponse
```python
class ChatResponse(BaseModel):
    message: str
    session_id: str
    suggested_actions: Optional[List[str]] = None
    related_tasks: Optional[List[TaskResponse]] = None
```

### SearchResponse
```python
class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
```

### SearchResult
```python
class SearchResult(BaseModel):
    type: str  # "task" or "attachment"
    id: str
    title: str
    relevance: float  # 0.0 to 1.0
    snippet: Optional[str] = None
```

---

## Authentication

For local use (Docker or localhost), authentication is optional.

**When configured:**
```python
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}
```

**When not configured:**
```python
headers = {
    "Content-Type": "application/json"
}
```

---

## OpenAPI/Swagger

Auto-generated API documentation available at:
```
http://localhost:8080/docs
```

Includes:
- Interactive API explorer
- Request/response schemas
- Try-it-out feature
- Authentication instructions

---

## WebSocket Events (Chat Streaming)

### Server-Sent Events (SSE)

**Connection:**
```
GET /api/v1/chat/stream
Accept: text/event-stream
```

**Event Format:**
```
data: <token>
data: [DONE]
```

**Keep-Alive:**
- Heartbeat every 15 seconds
- `: keep-alive\n`

---

## Examples

### Example 1: Create Task via API

```bash
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Review PR #123",
    "description": "Fix authentication bug",
    "priority": "high",
    "eta": "2025-01-15T14:00:00Z"
  }'
```

Response:
```json
{
  "id": "abc123-def456-ghi789",
  "title": "Review PR #123",
  ...
}
```

---

### Example 2: Chat with Streaming (Python)

```python
import httpx

async def chat_stream():
    async with httpx.AsyncClient() as client:
        async with client.stream(
            'POST',
            'http://localhost:8080/api/v1/chat',
            json={'message': 'What tasks are due today?'},
            timeout=None
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    token = line[5:]  # Remove 'data: ' prefix
                    print(token, end='', flush=True)
                elif line.strip() == 'data: [DONE]':
                    break
```

---

### Example 3: Semantic Search

```bash
curl "http://localhost:8080/api/v1/search/semantic?q=authentication+problems&limit=5"
```

Response:
```json
{
  "results": [
    {
      "type": "task",
      "id": "abc123",
      "title": "Fix authentication bug",
      "relevance": 0.95,
      "reasoning": "Task discusses authentication"
    }
  ]
}
```

---

## Testing

### Unit Tests
```python
def test_create_task():
    response = client.post("/api/v1/tasks", json={
        "title": "Test task"
    })
    assert response.status_code == 201
    assert "id" in response.json()

def test_get_task_not_found():
    response = client.get("/api/v1/tasks/nonexistent")
    assert response.status_code == 404
    assert "error" in response.json()
```

### Integration Tests
```python
def test_chat_flow():
    # 1. Create task
    task = create_task({"title": "Test task"})
    
    # 2. Search for task
    results = search("test")
    assert task["id"] in [r["id"] for r in results]
    
    # 3. Ask AI about task
    response = chat(f"What's in {task['id']}?")
    assert "content" in response
```

---

## Versioning

**Current Version:** v1.0

**Breaking Changes:** None (initial release)

**Future Considerations:**
- Rate limiting per user
- Cursor-based pagination for large datasets
- WebSocket reconnection handling
- Batch operations (bulk create, bulk update)
