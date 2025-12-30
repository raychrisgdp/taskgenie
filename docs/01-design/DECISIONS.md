# Design Decisions Log

This document tracks all architectural and design decisions made during development, along with rationale.

---

## 1. Chat Interface Approach

**Decision:** Terminal-based REPL as primary (opencode-like experience)
**Date:** 2025-01-29
**Status:** ✅ Confirmed
**Rationale:**
- Familiar to developers (like git, docker workflows)
- Scriptable and SSH-friendly
- Natural language feels more "personal" than web forms
- Web UI serves as secondary for rich attachment preview

**Alternatives Considered:**
- Web-only chat (rejected - less scriptable)
- Both CLI and Web as primary (rejected - complexity)

---

## 2. Gmail Interaction Method

**Decision:** URL-based attachment with auto-detection
**Date:** 2025-01-29
**Status:** ✅ Confirmed
**Rationale:**
- Finding Gmail message-id is difficult (requires "Show Original" → Copy header)
- URLs are natural to copy (Ctrl+L from browser)
- Auto-detection parses task content for URLs during creation

**Implementation:**
```python
# Auto-detection runs on task create/edit
def detect_links(text: str) -> List[str]:
    # Regex for GitHub, Gmail, generic URLs
    return extract_urls(text)

# User can also manually attach:
# tgenie attach <task_id> --type gmail --ref "https://mail.google.com/mail/u/0/#inbox/..."
```

---

## 3. Docker Notification Strategy

**Decision:** Web UI notifications for MVP; Desktop notifications as Phase 3
**Date:** 2025-01-29
**Status:** ⚠️ Pending user confirmation
**Rationale:**
- Docker containers are isolated from host desktop (X11/DBus forwarding required)
- Complex to implement reliable host bridge
- Web UI can use browser notifications API

**Implementation (MVP):**
```python
# In Docker: No desktop notifications
# Notifications shown in Web UI when page is open
if web_ui_open:
    await notify_via_websocket(notification)
```

**Implementation (Phase 3):**
```python
# Optional: Host-side notification daemon
# Systemd service: tgenie-notify-host
# Listens to Docker container via socket, triggers plyer
```

**Alternatives Considered:**
- Docker with host IPC (rejected - complex, fragile)
- Skip desktop entirely (rejected - critical feature)

---

## 4. CLI Chat Session Behavior

**Decision:** Resume last session by default (if <24h old)
**Date:** 2025-01-29
**Status:** ✅ Confirmed
**Rationale:**
- Context continuity is critical for AI chat experience
- Users expect conversation memory
- Fresh sessions still available via `--new` flag

**Implementation:**
```python
# Default behavior
tgenie  # Resumes session if last message <24h ago

# Explicit controls
tgenie --new       # Always start fresh
tgenie --continue  # Force resume even if old
```

---

## 5. Task Metadata Fields

**Decision:** Required fields only; tags/subtasks as Phase 2
**Date:** 2025-01-29
**Status:** ✅ Confirmed
**Required Fields:**
- Title (string, required)
- Description (text, optional)
- Status (enum: pending/in_progress/completed)
- Priority (enum: low/medium/high/critical)
- ETA (datetime, optional)
- Attachments (list, auto-detected)

**Optional (Phase 2+):**
- Tags (array of strings)
- Subtasks (nested tasks)
- Dependencies (task blocking another task)

**Rationale:**
- Keep MVP simple (MVP: 8 weeks)
- Tags and subtasks add complexity
- Can be added post-MVP without breaking changes

---

## 6. Tech Stack - Python/FastAPI

**Decision:** Python 3.11+ with FastAPI + SQLite
**Date:** 2025-01-29
**Status:** ✅ Confirmed
**Rationale:**
- Python has best LLM/RAG ecosystem (OpenAI, ChromaDB)
- FastAPI: Native async support, auto API docs, type-safe
- SQLite: Simple, portable, no external dependencies (can migrate to Postgres later)
- Single language simplifies development

**Alternatives Considered:**
- Node.js (rejected - weaker AI library ecosystem)
- Go (rejected - good performance but slower development speed)
- Rust (rejected - excellent performance but steeper learning curve)

---

## 7. LLM Provider Strategy

**Decision:** OpenRouter with BYOK (Bring Your Own Key) support
**Date:** 2025-01-29
**Status:** ✅ Confirmed
**Rationale:**
- OpenRouter: 100+ models available, free options, single API endpoint
- BYOK: Users can use existing OpenAI/Anthropic credits
- Multi-provider: Can switch models without changing code
- Local models: Support for privacy-focused users

**Implementation:**
```python
# Config in ~/.taskgenie/config.toml
[llm]
provider = "openrouter"  # or "openai", "anthropic", "ollama"
model = "anthropic/claude-3-haiku"
api_key = "sk-or-v1-..."  # or sk-..., sk-ant-...
```

---

## 8. RAG Implementation

