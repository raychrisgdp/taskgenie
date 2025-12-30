# Implementation Plan: Pull Requests

**Status:** Spec Complete | Implementation In Progress  
**Last Reviewed:** 2025-12-29  
**Total PRs:** 12 (PR-001 through PR-012)

## Overview

This document tracks all planned Pull Requests for the TaskGenie project. The plan follows an **Interactive TUI-First** strategy, with chat as the primary capability within the interactive interface.

**Strategy:**
1.  **Foundation:** DB + Task API (unblocks everything)
2.  **UX First:** Interactive TUI early, iterate fast on usability
3.  **Chat Next:** Add LLM chat inside the TUI once the UX shell exists
4.  **Feature Delivery:** Add attachments, then ship the earliest “tryable” features (Notifications and/or Integrations)
5.  **Intelligence:** RAG + semantic search to level-up chat and discovery
6.  **Polish:** Web UI (optional) + deployment/docs

> **Note:** The primary UX is an interactive TUI entered via `tgenie` (default), with chat as the main mode. Non-interactive subcommands (`tgenie add`, `tgenie list`, etc.) exist for scripting and automation.

---

## Design References

- Interactive TUI: `docs/01-design/DESIGN_TUI.md`
- Background jobs (no queue MVP): `docs/01-design/DESIGN_BACKGROUND_JOBS.md`
- Core architecture: `docs/01-design/DESIGN_ARCHITECTURE.md`

## Recommended Execution Order (UX-First)

This sequence prioritizes **something usable early** (good UX) and then adds capabilities bit-by-bit.

| Seq | PR | Title | Why now? | Depends on |
|---:|---|---|---|---|
| 1 | PR-001 | Database & Configuration | Foundation + migrations | - |
| 2 | PR-002 | Task CRUD API | Core workflows + enables clients | PR-001 |
| 3 | PR-008 | Interactive TUI (Tasks MVP) | Validate UX early | PR-002 |
| 4 | PR-003 | LLM + Chat Backbone | Make chat real inside TUI | PR-001, PR-002, PR-008 |
| 5 | PR-009 | CLI Subcommands (Secondary) | Scriptable workflows | PR-002 |
| 6 | PR-004 | Attachments + Link Detection | Context capture for real work | PR-002 |
| 7 | PR-011 | Notifications | Early “daily value” | PR-002 |
| 8 | PR-007 | GitHub Integration | High-value for dev tasks | PR-004 |
| 9 | PR-006 | Gmail Integration | High-value, higher complexity | PR-004 |
| 10 | PR-005 | RAG + Semantic Search | Better recall + better chat | PR-004, PR-003 |
| 11 | PR-010 | Web UI | Secondary UX for rich preview | PR-002 (chat optional: PR-003) |
| 12 | PR-012 | Deployment + Docs | Make it easy to run/share | PR-010, PR-011 |

Notes:
- You can swap **Seq 7–9** based on what you can test earliest (notifications vs integrations).
- PR-010 can be started earlier for task pages, but chat streaming needs PR-003.
- Specs (with test scenarios): `pr-specs/INDEX.md`

## PR Dependency Diagram

```mermaid
flowchart TD
  PR001["PR-001: Database & Config"]
  PR002["PR-002: Task CRUD API"]
  PR008["PR-008: Interactive TUI (Tasks MVP)"]
  PR003["PR-003: LLM + Chat Backbone"]
  PR009["PR-009: CLI Subcommands"]
  PR004["PR-004: Attachments + Link Detection"]
  PR011["PR-011: Notifications"]
  PR007["PR-007: GitHub Integration"]
  PR006["PR-006: Gmail Integration"]
  PR005["PR-005: RAG (ChromaDB)"]
  PR010["PR-010: Web UI"]
  PR012["PR-012: Deployment + Docs"]

  PR001 --> PR002
  PR002 --> PR008
  PR001 --> PR003
  PR002 --> PR003
  PR008 --> PR003
  PR002 --> PR009
  PR002 --> PR004
  PR004 --> PR007
  PR004 --> PR006
  PR002 --> PR011
  PR004 --> PR005
  PR003 --> PR005
  PR002 --> PR010
  PR003 -. "chat UI (optional)" .-> PR010
  PR010 --> PR012
  PR011 --> PR012
```

