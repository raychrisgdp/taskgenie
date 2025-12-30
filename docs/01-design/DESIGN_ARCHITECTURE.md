# System Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interfaces                     │
├──────────────────────┬──────────────────────┬─────────────┤
│                      │                      │             │
│      CLI (Primary)    │   Web UI (Rich)    │   API (Dev) │
│   Typer + Rich      │   HTMX + Jinja2     │  FastAPI     │
│                      │                      │             │
└──────────┬───────────┴──────────┬───────────┴───────┘
           │                      │
           │                      │
           │       HTTP/WebSocket │
           │                      │
           ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                        │
│  ┌─────────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  Task API   │  │ Chat API │  │ Notification  │  │
│  │  (CRUD)     │  │ (LLM)    │  │   Service    │  │
│  └──────┬──────┘  └────┬─────┘  └──────┬───────┘  │
│         │                 │                 │           │
│  ┌──────┴────────────────┴─────────────────┴───────┐  │
│  │              SQLAlchemy ORM                      │  │
│  └────────────────────────┬───────────────────────────────┘  │
└───────────────────────────────┼───────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌──────────────┐   ┌──────────────┐
│  SQLite DB    │   │ ChromaDB     │   │ Scheduler    │
│ (Tasks,       │   │ (Vectors)    │   │ (APScheduler)│
│  Attachments) │   │              │   │              │
└───────────────┘   └──────────────┘   └──────────────┘
                                │
                                │
        ┌───────────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌──────────────┐   ┌──────────────┐
│  Gmail API    │   │ GitHub API   │   │  Desktop     │
│  (Python)    │   │  (PyGithub)  │   │  Notify      │
│              │   │              │   │  (plyer)    │
└───────────────┘   └──────────────┘   └──────────────┘
```

## Key Design Principles

1. **Interactive TUI-first** - Primary UX is interactive mode (entered via `tgenie`) with chat as main capability
2. **CLI subcommands for scripting** - Non-interactive commands (`tgenie add`, `tgenie list`, etc.) for automation
3. **AI-native** - Chat as primary interface within TUI, not bolted on
4. **Simple architecture** - One language (Python), minimal services
5. **Local-first** - All data stored locally, sync optional later
6. **Extensible** - Easy to add new integrations/LLM providers

## Service Boundaries

### CLI Service
- **Interactive TUI mode** (default): Entered via `tgenie`, chat-first interface
- **Subcommands** (for scripting): `tgenie add`, `tgenie list`, `tgenie show`, `tgenie edit`, `tgenie delete`, `tgenie attach`
- Output: formatted text (Rich library)
- Input: command-line arguments, interactive prompts
- State: Session state for interactive mode (stateless for subcommands, calls API)

### Web UI Service
- Pages: chat, tasks, task details, settings
- Tech: HTMX + Jinja2 + Tailwind CSS
- Updates: WebSocket for real-time chat
- Auth: None (local, single-user)

### API Service
- Endpoints: REST for CRUD, WebSocket for chat
- Format: JSON
- Auth: API key (optional for local use)
- Docs: OpenAPI/Swagger auto-generated

### Task Service
- CRUD operations on tasks
- Status management
- Search (keyword + RAG)

### LLM Service
- Multi-provider: OpenRouter, OpenAI, Anthropic, local
- Chat completion
- Prompt management
- Streaming responses

### Notification Service
- Desktop notifications (plyer)
- Scheduling: 24hr, 6hr before ETA
- History tracking
- Click actions (open task, mark done)

### Integration Service
- Gmail: OAuth, fetch, parse, attach
- GitHub: OAuth (optional), fetch, parse, attach
- **Provider Protocol**: Common interface for all integrations (`match_url`, `fetch_content`)
- **Auto-Discovery**: Link detection service to auto-attach URLs
- Extensible: Add new integrations by implementing the Provider Protocol

### Link Detection Service
- Parses task content (title, description) for URLs
- Matches URLs against registered Integration Providers
- Auto-triggers attachment creation for matched links

### RAG Service
- Embedding generation
- Vector storage (ChromaDB)
- Semantic search
- Context retrieval for chat