**Decision:** ChromaDB for vector storage with hybrid search
**Date:** 2025-01-29
**Status:** ✅ Confirmed
**Rationale:**
- ChromaDB: Python-native, no external service, works in Docker
- Hybrid search: Semantic + keyword fallback for reliability
- Task + Attachment indexing: Unified search across all content

**Implementation:**
```python
# Search strategy
1. Try RAG search (ChromaDB)
2. If fails or no results: Fall back to keyword search
3. Merge and rerank results
4. Present to user with relevance scores
```

---

## 9. Notification Timing

**Decision:** 24h and 6h before ETA (user-configurable)
**Date:** 2025-01-29
**Status:** ✅ Confirmed
**Rationale:**
- 24h: "Tomorrow" planning time
- 6h: "Today" urgency reminder
- User can customize schedule in config
- Quiet hours respected (no notifications 10PM-8AM)

**Implementation:**
```python
# Config
[notifications]
enabled = true
schedule = ["24h", "6h"]  # Also supports "1h"
quiet_hours = {"start": "22:00", "end": "08:00"}
```

---

## 10. Integration Approach

**Decision:** Provider Protocol with auto-discovery
**Date:** 2025-01-29
**Status:** ✅ Confirmed
**Rationale:**
- Extensible: New integrations just implement interface
- Auto-discovery: Links in task content automatically attached
- Clean separation: Integration logic isolated from core

**Interface Definition:**
```python
class IntegrationProvider(Protocol):
    def match_url(self, url: str) -> bool: ...
    async def fetch_content(self, reference: str) -> str: ...
    def get_metadata(self, reference: str) -> dict: ...
```

**Planned Integrations:**
- Gmail (Phase 3)
- GitHub (Phase 3)
- Future: Jira, Notion, Slack (user-contrib)

---

## 11. Web UI Technology

**Decision:** HTMX + Jinja2 + Tailwind CSS
**Date:** 2025-01-29
**Status:** ✅ Confirmed
**Rationale:**
- HTMX: Minimal JavaScript, server-rendered, fast
- Jinja2: Python-native, good integration with FastAPI
- Tailwind: Rapid styling, modern defaults
- No framework: Keeps app lightweight (<100MB bundle)

**Alternatives Considered:**
- React (rejected - adds complexity, larger bundle)
- Vue (rejected - requires build step)
- Alpine.js (rejected - less "pythonic")

---

## 12. Testing Strategy

**Decision:** Unit + Integration + E2E tests with 80% coverage target
**Date:** 2025-01-29
**Status:** ✅ Confirmed
**Rationale:**
- Unit tests: Fast feedback, catch regressions
- Integration tests: Validate API contracts
- E2E tests: Critical user journeys validated
- 80% coverage: Industry standard, prevents rot

**Implementation:**
```python
# Per PR requirement
- Unit tests for new/changed code
- Integration tests for new endpoints
- Manual E2E checklist for critical paths

# Critical journeys
1. Create task via chat
2. Auto-attach URL
3. Semantic search
4. Notification triggers
```

---

## 13. TUI Approach

**Decision:** Textual TUI-first for MVP; CLI subcommands for scripting
**Date:** 2025-12-29 (updated)
**Status:** ✅ Confirmed
**Rationale:**
- UX is a priority from day 1; TUI is the primary interface
- Textual provides full-screen "IDE-like" experience with fast iteration
- CLI subcommands remain for automation/scripting (best of both)

**Comparison:**
| Aspect | Rich (Subcommands) | Textual (Interactive TUI) |
|---------|----------------|---------------------|
| Complexity | Low | Medium |
| UX | Good | Excellent |
| Scripting | Perfect | Possible (with inline mode) |
| Learning Curve | Low | Medium |

---

## 14. Data Retention

**Decision:** 7-day backup retention, 90-day chat history
**Date:** 2025-01-29
**Status:** ⚠️ Tentative
**Rationale:**
- Backups: Keep 7 days of daily backups (disk space)
- Chat history: 90 days sufficient for context
- Can prune old messages to prevent DB bloat

**Implementation:**
```python
# Backup retention
# Keep 7 daily backups, delete older

# Chat history pruning
DELETE FROM chat_history
WHERE timestamp < datetime.utcnow() - timedelta(days=90)
```

---

## Pending Decisions

The following decisions require user input or further exploration:

### [ ] Docker vs Local Deployment
**Question:** Should this run in Docker on host machine?
**Options:**
- A) Docker Compose (recommended for development)
- B) Direct Python installation (simpler for production)
- C) Systemd service (auto-start on boot)

**Blocked By:** User preference

---

### [ ] Mobile Notification Strategy (Phase 3)
**Question:** How should mobile notifications work?
**Options:**
- A) Google Space integration (as mentioned in PLAN.md)
- B) Push notifications (Firebase/APNs)
- C) Email alerts
- D) No mobile (web-only)

**Blocked By:** Phase 3 scope

---

## Version History

| Version | Date | Changes |
|----------|-------|----------|
| 1.0 | 2025-01-29 | Initial decisions log |
