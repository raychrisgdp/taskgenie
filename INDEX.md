# Personal TODO System - Design Documents

## 📋 Overview

This repository contains comprehensive design documents for building a **CLI-first, AI-native personal task management system**.

## 📖 Design Documents

### 1. [MARKET_RESEARCH.md](./MARKET_RESEARCH.md)
**What:** Detailed analysis of 40+ open-source competitors
**Includes:**
- CLI tools (dstask, t, etc.)
- AI/chat-based tools (Taskosaur, todo-for-ai)
- Self-hosted solutions (Super Productivity, etc.)
- Gmail integration tools
- BYOK/OpenRouter support projects
- Terminal/chat UI tools
- Vector/RAG search implementations

**Key Finding:** No single project combines CLI + AI Chat + Gmail + RAG + Notifications in a simple, personal-focused package.

### 2. [COMPARISON_SUMMARY.md](./COMPARISON_SUMMARY.md)
**What:** Quick reference with market gap analysis
**Includes:**
- Top 5 closest competitors
- Unique feature comparison matrix
- Why we win against each competitor
- Market segments we capture
- Recommended positioning and taglines
- Technical advantages
- Risks and mitigations
- Success metrics

**Key Finding:** Clear opportunity exists. We're first to market with this specific combination.

### 3. [DESIGN_ARCHITECTURE.md](./DESIGN_ARCHITECTURE.md)
**What:** High-level system architecture
**Includes:**
- System overview diagram
- Service boundaries (CLI, Web UI, API, Task, LLM, Notification, Integration, RAG)
- Key design principles
- Technology choices rationale

**Key Decisions:** Python/FastAPI, SQLite, ChromaDB, single language, local-first

### 4. [DESIGN_CLI.md](./DESIGN_CLI.md)
**What:** Detailed CLI command design
**Includes:**
- All commands: add, list, show, edit, delete, chat, attach, ui, config, search, export/import
- Options and flags for each command
- Rich terminal output examples
- Interactive prompts
- Shell integration (completion, aliases)
- Configuration file structure

**Key Design:** Scriptable, familiar, fast, conversational

### 5. [DESIGN_DATA.md](./DESIGN_DATA.md)
**What:** Database schemas and data models
**Includes:**
- SQLite table definitions (tasks, attachments, notifications, chat_history, config)
- Pydantic schemas for API
- JSON examples for all entities
- RAG document structure
- Data relationships diagram
- Indexes for performance
- Migration strategy
- Storage locations (file system, Docker volumes)
- Privacy and security considerations

**Key Design:** Simple, extensible, privacy-focused

### 6. [DESIGN_CHAT.md](./DESIGN_CHAT.md)
**What:** AI/chat flow and RAG integration
**Includes:**
- Chat experience flow diagram
- Query types and handling (task info, actions, attachments, RAG search, suggestions)
- RAG integration architecture
- Document storage for vector search
- Search strategy (embedding + rerank)
- Prompt engineering (system prompt, context prompt)
- Conversation management (sessions, context tracking)
- Streaming responses
- Error handling and graceful degradation
- Multi-provider LLM support
- Testing scenarios

**Key Design:** Natural, conversational, context-aware, streaming

### 7. [DESIGN_WEB.md](./DESIGN_WEB.md)
**What:** Web UI pages and components
**Includes:**
- Page layouts: Chat, Tasks, Task Detail, Settings
- Component library (Message bubble, Action button, Task card)
- HTMX interactions (filtering, streaming, dynamic updates)
- Color scheme (status, priority, accents)
- Responsive design (mobile, tablet, desktop)
- Accessibility features
- Performance optimizations

**Key Design:** Simple, fast, server-rendered, minimal JS

### 8. [DESIGN_NOTIFICATIONS.md](./DESIGN_NOTIFICATIONS.md)
**What:** Desktop notification system
**Includes:**
- Notification types (deadline reminders, overdue alerts, system notifications)
- System architecture with scheduler
- Database schema (notifications table)
- Scheduling logic (24h, 6h before ETA)
- Desktop notification implementation (plyer, platform-specific)
- Notification templates
- User preferences
- Notification history
- Error handling and retry logic
- Privacy considerations
- Testing scenarios
- Future enhancements (mobile integration)

**Key Design:** Timely, actionable, cross-platform, configurable

### 9. [DESIGN_SUMMARY.md](./DESIGN_SUMMARY.md)
**What:** Executive summary tying everything together
**Includes:**
- What we're building
- Key differentiators vs competitors
- Tech stack summary
- User journey examples
- Architecture diagram
- Data flow examples
- File structure
- Implementation timeline (Phase 1-3)
- Configuration files
- API endpoints reference
- CLI commands reference
- Key decisions made
- Risks and mitigations
- Success metrics

**Key Summary:** Ready-to-build design, 8-week MVP plan

---

## 🚀 Quick Start

### Review Order
1. **Read** `DESIGN_SUMMARY.md` - Get overall picture
2. **Deep dive** into areas of interest:
   - For architecture: `DESIGN_ARCHITECTURE.md`
   - For CLI: `DESIGN_CLI.md`
   - For data: `DESIGN_DATA.md`
   - For AI/chat: `DESIGN_CHAT.md`
   - For web UI: `DESIGN_WEB.md`
   - For notifications: `DESIGN_NOTIFICATIONS.md`
3. **Validate** market analysis: `MARKET_RESEARCH.md` and `COMPARISON_SUMMARY.md`

