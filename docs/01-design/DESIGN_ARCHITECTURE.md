# System Architecture

## Overview

The system is designed as a CLI-first, AI-native personal task manager with a local, single-user architecture.

```
User Interfaces
├── CLI (Typer)
├── Web UI (HTMX + Jinja2)
└── API (FastAPI)

Core Services
├── Task Service (CRUD)
├── LLM Service (Multi-provider)
├── Chat Service (RAG-powered)
├── Notification Service (Desktop)
└── Integration Services (Gmail, GitHub)

Data Layer
├── SQLite (Tasks, Attachments, Notifications)
└── ChromaDB (Vector storage for RAG)
```

## Key Design Principles

1. **CLI-first** - All functionality accessible from terminal via `todo` command
2. **AI-native** - Chat interface is primary, not a bolt-on feature
3. **Simple architecture** - One language (Python), minimal services, async-first
4. **Local-first** - All data stored locally, cloud sync optional
5. **Extensible** - Easy to add new LLM providers, integrations, and tools
6. **Privacy-focused** - No cloud dependencies for core functionality
7. **Type-safe** - Full type hints throughout (Pydantic, mypy)
8. **Testable** - Comprehensive test coverage

## Service Boundaries

### CLI Service

**Responsibilities:**
- Parse command-line arguments
- Format and display output (Rich library)
- Call API endpoints for all operations
- Handle interactive prompts
- Manage shell completion

**Dependencies:**
- Task Service API
- Chat Service API
- FastAPI client

**Key Design Decisions:**
- CLI should be stateless (no local state between commands)
- All operations go through API (even for local operations)
- Supports interactive mode with Rich prompts
- Generates shell completion scripts

---

### Web UI Service

**Responsibilities:**
- Render HTML templates with Jinja2
- Handle HTMX interactions
- Serve static assets
- WebSocket/SSE support for streaming

**Dependencies:**
- Task Service API
- Chat Service API
- HTMX library
- Tailwind CSS
- Jinja2 templates

**Key Design Decisions:**
- Server-side rendering (no SPA complexity)
- HTMX for dynamic interactions
- WebSocket for chat streaming
- Minimal JavaScript (only for WebSocket handling)
- Responsive design using Tailwind

---

### API Service (FastAPI)

**Responsibilities:**
- Expose REST API endpoints
- Handle WebSocket/SSE connections
- Validate requests with Pydantic
- Manage CORS if needed
- Auto-generate OpenAPI docs

**Dependencies:**
- Task Service
- Chat Service
- Notification Service
- Integration Services

**Key Design Decisions:**
- Async operations throughout
- Background tasks for notifications
- WebSocket manager for chat streaming
- Proper error handling and logging
- API versioning

---

### Task Service

**Responsibilities:**
- CRUD operations on tasks
- Search and filtering
- Attach task metadata
- Status management

**Dependencies:**
- Database (SQLAlchemy)
- Pydantic schemas

**Key Operations:**
- Create, Read, Update, Delete tasks
- List with filters (status, priority, due date)
- Search (keyword + RAG)

---

### LLM Service

**Responsibilities:**
- Multi-provider abstraction
- Chat completion
- Streaming responses
- Prompt management
- Error handling and retry logic

**Dependencies:**
- OpenAI SDK (works with 75+ providers)
- Environment configuration

**Key Design Decisions:**
- Support OpenRouter, OpenAI, Anthropic, custom endpoints
- Use OpenAI SDK's unified API
- Fallback between providers if one fails
- Streaming for real-time chat
- Configurable models and parameters

---

### Chat Service

**Responsibilities:**
- Context management for conversations
- RAG integration for semantic search
- Conversation history persistence
- Tool calling integration

**Dependencies:**
- LLM Service
- RAG Service
- Database

**Key Design Decisions:**
- Maintain conversation sessions (UUID-based)
- RAG context included in prompts
- Conversation history stored in database
- Support session resumption
- Context window management

---

### Notification Service

**Responsibilities:**
- Desktop notifications via plyer
- Scheduling logic (24h, 6h before ETA)
- Notification history tracking
- Click action handling

**Dependencies:**
- APScheduler for background scheduling
- Database for notification records
- plyer for cross-platform notifications
- Task Service for due date tracking

**Key Design Decisions:**
- Scheduled checks every 5 minutes
- Multiple notification triggers (24h, 6h before ETA)
- Notifications sent only if task not complete
- History tracking for debugging
- Clickable notifications (open task in web UI)
- Cross-platform support (Linux, macOS, Windows)

---

### Integration Services

#### Gmail Integration

**Responsibilities:**
- OAuth flow for authentication
- Fetch email by message ID or URL
- Parse email metadata (subject, from, date, threads)
- Cache email content for RAG
- Handle rate limiting

