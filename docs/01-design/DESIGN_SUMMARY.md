# Design Summary - Quick Reference

## What We're Building

An **interactive TUI-first, AI-native personal task manager** with:
- Conversational chat interface (like opencode)
- Gmail + GitHub attachment support
- RAG-powered semantic search
- Desktop notifications
- Docker containerization
- BYOK + OpenRouter support

## Key Differentiators vs Competitors

| Feature | dstask | Taskosaur | Our System |
|---------|---------|-----------|-------------|
| CLI-first | ✅ | ❌ | ✅ |
| AI chat | ❌ | ✅ | ✅ |
| RAG search | ❌ | ❌ | ✅ |
| Gmail integration | ❌ | ❌ | ✅ |
| GitHub attachments | ❌ | ❌ | ✅ |
| Desktop notifications | ❌ | ❌ | ✅ |
| BYOK support | ❌ | ✅ | ✅ |
| Personal-focused | ✅ | ❌ | ✅ |
| Simple architecture | ✅ | ❌ | ✅ |

## Tech Stack

### Backend
- **FastAPI** - Async, type-safe, Python-native
- **SQLAlchemy** - ORM, easy migrations
- **SQLite** - Simple, portable, can upgrade to Postgres
- **ChromaDB** - Local vector store for RAG
- **APScheduler** - Notification scheduling
- **plyer** - Cross-platform desktop notifications

### CLI
- **Typer** - Modern, type hints, auto-help
- **Rich** - Beautiful terminal output
- **Shell completion** - bash/zsh/fish support

### Web UI
- **HTMX + Jinja2** - Minimal JS, server-rendered
- **Tailwind CSS** - Rapid, modern styling
- **WebSocket** - Real-time chat streaming
- **No frameworks** - Lightweight, fast

### Integrations
- **Google API Python Client** - Gmail OAuth and fetching
- **PyGithub** - GitHub API for PRs/issues
- **OpenAI SDK** - OpenRouter + OpenAI + Anthropic support

### Deployment
- **Docker Compose** - One-command setup
- **Auto-start** - systemd service (optional)
- **Local-only** - No cloud dependencies

## User Journey

### Setup (5 minutes)
```bash
# Clone and setup
git clone https://github.com/user/personal-todo.git
cd personal-todo

# Configure
tgenie config --llm openrouter --api-key YOUR_KEY
tgenie config --gmail-auth  # Optional, opens browser
docker compose up -d

# Done! System running on http://localhost:8080
```

### Daily Use

**Morning - Check what's due:**
```bash
$ tgenie
You: What do I have due today?
🤖 You have 2 tasks due today:
  1. Review PR #123 [high]
  2. Client meeting [medium]
```

**Add task from email (using subcommand):**
```bash
# Found important email in Gmail
$ tgenie attach abc123 --type gmail --ref 18e4f7a2b3c
✓ Gmail attached to task abc123
```

**Get help prioritizing:**
```bash
$ tgenie
You: What should I focus on today?
🤖 Based on 3 pending tasks:
  • Start with PR #123 (high priority, 2 approvals)
  • Block 2 hours for client meeting prep
  • Work on authentication bug in afternoon
```

**Evening - Progress:**
```bash
$ tgenie done abc123
✓ Task completed
🔔 Desktop notification shows task completed

$ tgenie
You: What's left for tomorrow?
🤖 1 task due tomorrow:
  • Send project update (medium priority)
```

## Architecture Diagram

```
CLI (Typer)          Web UI (HTMX)          API (FastAPI)
    │                      │                         │
    └──────────────────────┼─────────────────────────┘
                           │
                           ▼
                    ┌─────────────────┐
                    │  Task Service  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │  SQLite  │  │ ChromaDB │  │  Gmail    │
        │  (Tasks) │  │  (RAG)   │  │  Service  │
        └──────────┘  └──────────┘  └──────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Notification    │
                    │ Scheduler      │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ Desktop Notify  │
                    │   (plyer)     │
                    └─────────────────┘
```

## Data Flow Examples