### Before Approval
Ask yourself:
- [ ] Does the CLI-first approach match my needs?
- [ ] Is the chat interface natural and helpful?
- [ ] Do I understand how notifications will work?
- [ ] Is the tech stack (Python/FastAPI) acceptable?
- [ ] Are the integration priorities (Gmail, GitHub) correct?
- [ ] Do I agree with the 8-week MVP timeline?
- [ ] Do the data models capture what I need?
- [ ] Is the architecture simple enough?

### After Approval
- [ ] Confirm tech stack
- [ ] Confirm features for MVP (Phase 1)
- [ ] Create repository structure
- [ ] Set up development environment
- [ ] Begin implementation

---

## 📊 Key Decisions Summary

| Area | Decision | Rationale |
|-------|----------|-----------|
| **Primary interface** | CLI | Scriptable, SSH-friendly, familiar |
| **Web UI** | Secondary (HTMX) | Rich experience without complexity |
| **TUI** | Optional (Phase 3) | Can be added later |
| **Backend** | FastAPI (Python) | AI ecosystem, async, type-safe |
| **Database** | SQLite | Simple, local, portable |
| **Vector store** | ChromaDB | Local, Python-native, no external service |
| **LLM providers** | OpenRouter + BYOK | 100+ models, free options, flexibility |
| **Frontend** | HTMX + Jinja2 | Minimal JS, server-rendered, fast |
| **Notifications** | plyer | Cross-platform, works in Docker |
| **Integrations** | Gmail + GitHub | Covers main external sources |
| **Chat style** | Conversational | Like opencode, natural, context-aware |
| **RAG approach** | ChromaDB + rerank | Local, semantic search |
| **Deployment** | Docker Compose | One-command setup, auto-start |
| **Scope** | Personal-focused | Simpler than team tools |
| **Architecture** | Monolith with services | Simpler than microservices |

---

## 🎯 MVP Scope (Weeks 1-8)

**Must Have:**
- ✅ CLI with add, list, show, edit, delete, chat commands
- ✅ Task fields: title, description, status, priority, ETA
- ✅ Attachments: Gmail messages, GitHub PRs/issues, URLs
- ✅ Chat interface with AI responses (non-RAG initially)
- ✅ Desktop notifications: 24h, 6h before ETA
- ✅ Docker containerization
- ✅ SQLite database
- ✅ BYOK + OpenRouter support
- ✅ FastAPI backend
- ✅ Web UI with chat and task pages

**Nice to Have (Phase 2):**
- ⬜ RAG-powered search
- ⬜ Gmail OAuth and fetching
- ⬜ GitHub integration
- ⬜ Shell completion
- ⬜ Export/import
- ⬜ Notification history

**Out of Scope:**
- ❌ TUI (Phase 3)
- ❌ Multi-user
- ❌ Real-time collaboration
- ❌ Mobile app
- ❌ Task dependencies
- ⬜ Subtasks

---

## 📋 Implementation Checklist

### Week 1-2: Core Infrastructure
- [ ] Create repository structure
- [ ] Set up FastAPI backend
- [ ] Create SQLite database with migrations
- [ ] Implement Task model and schemas
- [ ] Create Dockerfile and docker-compose.yml
- [ ] Set up pyproject.toml and requirements.txt

### Week 3-4: CLI Commands
- [ ] Implement `add` command
- [ ] Implement `list` command with filters
- [ ] Implement `show` command
- [ ] Implement `edit` command
- [ ] Implement `delete` and `done` commands
- [ ] Add Rich library for beautiful output
- [ ] Add shell completion (bash/zsh/fish)

### Week 5-6: AI Integration
- [ ] Implement LLM service with OpenRouter
- [ ] Implement BYOK support (OpenAI, Anthropic)
- [ ] Create chat endpoint
- [ ] Implement streaming responses
- [ ] Add basic prompt management
- [ ] Implement `chat` CLI command

### Week 7-8: Web UI & Notifications
- [ ] Create Jinja2 templates (base, chat, tasks)
- [ ] Implement chat page with WebSocket streaming
- [ ] Implement tasks list page
- [ ] Implement task detail page
- [ ] Integrate Tailwind CSS
- [ ] Set up plyer for desktop notifications
- [ ] Implement notification scheduler (APScheduler)
- [ ] Create notification service (24h, 6h before ETA)
- [ ] Test Docker Compose setup

---

## 📞 Questions & Feedback

### For Review
Please review and provide feedback on:
1. **Overall architecture** - Does it make sense?
2. **CLI design** - Are commands intuitive?
3. **Data models** - Do they capture what you need?
4. **Chat interface** - Does it feel natural?
5. **Web UI** - Is the page layout good?
6. **Notifications** - Will this work for your workflow?
7. **Tech stack** - Any concerns with Python/FastAPI?
8. **Timeline** - Is 8 weeks realistic for MVP?
9. **Scope** - Anything missing or over-scoped?
10. **Risk** - Any major risks not addressed?

### Contact
Questions? Feedback? Concerns?

---

## 📦 File Index

| Document | Purpose | Status |
|----------|---------|--------|
| MARKET_RESEARCH.md | Competitor analysis | ✅ Complete |
| COMPARISON_SUMMARY.md | Market gap summary | ✅ Complete |
| DESIGN_ARCHITECTURE.md | System architecture | ✅ Complete |
| DESIGN_CLI.md | CLI command design | ✅ Complete |
| DESIGN_DATA.md | Database & models | ✅ Complete |
| DESIGN_CHAT.md | AI/chat flow | ✅ Complete |
| DESIGN_WEB.md | Web UI design | ✅ Complete |
| DESIGN_NOTIFICATIONS.md | Notification system | ✅ Complete |
| DESIGN_SUMMARY.md | Executive summary | ✅ Complete |
| PLAN.md | Original requirements | ✅ Complete |

---

**Ready to build? Review documents and let's start implementation!**
