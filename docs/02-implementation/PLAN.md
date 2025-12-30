# Personal TODO List Application - Project Plan

## Core Requirements
- [ ] Task management with rich metadata (description, references, links, ETA)
- [ ] Docker container with auto-start capability
- [ ] Local notifications (initially)
- [ ] Future: Mobile notifications (Google Space integration)
- [ ] Quick/easy task entry from various sources
- [ ] Agent spawning capability from tasks

---

## User Requirements (Confirmed)

### 1. Primary Entry Point
- **Interactive TUI as main interface** - Python application running locally (managed by systemd/launchd or manual start)
- Accessible via `tgenie` command (defaults to interactive mode with chat)
- Non-interactive subcommands (`tgenie add`, `tgenie list`, etc.) available for scripting

### 2. Task Entry & Information Management
- **Document/email/PR attachment** - Link relevant emails (GMail), documents, GitHub PRs, etc. to tasks
- Goal: Reduce time spent finding information for each task

### 3. Tech Stack (Final)
- **Runtime**: Python 3.11+
- **Package Manager**: `uv` (modern, fast replacement for pip/poetry)
- **Backend**: FastAPI (async, clean, extensible)
- **CLI**: Typer (modern, type-safe CLI framework)
- **Database**: SQLite + SQLAlchemy (Async)
- **Vector Store**: ChromaDB (Local RAG)
- **Notifications**: `plyer` (Native OS notifications)
- **Linting/Formatting**: `ruff`
- **Type Checking**: `mypy`

### 4. Notifications
- **Default triggers**: 24 hours before, 6 hours before (if not marked complete)
- **Desktop notifications** - Clickable, opens relevant task
- Local system notifications (Linux/Mac/Windows) via `plyer`

### 5. Chat Interface
- **Chat-based interaction** - Not keyword search
- AI agent searches within TODO information and attached documents
- Natural language queries like "What tasks need attention this week?"

### 6. LLM Integration
- **BYOK (Bring Your Own Key)** support
- **Free models via OpenRouter** (similar to opencode)
- Flexible model switching

---

## Clarifying Questions (Resolved)

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

## Proposed Architecture (Updated)

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface                            │
│  ┌──────────┐           ┌──────────────────┐                │
│  │ CLI Tool │           │  Web Chat UI     │                │
│  │ (Typer)  │           │  (localhost:8080) │                │
│  └────┬─────┘           └────────┬─────────┘                │
└───────┼──────────────────────────┼──────────────────────────┘
        │                          │
        │ HTTP/WebSocket           │
        └──────────┬───────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Task API     │  │ Chat API     │  │ LLM Integration  │  │
│  │ (CRUD)       │  │ (Agent)      │  │ (OpenRouter/     │  │
│  │              │  │              │  │  BYOK)           │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
└─────────┼─────────────────┼──────────────────┼────────────┘
          │                 │                  │
          ▼                 ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ SQLite DB    │   │ RAG/Vector    │   │ External     │
│ (Tasks,      │   │ Store         │   │ Integrations │
│  Attachments)│   │ (For doc      │   │ (Gmail API,  │
│              │   │  search)      │   │  GitHub API) │
└──────────────┘   └──────────────┘   └──────────────┘
                          │
                          ▼
                 ┌────────────────┐
                 │ Background Jobs│
                 │ (APScheduler + │
                 │  SQLite state  │
                 │  tables)       │
                 └────────────────┘
                          │
                          ▼
                 ┌────────────────┐
                 │ Notifications  │
                 │ (Desktop/Web)  │
                 └────────────────┘
```

---

## Tech Stack (Final)

### Core
- **Backend**: Python 3.11+ with FastAPI (async, clean, extensible)
- **CLI**: Typer (modern, type-safe CLI framework)
- **Database**: SQLite (simple, local) + SQLAlchemy (ORM, easy to migrate to Postgres)
- **Background Jobs**: APScheduler (in-process) + SQLite state tables (no external queue for MVP; Redis/Celery optional later)

### AI/LLM
- **LLM Provider**: OpenAI SDK (supports OpenRouter, BYOK, multiple models)
- **RAG/Vector Store**: ChromaDB (local, no external service needed) or FAISS
- **Prompt Management**: Simple template system

### Integrations
- **GMail**: Google API Python Client
- **GitHub**: PyGithub
- **Desktop Notifications**: plyer (cross-platform)

### Frontend
- **Web UI**: HTMX or Alpine.js (minimal JS, server-rendered) + Jinja2 templates
- **Terminal UI**: Rich + Textual (for better CLI experience)

### Development
- **Testing**: Pytest
- **Linting**: Ruff (fast, Python-only)
- **Docker**: Docker Compose for local development

---

## Proposed Features - Phase 1 (MVP)

### Core Functionality
- **Interactive TUI** - Primary interface entered via `tgenie` command (Typer-based, chat-first)
- **CLI subcommands** - Non-interactive commands for scripting (`tgenie add`, `tgenie list`, etc.)
- **Web chat UI** - Secondary interface (localhost:8080, HTMX + Jinja2)
- **Task CRUD** - Create, Read, Update, Delete, List tasks
- **Task fields**:
  - Title, Description, ETA
  - Status (pending, in_progress, completed)
  - Attachments/links (Gmail, GitHub PRs, docs)
- **Chat interface** - Ask questions about tasks using natural language
- **Desktop notifications** - 24hr and 6hr before ETA (if not complete)
- **Docker Compose** - Auto-start on boot
- **SQLite database** - Simple local storage
- **BYOK support** - OpenRouter, OpenAI, Anthropic, local models
- **FastAPI backend** - Async, type-safe, Python-native

### Unique Differentiators (vs. Competitors)
- ✅ **Interactive TUI-first** with AI chat as primary mode (no other project has both)
- ✅ **RAG-powered search** across tasks and attachments (unique)
- ✅ **Gmail + GitHub integration** for attachments (no CLI tool has this)
- ✅ **Desktop notifications** from Docker container (completely missing)
- ✅ **Personal-focused** (most AI tools are team-focused)
- ✅ **Simple architecture** (vs. Taskosaur's 4+ services)

See MARKET_RESEARCH.md for detailed competitor analysis.

### CLI Examples

**Interactive mode (default):**
```bash
tgenie
# Opens interactive TUI with chat as primary mode
# "What tasks are due this week?"
# "Show me tasks related to frontend"
```

**Add task (subcommand for scripting):**
```bash
tgenie add "Review PR #123" --description "Fix authentication bug" --eta "2025-01-15" --attach "github:owner/repo/pull/123"
```

**List tasks:**
```bash
tgenie list
tgenie list --status pending
```

**Add attachment to task:**
```bash
tgenie attach <task_id> --gmail "msg:abc123" --github "https://github.com/..."
```

**Task details:**
```bash
tgenie show <task_id>
```

### Web Chat UI Examples

```
User: What tasks do I need to work on today?