### Adding a Task
```mermaid
graph LR
    A[CLI: tgenie add] --> B[Task Service]
    B --> C[Save to SQLite]
    C --> D[Generate Embedding]
    D --> E[Store in ChromaDB]
    E --> F[Send Success Response]
    F --> G[CLI: ✓ Created]
```

### Chat Query
```mermaid
graph LR
    A[User: What's due?] --> B[LLM Intent Analysis]
    B --> C[Query SQLite]
    C --> D[Search ChromaDB]
    D --> E[Rerank Results]
    E --> F[Generate Response]
    F --> G[Stream to CLI/Web]
```

### Notification Trigger
```mermaid
graph LR
    A[Scheduler: Check every 5min] --> B{Task due in 24h?}
    B -->|Yes| C[Create Notification Record]
    B -->|No| A
    C --> D[Send Desktop Notify]
    D --> E[User Clicks]
    E --> F[Open Web UI / Mark Done]
    F --> G[Update Notification Status]
```

## File Structure

```
personal-todo/
├── backend/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── database.py             # SQLite + SQLAlchemy
│   ├── models/                # Pydantic schemas
│   │   ├── task.py
│   │   ├── attachment.py
│   │   └── chat.py
│   ├── services/              # Business logic
│   │   ├── task_service.py
│   │   ├── llm_service.py
│   │   ├── rag_service.py
│   │   ├── notification_service.py
│   │   └── integrations/
│   │       ├── gmail.py
│   │       └── github.py
│   └── templates/             # Jinja2 templates
│       ├── base.html
│       ├── chat.html
│       └── tasks.html
├── cli/
│   ├── __init__.py
│   ├── main.py                 # Typer CLI
│   ├── commands/
│   │   ├── add.py
│   │   ├── list.py
│   │   ├── chat.py
│   │   └── ...
│   └── utils.py               # Rich output helpers
├── tests/
│   ├── test_tasks.py
│   ├── test_chat.py
│   └── test_rag.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Implementation Roadmap

**Source of truth:** `docs/02-implementation/PR-PLANS.md` (UX-first execution order + dependency diagram).

High-level sequence:
1. Foundation (DB + Task API)
2. Interface (interactive TUI tasks MVP)
3. Chat (LLM + chat inside the TUI)
4. Context (attachments + link detection)
5. Early value (notifications and/or integrations)
6. Intelligence (RAG + semantic search)
7. Secondary UIs (web UI)
8. Shipping (deployment + docs)

## Configuration Files

### ~/.taskgenie/config.toml
```toml
[llm]
provider = "openrouter"
model = "anthropic/claude-3-haiku"
api_key = "sk-or-v1-..."

[gmail]
enabled = true
credentials_path = "~/.taskgenie/credentials.json"

[github]
enabled = true
token = "ghp_..."

[notifications]
enabled = true
schedule = ["24h", "6h"]
sound_enabled = true
quiet_hours = {"start": "22:00", "end": "08:00"}

[database]
path = "~/.taskgenie/data/taskgenie.db"

[web]
port = 8080
host = "localhost"
```

## API Endpoints

### Tasks
- `POST /api/v1/tasks` - Create task
- `GET /api/v1/tasks` - List tasks (with filters)
- `GET /api/v1/tasks/{id}` - Get task details
- `PATCH /api/v1/tasks/{id}` - Update task
- `DELETE /api/v1/tasks/{id}` - Delete task

### Attachments
- `POST /api/v1/attachments` - Create attachment
- `GET /api/v1/attachments/{id}` - Get attachment
- `DELETE /api/v1/attachments/{id}` - Delete attachment

### Chat
- `POST /api/v1/chat` - Send chat message (streaming)
- `GET /api/v1/chat/stream` - SSE stream
- `GET /api/v1/chat/history/{session_id}` - Get conversation

### Search
- `GET /api/v1/search` - Keyword search
- `GET /api/v1/search/semantic` - RAG search

## CLI Commands Reference

```bash
# Interactive TUI (default - chat-first)
tgenie                              # Start interactive TUI
tgenie "What tasks are due?"        # One-shot chat query