Notes:
- Edges reflect planned dependency relationships.
- PR-010 can ship “tasks-only” early; chat streaming waits on PR-003.

## Phase 1: Foundation + UX MVP (Weeks 1-2)

### PR-001: Database & Configuration Setup
**Branch:** `feature/db-config`
**Status:** ⬜ Not Started
**Description:** Initialize SQLite database with migrations and environment configuration.
**Spec:** `pr-specs/PR-001-db-config.md`
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
**Spec:** `pr-specs/PR-002-task-crud-api.md`
**Files to modify:**
- `backend/api/tasks.py` - Create API routes
- `backend/schemas/task.py` - Pydantic models
**Acceptance Criteria:**
- [ ] CRUD Endpoints (POST, GET, PATCH, DELETE) working
- [ ] Status transitions working
- [ ] Unit tests for API endpoints

### PR-008: CLI Interactive TUI Interface (Tasks MVP)
**Branch:** `feature/cli-core`
**Status:** ⬜ Not Started
**Dependency:** PR-002
**Description:** The `tgenie` command entry point. Ships an interactive TUI early for core task workflows (chat can be a stub until PR-003).
**Spec:** `pr-specs/PR-008-interactive-tui.md`
**Files to modify:**
- `backend/cli/main.py`
- `backend/cli/chat_repl.py`
**Acceptance Criteria:**
- [ ] `tgenie` opens interactive TUI
- [ ] Core task flows work end-to-end (create/list/show/edit/done)
- [ ] Chat UI can be present as placeholder until PR-003

---

## Phase 2: Chat + Attachments (Weeks 3-4)

### PR-003: LLM Service & Chat Backbone
**Branch:** `feature/llm-service`
**Status:** ⬜ Not Started
**Dependency:** PR-001, PR-002, PR-008
**Description:** Implement LLM service with OpenRouter/BYOK support and Chat API, then wire chat into the interactive TUI.
**Spec:** `pr-specs/PR-003-llm-chat-backbone.md`
**Files to modify:**
- `backend/services/llm_service.py` - LLM Provider logic
- `backend/api/chat.py` - Chat endpoint (streaming)
**Acceptance Criteria:**
- [ ] Supports OpenRouter/OpenAI API
- [ ] Streaming response support
- [ ] Interactive TUI chat works end-to-end

### PR-004: Attachment API & Link Detection
**Branch:** `feature/attachments`
**Status:** ⬜ Not Started
**Dependency:** PR-002
**Description:** API for attachments and auto-detection service.
**Spec:** `pr-specs/PR-004-attachments-link-detection.md`
**Files to modify:**
- `backend/api/attachments.py` - CRUD for attachments
- `backend/services/link_detection.py` - Regex matcher for URLs
- `backend/schemas/attachment.py`
**Acceptance Criteria:**
- [ ] Manual attachment API works
- [ ] Detecting a URL in task description auto-creates attachment

---

## Phase 3: Early Value Track (Weeks 5-6)

This phase is intentionally flexible: pick what’s easiest to validate early from a user POV.

### PR-011: Notification Service
**Branch:** `feature/notifications`
**Status:** ⬜ Not Started
**Dependency:** PR-002
**Description:** Reminders (24h/6h/overdue) based on task ETA; delivery via desktop notifications and/or in-app notifications depending on environment.
**Spec:** `pr-specs/PR-011-notifications.md`
**Files to modify:**
- `backend/services/notification_service.py`
**Acceptance Criteria:**
- [ ] Notifications trigger 24h/6h before deadline (and overdue)

### PR-007: GitHub Integration
**Branch:** `feature/github-integration`
**Status:** ⬜ Not Started
**Dependency:** PR-004
**Description:** Fetch Issue/PR details by URL and store as cached attachment content.
**Spec:** `pr-specs/PR-007-github-integration.md`
**Files to modify:**
- `backend/integrations/github.py`
**Acceptance Criteria:**
- [ ] Fetch Issue/PR details by URL
- [ ] Attachment content is cached for later search

