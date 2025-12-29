# Implementation Plan: Pull Requests (Chat-First Strategy)

## Overview

This document tracks all planned Pull Requests for the taskgenie repository. The plan follows a **Chat-First** strategy, prioritizing the AI/LLM core and Chat interface over traditional CLI commands.

**Strategy:**
1.  **Foundation:** DB, API, and LLM backbone
2.  **Chat Core:** Conversational interface and basic context
3.  **Intelligence:** RAG and Semantic Search
4.  **Integrations:** Connecting external tools (Gmail, GitHub)
5.  **Interfaces:** CLI (Secondary) and Web UI
6.  **Polish:** Notifications and Deployment

---

## Phase 1: Core Foundation & AI Backbone (Weeks 1-2)

### PR-001: Database & Configuration Setup
**Branch:** `feature/db-config`
**Status:** ⬜ Not Started
**Description:** Initialize SQLite database with migrations and environment configuration.
**Files to modify:**
- `backend/database.py` - Complete database initialization (Async SQLAlchemy)
- `backend/config.py` - Add configuration for migrations
- `backend/main.py` - Basic FastAPI app structure
**Acceptance Criteria:**
- [ ] Database creates tables on startup
- [ ] Environment variables load correctly
- [ ] Tests pass for database operations

### PR-002: Task CRUD API Endpoints
**Branch:** `feature/task-crud`
**Status:** ⬜ Not Started
**Dependency:** PR-001
**Description:** Create REST API endpoints for basic task management.
**Files to modify:**
- `backend/api/tasks.py` - Create API routes
- `backend/schemas/task.py` - Pydantic models
**Acceptance Criteria:**
- [ ] CRUD Endpoints (POST, GET, PATCH, DELETE) working
- [ ] Status transitions working
- [ ] Unit tests for API endpoints

### PR-003: LLM Service & Chat Backbone
**Branch:** `feature/llm-service`
**Status:** ⬜ Not Started
**Dependency:** PR-001
**Description:** Implement LLM service with OpenRouter/BYOK support and basic Chat API.
**Files to modify:**
- `backend/services/llm_service.py` - LLM Provider logic
- `backend/api/chat.py` - Chat endpoint (streaming)
**Acceptance Criteria:**
- [ ] Supports OpenRouter/OpenAI API
- [ ] Streaming response support
- [ ] Basic "Chat with Task" capability (System prompt aware of tasks)

---

## Phase 2: Intelligence & Attachments (Weeks 3-4)

### PR-004: Attachment API & Link Detection
**Branch:** `feature/attachments`
**Status:** ⬜ Not Started
**Dependency:** PR-002
**Description:** API for attachments and auto-detection service.
**Files to modify:**
- `backend/api/attachments.py` - CRUD for attachments
- `backend/services/link_detection.py` - Regex matcher for URLs
- `backend/schemas/attachment.py`
**Acceptance Criteria:**
- [ ] Manual attachment API works
- [ ] Detecting a URL in task description auto-creates attachment

### PR-005: ChromaDB & RAG Integration
**Branch:** `feature/rag-core`
**Status:** ⬜ Not Started
**Dependency:** PR-003, PR-004
**Description:** Vector storage for tasks and attachments to enable semantic search.
**Files to modify:**
- `backend/services/rag_service.py`
- `backend/database.py` - ChromaDB setup
**Acceptance Criteria:**
- [ ] Tasks/Attachments are auto-embedded on create/update
- [ ] Semantic search endpoint returns relevant results
- [ ] Chat uses RAG context for answers

---

## Phase 3: Integrations (Weeks 5-8)

*Note: PR-006 and PR-007 can be developed in parallel.*

### PR-006: Gmail Integration
**Branch:** `feature/gmail-integration`
**Status:** ⬜ Not Started
**Dependency:** PR-004
**Description:** Gmail OAuth, email fetching, and RAG content caching.
**Files to modify:**
- `backend/integrations/gmail.py`
- `backend/services/rag_service.py` (Update for email content)
**Acceptance Criteria:**
- [ ] OAuth flow working
- [ ] Fetch email content by ID/URL
- [ ] Email content indexed in RAG

### PR-007: GitHub Integration
**Branch:** `feature/github-integration`
**Status:** ⬜ Not Started
**Dependency:** PR-004
**Description:** GitHub API integration for Issues/PRs.
**Files to modify:**
- `backend/integrations/github.py`
**Acceptance Criteria:**
- [ ] Fetch Issue/PR details by URL
- [ ] PR content indexed in RAG

---

## Phase 4: User Interfaces (Weeks 9-12)

### PR-008: CLI Chat-First Interface
**Branch:** `feature/cli-core`
**Status:** ⬜ Not Started
**Dependency:** PR-003, PR-005
**Description:** The "todo" command entry point. Defaults to interactive chat REPL.
**Files to modify:**
- `backend/cli/main.py`
- `backend/cli/chat_repl.py`
**Acceptance Criteria:**
- [ ] `todo` opens chat REPL
- [ ] `todo "msg"` sends one-shot chat
- [ ] REPL supports slash commands (`/help`, `/exit`)

### PR-009: CLI Standard Commands (Secondary)
**Branch:** `feature/cli-commands`
**Status:** ⬜ Not Started
**Dependency:** PR-008
**Description:** Standard commands (`add`, `list`, `edit`) for scripting/power users.
**Files to modify:**
- `backend/cli/commands.py`
**Acceptance Criteria:**
- [ ] `todo list`, `todo add` work as subcommands
- [ ] Rich terminal output

### PR-010: Web UI (Chat & Tasks)
**Branch:** `feature/web-ui`
**Status:** ⬜ Not Started
**Dependency:** PR-003
**Description:** HTMX + Jinja2 Web Interface.
**Files to modify:**
- `backend/templates/*`
- `backend/api/web.py`
**Acceptance Criteria:**
- [ ] Chat interface with streaming
- [ ] Task management pages
- [ ] Responsive design

---

## Phase 5: Polish & Deployment (Weeks 13-14)

### PR-011: Notification Service
**Branch:** `feature/notifications`
**Status:** ⬜ Not Started
**Description:** Desktop notifications via `plyer` and scheduler.
**Files to modify:**
- `backend/services/notification_service.py`
**Acceptance Criteria:**
- [ ] Notifications trigger 24h/6h before deadline

### PR-012: Deployment & Documentation
**Branch:** `feature/deploy`
**Status:** ⬜ Not Started
**Description:** Docker polish, comprehensive README, and final docs.
**Acceptance Criteria:**
- [ ] `docker compose up` works flawlessly
- [ ] User guide complete

---

## Summary Timeline

| Phase | Focus | Weeks | Key PRs |
|-------|-------|--------|----------|
| **1** | **Foundation** | 1-2 | PR-001 (DB), PR-002 (Task API), PR-003 (LLM) |
| **2** | **Intelligence** | 3-4 | PR-004 (Attachments), PR-005 (RAG), PR-006 (Router) |
| **3** | **Integrations** | 5-8 | PR-007 (Gmail), PR-008 (GitHub) - **Can parallelize** |
| **4** | **Interfaces** | 9-12 | PR-009 (CLI Chat), PR-010 (CLI Commands), PR-011 (Web UI) |
| **5** | **Polish** | 13-14 | PR-012 (Notifications), PR-013 (Testing), PR-014 (Docs & Deploy) |

**Total Estimated Effort:** ~130 hours (~16 weeks for one developer)
