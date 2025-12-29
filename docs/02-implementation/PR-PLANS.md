# Implementation Plan: Pull Requests

## Overview

This document tracks all planned Pull Requests for the taskgenie repository.

## Phase 1: Core Infrastructure (Weeks 1-2)

### PR-001: Database & Configuration Setup
**Branch:** `feature/db-config`
**Status:** ⬜ Not Started
**Description:** Initialize SQLite database with migrations and environment configuration
**Files to modify:**
- `backend/database.py` - Complete database initialization
- `backend/config.py` - Add configuration for migrations
**Acceptance Criteria:**
- [ ] Database creates tables on startup
- [ ] Environment variables load correctly
- [ ] Tests pass for database operations
**Estimated effort:** 2-3 hours

---

### PR-002: Task CRUD API Endpoints
**Branch:** `feature/task-crud`
**Status:** ⬜ Not Started
**Description:** Create REST API endpoints for task management
**Files to modify:**
- `backend/api/tasks.py` - Create API routes
- `backend/schemas/task.py` - Add/update schemas as needed
**Acceptance Criteria:**
- [ ] POST /api/tasks - Create task
- [ ] GET /api/tasks - List tasks with filters
- [ ] GET /api/tasks/{id} - Get task by ID
- [ ] PATCH /api/tasks/{id} - Update task
- [ ] DELETE /api/tasks/{id} - Delete task
- [ ] All endpoints return proper HTTP status codes
**Estimated effort:** 3-4 hours

---

### PR-003: CLI Task Commands
**Branch:** `feature/cli-tasks`
**Status:** ⬜ Not Started
**Description:** Implement CLI commands for task management
**Files to modify:**
- `backend/cli/main.py` - Add task commands
- `backend/cli/commands.py` - Create command modules (new file)
**Acceptance Criteria:**
- [ ] `todo add "Task title"` works
- [ ] `todo list` displays tasks
- [ ] `todo show <id>` shows task details
- [ ] `todo edit <id>` updates task
- [ ] `todo done <id>` marks complete
- [ ] `todo delete <id>` removes task
- [ ] Rich output with colors and formatting
**Estimated effort:** 4-5 hours

---

## Phase 2: AI Integration (Weeks 3-4)

### PR-004: LLM Service Implementation
**Branch:** `feature/llm-service`
**Status:** ⬜ Not Started
**Description:** Implement LLM service with OpenRouter/BYOK support
**Files to modify:**
- `backend/services/llm_service.py` - Complete implementation
- `backend/config.py` - Add LLM configuration options
**Acceptance Criteria:**
- [ ] Supports OpenRouter API
- [ ] Supports custom provider via base URL
- [ ] Handles API errors gracefully
- [ ] Streaming responses supported
- [ ] Tests pass for LLM calls
**Estimated effort:** 5-6 hours

---

### PR-005: Chat API & CLI Command
**Branch:** `feature/chat-api`
**Status:** ⬜ Not Started
**Description:** Create chat API endpoint and CLI chat command
**Files to modify:**
- `backend/api/chat.py` - Create API routes (new file)
- `backend/schemas/chat.py` - Add/update schemas as needed
- `backend/cli/main.py` - Add chat command
**Acceptance Criteria:**
- [ ] POST /api/chat - Send message, get response
- [ ] WebSocket or SSE streaming support
- [ ] CLI `todo chat` starts interactive session
- [ ] Conversation context maintained
- [ ] Tests for chat functionality
**Estimated effort:** 6-8 hours

---

## Phase 3: Integrations (Weeks 5-8)

### PR-006: Gmail Integration
**Branch:** `feature/gmail-integration`
**Status:** ⬜ Not Started
**Description:** Add Gmail OAuth and email fetching
**Files to modify:**
- `backend/integrations/gmail.py` - Complete implementation
- `backend/config.py` - Add Gmail OAuth settings
- `backend/schemas/attachment.py` - Update for Gmail attachments
**Acceptance Criteria:**
- [ ] OAuth flow works (browser authentication)
- [ ] Can fetch email by message ID or URL
- [ ] Email content cached in database
- [ ] Parse email metadata (subject, from, etc.)
- [ ] Tests for Gmail operations
**Estimated effort:** 8-10 hours