### PR-006: Gmail Integration
**Branch:** `feature/gmail-integration`
**Status:** ⬜ Not Started
**Dependency:** PR-004
**Description:** Gmail OAuth + email fetching by URL; store as cached attachment content.
**Spec:** `pr-specs/PR-006-gmail-integration.md`
**Files to modify:**
- `backend/integrations/gmail.py`
**Acceptance Criteria:**
- [ ] OAuth flow working
- [ ] Fetch email content by URL and cache it as an attachment

---

## Phase 4: Intelligence (Weeks 7-8)

### PR-005: ChromaDB & RAG Integration
**Branch:** `feature/rag-core`
**Status:** ⬜ Not Started
**Dependency:** PR-003, PR-004
**Description:** Vector storage and semantic search over tasks and cached attachment content; integrate RAG context into chat responses.
**Spec:** `pr-specs/PR-005-rag-semantic-search.md`
**Files to modify:**
- `backend/services/rag_service.py`
- `backend/database.py` - ChromaDB setup
**Acceptance Criteria:**
- [ ] Tasks/Attachments are auto-embedded on create/update
- [ ] Semantic search endpoint returns relevant results
- [ ] Chat uses RAG context for answers

---

## Phase 5: Secondary UIs + Scripting (Weeks 9-10)

### PR-009: CLI Standard Commands (Secondary)
**Branch:** `feature/cli-commands`
**Status:** ⬜ Not Started
**Dependency:** PR-002
**Description:** Standard commands (`add`, `list`, `edit`) for scripting/power users.
**Spec:** `pr-specs/PR-009-cli-subcommands.md`
**Files to modify:**
- `backend/cli/commands.py`
**Acceptance Criteria:**
- [ ] `tgenie list`, `tgenie add` work as subcommands (for scripting)
- [ ] Rich terminal output

### PR-010: Web UI (Chat & Tasks)
**Branch:** `feature/web-ui`
**Status:** ⬜ Not Started
**Dependency:** PR-002 (chat optional: PR-003)
**Description:** HTMX + Jinja2 Web Interface (tasks first; chat streaming once PR-003 exists).
**Spec:** `pr-specs/PR-010-web-ui.md`
**Files to modify:**
- `backend/templates/*`
- `backend/api/web.py`
**Acceptance Criteria:**
- [ ] Task management pages
- [ ] Chat interface with streaming (if PR-003 is implemented)
- [ ] Responsive design

---

## Phase 6: Deploy + Docs (Weeks 11-12)

### PR-012: Deployment & Documentation
**Branch:** `feature/deploy`
**Status:** ⬜ Not Started
**Dependency:** PR-010, PR-011
**Description:** Docker polish, comprehensive README, and final docs.
**Spec:** `pr-specs/PR-012-deployment-docs.md`
**Acceptance Criteria:**
- [ ] `docker compose up` works flawlessly
- [ ] User guide complete

---

## Summary Timeline

| Phase | Focus | Weeks | Key PRs |
|-------|-------|--------|----------|
| **1** | **Foundation + UX MVP** | 1-2 | PR-001 (DB), PR-002 (Task API), PR-008 (TUI Tasks) |
| **2** | **Chat + Attachments** | 3-4 | PR-003 (LLM+Chat), PR-004 (Attachments) |
| **3** | **Early Value Track** | 5-6 | PR-011 (Notifications) and/or PR-007 (GitHub) / PR-006 (Gmail) |
| **4** | **Intelligence** | 7-8 | PR-005 (RAG + Semantic Search) |
| **5** | **Secondary UIs** | 9-10 | PR-009 (CLI subcommands), PR-010 (Web UI) |
| **6** | **Deploy + Docs** | 11-12 | PR-012 (Deployment & Docs) |

**Total Estimated Effort:** ~130 hours (~16 weeks for one developer)
