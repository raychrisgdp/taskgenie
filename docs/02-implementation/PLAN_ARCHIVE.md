# Project Plan Archive (Planning Notes)

**Status:** Archived reference  
**Last Updated:** 2025-12-30

This file preserves early planning notes that are no longer part of the primary implementation roadmap.

Current sources of truth:
- Roadmap + dependency order: `docs/02-implementation/PR-PLANS.md`
- Per-PR specs (with test plans): `docs/02-implementation/pr-specs/`
- Design decisions: `docs/01-design/DECISIONS.md`

---

## Clarifying Questions (Original Notes)

### 1. Chat Interface Style ✅
**How do you want chat interface to work?**
- [x] **Terminal-based chat** (like we're doing now, in the terminal) ← **DECISION: CONFIRMED**
- [ ] **Web-based chat UI** (access at localhost:8080/chat) ← Secondary interface
- [x] **Both** - CLI for commands, web for rich chat with attachments preview ← **DECISION: CONFIRMED**
- [ ] **Slack/Discord integration** for chat access ← Future (Phase 3)

**See:** [DECISIONS.md](../01-design/DECISIONS.md) for detailed rationale

### 2. Document/Email Attachment ✅
**How should attachments work?**
- [ ] **Links/URLs only** - Store references to Gmail, GitHub PRs, documents
- [x] **Fetch and cache** - Download content and store in TODO system ← **DECISION: CONFIRMED**
- [x] **Hybrid** - Store links + cache content for search ← **DECISION: CONFIRMED**
- [ ] **Manual paste** - Copy content and attach to task ← Supported via command

**See:** [DECISIONS.md](../01-design/DECISIONS.md) for detailed rationale

### 3. Authentication for GMail/etc ✅
**How to access external services?**
- [x] **OAuth flow** - Browser-based authentication ← **DECISION: CONFIRMED**
- [ ] **API keys** - Store in environment variables ← For LLM providers only
- [ ] **Service accounts** - For GMail API ← Future (Phase 3)
- [ ] **User-provided tokens** - Manually input tokens ← LLM BYOK support

**See:** [DECISIONS.md](../01-design/DECISIONS.md) for detailed rationale

### 4. Task Metadata (Simplified) ✅
**Required fields:**
- [x] Title/summary ← **DECISION: CONFIRMED**
- [x] Description ← **DECISION: CONFIRMED**
- [x] ETA/due date ← **DECISION: CONFIRMED**
- [x] Status (pending, in progress, completed) ← **DECISION: CONFIRMED**
- [x] Links/attachments (Gmail, GitHub PRs, docs) ← **DECISION: CONFIRMED**

**Optional fields:**
- [x] Priority level ← **DECISION: CONFIRMED (included in MVP)**
- [ ] Tags/categories ← Future (Phase 2)
- [ ] Subtasks ← Future (Phase 2)
- [ ] Dependencies ← Future (Phase 3)

**See:** [DECISIONS.md](../01-design/DECISIONS.md) for detailed rationale

### 5. Notification Click Action ⚠️
**What should happen when clicking notification?**
- [x] Open web UI to task details ← **DECISION: MVP APPROACH**
- [ ] Open attached documents/links ← Limited support in Docker
- [ ] Show in terminal with option to mark complete ← Future (Phase 3)
- [ ] Open specific file/command ← Future (Phase 3)

**Note:** Due to Docker isolation, desktop notifications are complex. MVP will use Web UI browser notifications. Phase 3 will explore native desktop notifications.

**See:** [DECISIONS.md](../01-design/DECISIONS.md) for detailed rationale

### 3. Notification System ✅
**What notifications do you need?**
- [x] Due date reminders (how far in advance?) ← **DECISION: 24h and 6h before**
- [x] Overdue task alerts ← **DECISION: Immediate when task passes ETA**
- [x] Task completion confirmations ← **DECISION: System notification**
- [ ] Agent spawn status updates ← Future (Phase 3)
- [ ] Daily/weekly digest summaries ← Future (Phase 3)

**For mobile integration (Phase 3):**
- [x] Google Space (as mentioned) ← **DECISION: Planned for Phase 3**
- [ ] Push notifications (via Firebase/APNs?) ← Future (Phase 3)
- [ ] Email alerts ← Future (Phase 3)
- [ ] SMS alerts ← Not planned
- [ ] Slack/Discord ← Not planned
- [ ] Native mobile app? ← Not planned

**See:** [DECISIONS.md](../01-design/DECISIONS.md) for detailed rationale

### 4. Agent Integration
**What does "spawn agent" mean to you?**
- [ ] Create AI agent to work on the task (like this opencode session?)
- [ ] Assign task to an external service/API
- [ ] Generate subtasks automatically
- [ ] Schedule automated reminders
- [ ] Other?

### 5. Tech Stack Preferences
**Backend:**
- [ ] Node.js/Express
- [ ] Python/FastAPI
- [ ] Go
- [ ] Rust
- [ ] No preference

**Frontend:**
- [ ] React
- [ ] Vue
- [ ] Svelte
- [ ] Simple HTML/JS
- [ ] No UI needed (CLI only)

**Database:**
- [ ] SQLite (simple, local)
- [ ] PostgreSQL
- [ ] MySQL
- [ ] MongoDB
- [ ] Redis for cache + another DB

**Background jobs (for notifications/integrations/embeddings):**
- [x] In-process scheduler + DB persistence (APScheduler + SQLite tables) ← MVP
- [ ] systemd timer / cron running a `tgenie worker` command ← Alternative
- [ ] Redis/Celery ← Only if we need distributed workers later

### 6. User Interface Preferences
**Visual style:**
- [ ] Minimal/simple (like a text file)
- [ ] Rich UI with drag-drop
- [ ] Kanban board view
- [ ] Calendar view
- [ ] List view with filters
- [ ] Multiple views?

**Task management:**
- [ ] Keyboard shortcuts
- [ ] Bulk operations
- [ ] Search/filter
- [ ] Archive old tasks
- [ ] Export/backup data

### 7. Deployment & Infrastructure
**Where will this run?**
- [ ] Local machine only
- [ ] Home server/NAS
- [ ] Cloud (AWS/GCP/Azure?)
- [ ] VPS/Dedicated server

**Docker preferences:**
- [ ] Docker Compose for easy local setup
- [ ] Need to persist data volumes?
- [ ] Environment variables for configuration?
- [ ] Health checks for auto-restart?

### 8. Data Management
**Do you need:**
- [ ] Backup/restore functionality
- [ ] Export to CSV/JSON
- [ ] Sync across multiple devices
- [ ] API for programmatic access
- [ ] Webhooks for integration

### 9. Security & Access
- [ ] Single user (you only)
- [ ] Multi-user support (family/team)
- [ ] Authentication (username/password, OAuth, etc.)
- [ ] HTTPS/SSL
- [ ] VPN/private network only?

### 10. Email & Conversations Integration
**How do you want to capture from emails/conversations?**
- [ ] Forward emails to specific address
- [ ] Browser extension to extract from Gmail/Outlook
- [ ] Copy-paste text and auto-parse for task creation
- [ ] Gmail API integration
- [ ] Slack/Discord webhook
- [ ] Other?

---

## Questions to Answer (Original Notes)

Please provide:
1. Your preferred task entry methods (rank 1-5)
2. Required task metadata fields
3. Notification preferences and timing
4. What "spawn agent" should do
5. Tech stack preferences (or "no preference")
6. UI preference (minimal vs rich)
7. Where you'll host this
8. How you want to capture from emails/conversations