---

### PR-007: GitHub Integration
**Branch:** `feature/github-integration`
**Status:** ⬜ Not Started
**Description:** Add GitHub API integration for PRs and issues
**Files to modify:**
- `backend/integrations/github.py` - Complete implementation
- `backend/config.py` - Add GitHub token settings
- `backend/schemas/attachment.py` - Update for GitHub attachments
**Acceptance Criteria:**
- [ ] Can fetch PR by number
- [ ] Can fetch issue by number
- [ ] Repository and file details accessible
- [ ] Parse GitHub metadata (author, labels, etc.)
- [ ] Error handling for rate limits
- [ ] Tests for GitHub operations
**Estimated effort:** 6-8 hours

---

## Phase 4: RAG & Search (Weeks 9-10)

### PR-008: ChromaDB Integration
**Branch:** `feature/chromadb`
**Status:** ⬜ Not Started
**Description:** Integrate ChromaDB for vector storage and retrieval
**Files to modify:**
- `backend/services/rag_service.py` - Create new file
- `backend/database.py` - Add ChromaDB setup
- `backend/config.py` - Add ChromaDB configuration
- `pyproject.toml` - Add ChromaDB dependency
**Acceptance Criteria:**
- [ ] ChromaDB collection created on startup
- [ ] Documents embedded when created/updated
- [ ] Vector search implemented
- [ ] Semantic search across tasks and attachments
- [ ] Tests for RAG operations
**Estimated effort:** 8-10 hours

---

### PR-009: Semantic Search API
**Branch:** `feature/semantic-search`
**Status:** ⬜ Not Started
**Description:** Add semantic search endpoint with RAG
**Files to modify:**
- `backend/api/search.py` - Create API routes (new file)
- `backend/services/rag_service.py` - Add search methods
**Acceptance Criteria:**
- [ ] GET /api/search - Semantic search endpoint
- [ ] Returns ranked results with relevance scores
- [ ] Supports keyword search fallback
- [ ] RAG context included in results
- [ ] Tests for search functionality
**Estimated effort:** 4-5 hours

---

## Phase 5: Notifications (Weeks 11-12)

### PR-010: Notification Service
**Branch:** `feature/notifications`
**Status:** ⬜ Not Started
**Description:** Implement desktop notification service with scheduling
**Files to modify:**
- `backend/services/notification_service.py` - Complete implementation
- `backend/models/notification.py` - Update model
- `backend/config.py` - Add notification settings
- `pyproject.toml` - Add APScheduler dependency
**Acceptance Criteria:**
- [ ] Notification scheduler runs in background
- [ ] Notifications sent 24h before ETA
- [ ] Notifications sent 6h before ETA
- [ ] Overdue notifications sent
- [ ] Notifications use plyer (cross-platform)
- [ ] Tests for notification operations
**Estimated effort:** 6-8 hours

---

## Phase 6: Web UI (Weeks 13-14)

### PR-011: Web UI - Task Pages
**Branch:** `feature/web-tasks`
**Status:** ⬜ Not Started
**Description:** Create web UI pages for task management
**Files to modify:**
- `backend/api/tasks.py` - Add HTMX support
- `backend/templates/tasks.html` - Create template (new file)
- `backend/templates/base.html` - Update base template
**Acceptance Criteria:**
- [ ] Task list page renders correctly
- [ ] Task details page works
- [ ] HTMX interactions functional
- [ ] Responsive design
- [ ] No JavaScript required for basic functionality
**Estimated effort:** 8-10 hours

---

### PR-012: Web UI - Chat Interface
**Branch:** `feature/web-chat`
**Status:** ⬜ Not Started
**Description:** Create web chat interface with streaming
**Files to modify:**
- `backend/api/chat.py` - Add WebSocket/SSE for web
- `backend/templates/chat.html` - Create template (new file)
- `backend/templates/base.html` - Update for streaming
**Acceptance Criteria:**
- [ ] Chat page renders messages
- [ ] Streaming responses work
- [ ] WebSocket or SSE connected
- [ ] Input field accepts messages
- [ ] Responsive design
**Estimated effort:** 10-12 hours