**Dependencies:**
- Google API Python Client
- OAuth credentials management

**Key Design Decisions:**
- Browser-based OAuth flow
- Token storage encrypted or in keyring
- Content cached in database for RAG
- Rate limit handling with exponential backoff
- Support for both message ID and Gmail URLs

#### GitHub Integration

**Responsibilities:**
- Fetch PR/issue details
- Parse repository metadata
- Handle rate limiting
- Cache content for RAG

**Dependencies:**
- PyGithub library
- Token storage

**Key Design Decisions:**
- Support both personal access tokens and OAuth
- Repository and file details cached
- Rate limit handling
- Support for PRs and issues
- Content cached in database for RAG

---

### RAG Service

**Responsibilities:**
- Generate embeddings for tasks and attachments
- Store vectors in ChromaDB
- Semantic search queries
- Retrieve relevant context for chat

**Dependencies:**
- ChromaDB
- Sentence-transformers (embeddings)
- Task Service (for content)
- Database

**Key Design Decisions:**
- Embeddings generated when tasks/attachments are created/updated
- Local-only (no external vector service)
- Similarity search with configurable threshold
- Rerank results for better relevance
- Context included in LLM prompts

---

### Database Layer

**Schema Overview:**

**Tables:**
- `tasks` - Core task records
- `attachments` - Links to external resources (Gmail, GitHub, URLs)
- `notifications` - Desktop notification records
- `chat_history` - Conversation session storage (optional)

**Key Relationships:**
- Task has many attachments
- Notification references one task
- Chat history has many messages

**Design Decisions:**
- SQLite for simplicity (can migrate to Postgres later)
- SQLAlchemy for ORM and migrations
- Async operations for performance
- JSON columns for flexible metadata
- Foreign key relationships with cascade delete
- Indexed on frequently queried fields (status, eta, priority)

---

## Tech Stack Rationale

### Why Python 3.11+?

- AI ecosystem (LangChain, ChromaDB, sentence-transformers)
- Type hints throughout (mypy support)
- Async support (FastAPI, SQLAlchemy)
- Rich library for beautiful CLI output

### Why SQLite?

- Simple setup (single file, no external service)
- Easy backup (copy file)
- Sufficient for personal use (millions of tasks possible)
- Can migrate to Postgres when needed
- Works well with async SQLAlchemy

### Why FastAPI?

- Modern and fast
- Native async support
- Auto-generated OpenAPI docs
- Pydantic integration
- Dependency injection support
- WebSocket support

### Why Typer?

- Modern CLI framework
- Type hints for completion
- Auto-help generation
- Rich output support
- Shell completion generation

### Why ChromaDB?

- Local-only (no external dependencies)
- Python-native
- Easy to use
- Persistent storage
- Good performance for personal scale

### Why HTMX + Jinja2?

- Server-side rendering (no SPA complexity)
- Minimal JavaScript
- Fast development
- Easy to maintain
- Good for CLI-first app

---

## Error Handling Strategy

### API Errors

- 400 Bad Request - Validation errors
- 404 Not Found - Resource doesn't exist
- 409 Conflict - Duplicate operations
- 422 Unprocessable - Business logic errors
- 429 Too Many Requests - Rate limiting
- 500 Internal Server - Unexpected errors

### CLI Errors

- Validation errors - Invalid input
- API errors - Connection/refused/timeouts
- Database errors - Constraint violations

### Notification Errors

- Notification failures logged but don't crash
- Retry with exponential backoff
- Graceful degradation if notification service unavailable

---

## Performance Considerations

### Database Queries

- Use indexes on status, eta, priority
- Limit result sets (pagination)
- Use eager loading where appropriate
- Avoid N+1 queries (select related in single query)

### API Responses

- Compress responses where appropriate
- Use pagination for large datasets
- Cache frequently accessed data
- Lazy loading for expensive operations

### RAG Operations

- Embeddings generated only once per document (cached)
- Similarity search with vector operations
- Batch embedding generation for efficiency

---

## Security Considerations

### Authentication

- API key authentication for LLM providers
- OAuth for Gmail (optional for personal use)
- No user authentication required (single-user, local)

### Data Privacy

- All data stored locally
- No data sent to external cloud (except LLM API calls)
- Cached content never transmitted to third parties
- Credentials stored securely (encrypted or keyring)

### Input Validation

- Pydantic schemas for all API requests
- Length limits on text fields
- Format validation on dates, URLs
- Sanitization of all user inputs

---

## Scalability

### Current Design

- Scales to single user with thousands of tasks
- RAG search handles thousands of vectors efficiently
- API handles concurrent requests via async

### Future Enhancements

- Support for multiple users (database migration to Postgres)
- Horizontal scaling for API (load balancer + multiple instances)
- Dedicated vector database for production scale