AI: You have 2 tasks due today:
1. Review PR #123 (ETA: Today 2:00 PM)
   - Attached: GitHub PR #123
2. Send project update email (ETA: Today 5:00 PM)
   - Attached: Gmail thread

Would you like me to open any of these?

User: Show me the PR #123 details

AI: [Displays PR info from GitHub, description, files changed, etc.]
```

### Data Structure

```python
class Task(Base):
    id: str (UUID)
    title: str
    description: str
    eta: datetime
    status: str (pending, in_progress, completed)
    created_at: datetime
    updated_at: datetime

class Attachment(Base):
    id: str (UUID)
    task_id: str (FK)
    type: str (gmail, github, document, url)
    reference: str (URL, message ID, etc.)
    title: str
    content: str (cached content for search)
    metadata: dict (additional info)
    created_at: datetime
```

### LLM Integration

```python
# Model configuration
LLM_PROVIDERS = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "anthropic/claude-3-haiku"
    },
    "byok": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4-turbo"
    }
}
```

---

## Proposed Features - Phase 2

### Enhanced Integrations
- **GMail integration** - Fetch email content, attach to tasks
- **GitHub integration** - Fetch PR/issue details, auto-link
- **Document caching** - Store content for RAG search
- **Vector search** - Semantic search across tasks and attachments
- **Attachment preview** - Show content in chat UI

### RAG System
```bash
tgenie
User: "Show me all tasks related to authentication"

AI: [Searches task descriptions and cached attachment content]
Found 3 tasks:
1. Review PR #123 - mentions "authentication bug" and "JWT token"
2. Update auth service - description talks about OAuth flow
3. Security audit - Gmail thread references login issues
```

### CLI Enhancements
```bash
# Quick attach from clipboard
tgenie attach <task_id> --paste

# Search by content
tgenie search "authentication bug"

# Export tasks
tgenie export --format json
tgenie export --format markdown
```

---

## Proposed Features - Phase 3

### Advanced Notifications
- **Google Space integration** - Mobile notifications
- **Notification schedules** - Customize triggers
- **Snooze functionality** - Temporarily dismiss notifications
- **Notification history** - Track all alerts

### Task Management
- **Task priorities** - High, Medium, Low
- **Tags** - Categorize tasks
- **Subtasks** - Break down complex tasks
- **Dependencies** - Block tasks on others

### AI Features
- **Task summarization** - Generate summaries from attachments
- **Related tasks** - Suggest similar tasks
- **Auto-tagging** - AI suggests tags based on content
- **Priority suggestions** - AI suggests priority based on context

### Productivity
- **Daily digest** - Email/chat summary of tasks
- **Weekly review** - Stats and insights
- **Completion trends** - Track productivity over time

---

## Project Structure

```
personal-todo/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── pyproject.toml
├── README.md
├── PLAN.md
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuration
│   ├── database.py          # Database setup
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── task.py
│   │   ├── attachment.py
│   │   └── notification.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── task.py
│   │   ├── attachment.py
│   │   └── chat.py
│   ├── api/                 # API routes
│   │   ├── __init__.py
│   │   ├── tasks.py
│   │   ├── chat.py
│   │   └── attachments.py
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── task_service.py
│   │   ├── llm_service.py
│   │   ├── rag_service.py
│   │   ├── notification_service.py
│   │   └── integrations/
│   │       ├── __init__.py
│   │       ├── gmail.py
│   │       └── github.py
│   ├── cli/                 # CLI commands
│   │   ├── __init__.py
│   │   └── main.py          # Typer CLI
│   └── templates/           # Jinja2 templates for web UI
│       ├── base.html
│       ├── chat.html
│       └── tasks.html
├── tests/
│   ├── __init__.py
│   ├── test_tasks.py
│   ├── test_chat.py
│   └── test_llm.py
└── data/                    # SQLite and vector store
    ├── taskgenie.db
    └── chroma/
```

---

## Next Steps

1. **Answer clarifying questions above** to refine requirements
2. **Choose tech stack** based on preferences
3. **Create MVP architecture** with specific implementation details
4. **Set up development environment** (Docker Compose structure)
5. **Implement core features** incrementally

---

## Questions to Answer

Please provide:
1. Your preferred task entry methods (rank 1-5)
2. Required task metadata fields
3. Notification preferences and timing
4. What "spawn agent" should do
5. Tech stack preferences (or "no preference")
6. UI preference (minimal vs rich)
7. Where you'll host this
8. How you want to capture from emails/conversations

---

## Version History
- v0.1 - Initial plan with clarifying questions (2025-01-28)