# Task Management (subcommands for scripting)
tgenie add "Task title" [-d desc] [-e eta] [-p priority] [-a attachment]
tgenie list [--status STATUS] [--priority PRI] [--due DATE]
tgenie show <task_id>
tgenie edit <task_id> [options]
tgenie done <task_id>
tgenie delete <task_id>

# Attachments
tgenie attach <task_id> --type TYPE --ref REFERENCE

# Configuration
tgenie config                       # Show current config
tgenie config --llm PROVIDER        # Set LLM provider
tgenie config --api-key KEY         # Set API key
tgenie config --gmail-auth          # Configure Gmail
tgenie config --notify SCHEDULE     # Set notification schedule

# Web UI
tgenie ui                           # Launch web interface
tgenie ui --port 9000               # Specify port

# Data (backup/restore + migrations)
tgenie db dump --out backup.sql
tgenie db restore --in backup.sql
tgenie db upgrade
tgenie search <query>
```

## Design Documents Created

1. **DESIGN_ARCHITECTURE.md** - System architecture, service boundaries
2. **DESIGN_CLI.md** - Detailed CLI command design with examples
3. **DESIGN_DATA.md** - Database schemas, Pydantic models, JSON examples
4. **DESIGN_CHAT.md** - AI/chat flow, RAG integration, prompt engineering
5. **DESIGN_WEB.md** - Web UI pages, components, HTMX interactions
6. **DESIGN_NOTIFICATIONS.md** - Notification system, scheduling, templates

## Next Steps

### For User Review
- [ ] Review architecture (DESIGN_ARCHITECTURE.md)
- [ ] Review CLI design (DESIGN_CLI.md)
- [ ] Review data models (DESIGN_DATA.md)
- [ ] Review chat flow (DESIGN_CHAT.md)
- [ ] Review web UI (DESIGN_WEB.md)
- [ ] Review notifications (DESIGN_NOTIFICATIONS.md)

### After Approval
- [ ] Finalize tech stack
- [ ] Create repository structure
- [ ] Set up development environment
- [ ] Begin Phase 1 implementation

## Key Decisions Made

### Why Python/FastAPI?
- **AI ecosystem:** Python has best LLM/RAG libraries
- **Async native:** FastAPI built for async operations
- **Type hints:** Type-safe, easy maintenance
- **Simpler:** Single language, no separate backend/frontend

### Why SQLite + ChromaDB?
- **Local only:** No external services needed
- **Simple:** Single-file database, easy backup
- **Portable:** Works in Docker, easy to migrate later
- **Fast:** Good enough for personal use

### Why Interactive TUI-first?
- **Natural interaction:** Chat-first feels more intuitive than memorizing commands
- **Context-aware:** Conversation history helps with follow-up questions
- **Scriptable:** Subcommands (`tgenie add`, `tgenie list`) can be automated
- **SSH-friendly:** Works perfectly remotely
- **Familiar:** Like modern CLI tools (git, docker) but with AI assistance

### Why Chat Interface?
- **Natural:** Ask "what's due?" instead of `tgenie list --status pending`
- **Context-aware:** Remembers conversation
- **RAG-powered:** Searches across all attachments
- **Actionable:** Suggests and executes actions directly

## Risks & Mitigations

### Risk 1: Complexity creep
**Mitigation:**
- Strict MVP scope (8 weeks)
- Phase-based development
- Ship and iterate

### Risk 2: RAG quality
**Mitigation:**
- Start with keyword search
- Add RAG in Phase 2
- User feedback loop

### Risk 3: Integration reliability
**Mitigation:**
- Graceful degradation (API failures)
- Caching strategies
- Clear error messages

### Risk 4: User adoption
**Mitigation:**
- Great CLI UX (completion, colors)
- Clear documentation
- Quick onboarding (5-minute setup)
- Natural chat interface

## Success Metrics

### MVP (Week 8)
- Working CLI with CRUD
- Chat interface with AI
- Docker container running
- Desktop notifications
- 100 GitHub stars

### Phase 2 (Week 16)
- Gmail integration
- GitHub integration
- RAG search
- 500 GitHub stars

### Phase 3 (Week 52)
- 2,000 GitHub stars
- 10 active contributors
- Featured in tech communities

---

**Ready to proceed with implementation?**