---

## Phase 7: Testing & Polish (Weeks 15-16)

### PR-013: Testing Suite
**Branch:** `feature/testing`
**Status:** ⬜ Not Started
**Description:** Add comprehensive test suite
**Files to create:**
- `tests/test_tasks.py`
- `tests/test_chat.py`
- `tests/test_rag.py`
- `tests/test_integrations.py`
**Acceptance Criteria:**
- [ ] Unit tests for all services
- [ ] Integration tests for API endpoints
- [ ] Test coverage > 80%
- [ ] CI/CD pipeline configured
**Estimated effort:** 10-12 hours

---

### PR-014: Documentation & Deployment
**Branch:** `feature/docs-deploy`
**Status:** ⬜ Not Started
**Description:** Complete documentation and deployment configuration
**Files to modify:**
- `docs/02-implementation/DEPLOYMENT.md` - Create deployment guide
- `docs/INDEX.md` - Update to reflect new structure
- `README.md` - Update with deployment instructions
- `pyproject.toml` - Add deployment scripts
**Acceptance Criteria:**
- [ ] Deployment guide complete
- [ ] Docker configuration documented
- [ ] Local setup instructions clear
- [ ] Production deployment options documented
- [ ] README is comprehensive
**Estimated effort:** 4-6 hours

---

## PR Organization Strategy

### Immediate (Next 1-2 PRs)
1. **PR-001: Database & Configuration** - Foundation for everything
2. **PR-002: Task CRUD API** - Core API functionality

### Short-term (Weeks 3-6)
3. **PR-003: CLI Task Commands** - Primary interface
4. **PR-004: LLM Service** - AI capabilities
5. **PR-005: Chat API** - AI chat interface
6. **PR-006: Gmail Integration** - First integration
7. **PR-007: GitHub Integration** - Second integration
8. **PR-008: ChromaDB Integration** - Vector storage
9. **PR-009: Semantic Search** - RAG search

### Medium-term (Weeks 7-14)
10. **PR-010: Notification Service** - Desktop notifications
11. **PR-011: Web UI - Task Pages** - Web interface
12. **PR-012: Web UI - Chat Interface** - Streaming chat

### Long-term (Weeks 15-16)
13. **PR-013: Testing Suite** - Quality assurance
14. **PR-014: Documentation & Deployment** - Production ready

---

## Tracking Status

| PR # | Branch | Phase | Status | Estimated Effort |
|--------|---------|--------|--------|------------------|
| PR-001 | feature/db-config | Phase 1 | ⬜ Not Started | 2-3h |
| PR-002 | feature/task-crud | Phase 1 | ⬜ Not Started | 3-4h |
| PR-003 | feature/cli-tasks | Phase 1 | ⬜ Not Started | 4-5h |
| PR-004 | feature/llm-service | Phase 2 | ⬜ Not Started | 5-6h |
| PR-005 | feature/chat-api | Phase 2 | ⬜ Not Started | 6-8h |
| PR-006 | feature/gmail-integration | Phase 3 | ⬜ Not Started | 8-10h |
| PR-007 | feature/github-integration | Phase 3 | ⬜ Not Started | 6-8h |
| PR-008 | feature/chromadb | Phase 4 | ⬜ Not Started | 8-10h |
| PR-009 | feature/semantic-search | Phase 4 | ⬜ Not Started | 4-5h |
| PR-010 | feature/notifications | Phase 5 | ⬜ Not Started | 6-8h |
| PR-011 | feature/web-tasks | Phase 6 | ⬜ Not Started | 8-10h |
| PR-012 | feature/web-chat | Phase 6 | ⬜ Not Started | 10-12h |
| PR-013 | feature/testing | Phase 7 | ⬜ Not Started | 10-12h |
| PR-014 | feature/docs-deploy | Phase 7 | ⬜ Not Started | 4-6h |

**Total Estimated Effort:** ~120-150 hours (~3-4 months for one developer)

---

## Notes

- All PRs should be created from `main` branch
- Each PR should focus on one feature/component
- Tests should be included with each PR
- Documentation updates should accompany code changes
- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
