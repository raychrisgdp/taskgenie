# Open Source TODO/Task Management - Market Research

## Executive Summary

Research conducted on existing open-source task management tools reveals significant gaps in the market. While many tools excel at specific features (CLI, AI, Docker, chat), **no single project combines all the key requirements** identified for this personal TODO system.

---

## 1. CLI-Based Task Managers

### dstask (1.1k stars, Go)
**Repository:** https://github.com/naggie/dstask

**Features:**
- ✅ Terminal-based todo manager
- ✅ Git-powered sync
- ✅ Markdown notes per task
- ✅ Priority system (P0-P3)
- ✅ Context/tags filtering
- ✅ Shell completions
- ✅ Single binary

**Missing for Our Requirements:**
- ❌ No web UI
- ❌ No AI/chat interface
- ❌ No desktop notifications
- ❌ No email/Gmail integration
- ❌ No external attachments (GitHub PRs, etc.)
- ❌ No Docker containerization (though portable binary)

**Verdict:** Excellent CLI tool, but lacks AI and modern features

---

### t (794 stars, Python)
**Repository:** https://github.com/sjl/t

**Philosophy:** "For people that want to finish tasks, not organize them"

**Features:**
- ✅ Minimalist CLI design
- ✅ Plain text storage (editable in any editor)
- ✅ Version control friendly (random IDs reduce merge conflicts)
- ✅ Simple add/list/finish/edit

**Missing for Our Requirements:**
- ❌ No priorities/tags
- ❌ No due dates
- ❌ No web UI
- ❌ No AI
- ❌ No notifications
- ❌ No attachments

**Verdict:** Too minimal for our use case

---

### Other CLI Tools Found
- **todo-cli** (francoischalifour) - Node.js based
- **taskit** (Pradumnasaraf) - Simple CRUD CLI
- **tmgr** (CharlieKarafotias) - Task manager CLI
- **task-book** (basilioss/mdt) - Markdown-based

**Common Gap:** All focus on basic CRUD, none have AI/chat, notifications, or attachments

---

## 2. AI/Chat-Based Task Managers

### Taskosaur (244 stars, TypeScript/Node.js)
**Repository:** https://github.com/Taskosaur/Taskosaur

**Features:**
- ✅ Conversational AI task execution (in-app chat)
- ✅ Self-hosted with Docker
- ✅ BYOK support (OpenAI, Anthropic, OpenRouter, local models)
- ✅ Full project management (Kanban, sprints, dependencies)
- ✅ Browser automation for AI execution
- ✅ Real-time collaboration
- ✅ RESTful API + WebSocket

**Missing for Our Requirements:**
- ❌ CLI-first (web-first design)
- ❌ No Gmail integration (only email notifications)
- ❌ No RAG/search across attachments
- ❌ Team-focused (not personal)
- ❌ Complex architecture (NestJS + Next.js + Redis + Postgres)

**Verdict:** Most feature-complete, but over-engineered for personal use, CLI secondary

---

### Todo for AI (768 stars, Python/React)
**Repository:** https://github.com/todo-for-ai/todo-for-ai

**Features:**
- ✅ MCP (Model Context Protocol) integration for AI assistants
- ✅ Docker ready
- ✅ Gmail integration (for notifications)
- ✅ GitHub integration (OAuth)
- ✅ Project management with AI
- ✅ RESTful API

**Missing for Our Requirements:**
- ❌ AI assistant-focused, not personal productivity
- ❌ No CLI tool
- ❌ No chat interface (MCP is different)
- ❌ No RAG/search across tasks
- ❌ Team-focused features
- ❌ Complex setup (multiple submodules)

**Verdict:** Good for AI workflow integration, but not for personal task management

---

### MasteryListGPT (curiousily)
**Repository:** https://github.com/curiousily/MasteryListGPT-Chat-with-your-ToDo-List-with-LangChain-and-ChatGPT

**Features:**
- ✅ Chat with TODO list using LangChain
- ✅ Uses ChatGPT

**Missing for Our Requirements:**
- ❌ No CLI
- ❌ No Docker
- ❌ No notifications
- ❌ No attachments
- ❌ Abandoned/old tech

**Verdict:** Proof of concept, not production-ready

---

### claude-task-master (eyaltoledano)
**Repository:** https://github.com/eyaltoledano/claude-task-master

**Features:**
- ✅ AI-powered task management
- ✅ Drop into Cursor, Lovable, Windsurf

**Missing for Our Requirements:**
- ❌ Editor-integrated (not standalone)
- ❌ No CLI
- ❌ No Docker
- ❌ No Gmail/attachments

**Verdict:** Integration-focused, not standalone system

---

## 3. Self-Hosted/Docker Task Managers

### Super Productivity (johannesjo)
**Repository:** https://github.com/johannesjo/super-productivity

**Features:**
- ✅ Docker container available
- ✅ Integrations: Jira, GitLab, GitHub, Open Project
- ✅ Timeboxing and time tracking
- ✅ Desktop app (Electron)

**Missing for Our Requirements:**
- ❌ Desktop app (not CLI first)
- ❌ No AI/chat
- ❌ No Gmail integration
- ❌ No notifications system
- ❌ Team/project focused

**Verdict:** Great productivity tool, but wrong paradigm (desktop vs CLI)

---

### Tasks.md (BaldissaraMatheus)
**Repository:** https://github.com/BaldissaraMatheus/Tasks.md

**Features:**
- ✅ Self-hosted, markdown file based
- ✅ Task management board
- ✅ Simple architecture

**Missing for Our Requirements:**
- ❌ No CLI
- ❌ No AI
- ❌ No Docker
- ❌ No notifications
- ❌ No attachments

**Verdict:** Simple, but lacks features

---

### tududi (chrisvel)
**Repository:** https://github.com/chrisvel/tududi

**Features:**
- ✅ Self-hosted task management
- ✅ Personal and team features
- ✅ Docker ready

**Missing for Our Requirements:**
- ❌ No CLI
- ❌ No AI
- ❌ No Gmail
- ❌ No notifications
- ❌ No RAG

**Verdict:** Traditional web app, no innovation

---

### moaitime (bobalazek)
**Repository:** https://github.com/bobalazek/moaitime

**Features:**
- ✅ All-in-one productivity (calendar, tasks, habits, notes, focus, mood)
- ✅ Self-hosted
- ✅ Modern tech stack

**Missing for Our Requirements:**
- ❌ Bloated (too many features)
- ❌ No CLI
- ❌ No AI
- ❌ No Gmail integration
- ❌ No RAG

**Verdict:** Over-engineered for simple task management

---

## 4. Gmail/Email Integration Tools

### Gmail2Notion (Mike7154)
**Repository:** https://github.com/Mike7154/Gmail2Notion

**Features:**
- ✅ Convert labeled Gmail emails to Notion tasks
- ✅ Optional GPT processing

**Missing for Our Requirements:**
- ❌ Only converts to Notion (not standalone)
- ❌ No task management
- ❌ No CLI
- ❌ No Docker

**Verdict:** Integration tool, not full system

---

### vikunja-mail-parser (weselinka)
**Repository:** https://github.com/weselinka/vikunja-mail-parser

**Features:**
- ✅ Read unread emails via IMAP
- ✅ Parse subject for project mapping
- ✅ Create tasks with email body as description
- ✅ Supports attachments
- ✅ Docker + cron

**Missing for Our Requirements:**
- ❌ Only integrates with Vikunja (external service)
- ❌ No standalone task management
- ❌ No AI

**Verdict:** Good email-to-task pattern, but needs custom implementation

---

### todoist-email-tasks (jango)
**Repository:** https://github.com/jango/todoist-email-tasks

**Features:**
- ✅ Generate tasks from starred (Gmail) or flagged (Outlook) emails

**Missing for Our Requirements:**
- ❌ Todoist-specific
- ❌ No standalone system
- ❌ Old (2015)

**Verdict:** Outdated, service-specific

---

### universal-inbox (universal-inbox)
**Repository:** https://github.com/universal-inbox/universal-inbox

**Features:**
- ✅ Manage notifications in one place
- ✅ Convert to tasks

**Missing for Our Requirements:**
- ❌ No CLI
- ❌ No AI
- ❌ No Docker
- ❌ Activity unknown

**Verdict:** Concept matches, but implementation unclear

---

### crewai-gmail-automation (tonykipkemboi, 164 stars)
**Repository:** https://github.com/tonykipkemboi/crewai-gmail-automation

**Features:**
- ✅ Multi-agent system for Gmail
- ✅ Categorizes emails
- ✅ CrewAI framework

**Missing for Our Requirements:**
- ❌ No task management
- ❌ Complex for personal use
- ❌ No CLI

**Verdict:** AI email processing, but no task integration

---

## 5. BYOK/OpenRouter Support

### llm-openrouter (simonw)
**Repository:** https://github.com/simonw/llm-openrouter

**Features:**
- ✅ LLM plugin for OpenRouter models
- ✅ 100+ models available

**Missing for Our Requirements:**
- ❌ Plugin only, no application
- ❌ No task management
- ❌ No CLI tool built-in

**Verdict:** Good reference for OpenRouter integration

---

### Alorse/llm-proxy
**Repository:** https://github.com/Alorse/llm-proxy

**Features:**
- ✅ Allows BYOK editors (Cursor, Continue) to use any OpenAI-compatible LLM

**Missing for Our Requirements:**
- ❌ Proxy only, no application

**Verdict:** Infrastructure tool, not user-facing

---

## 6. Terminal/Chat UI

### chatty (mipsel64, 32 stars)
**Repository:** https://github.com/mipsel64/chatty

**Features:**
- ✅ TUI for chatting with AI models
- ✅ Multiple model support

**Missing for Our Requirements:**
- ❌ No task management
- ❌ No CLI commands

**Verdict:** Good UI reference, but no functionality

---

### chatgpt-tui (narinluangrath, 19 stars)
**Repository:** https://github.com/narinluangrath/chatgpt-tui

**Features:**
- ✅ Terminal-based UI for ChatGPT

**Missing for Our Requirements:**
- ❌ No task management
- ❌ Single provider

**Verdict:** Basic TUI implementation

---

### doconvo (MegaGrindStone)
**Repository:** https://github.com/MegaGrindStone/doconvo

**Features:**
- ✅ TUI for conversing with documents
- ✅ RAG-powered
- ✅ Support multiple LLM providers
- ✅ Contextual understanding

**Missing for Our Requirements:**
- ❌ Document chat only, no task management
- ❌ No CLI
- ❌ No Docker

**Verdict:** Excellent RAG/TUI reference architecture

---

## 7. Vector/RAG Search Tools

### github-assistant (framsouza, 5 stars)
**Repository:** https://github.com/framsouza/github-assistant

**Features:**
- ✅ Chat with GitHub repository
- ✅ RAG with Elasticsearch
- ✅ Semantic search

**Missing for Our Requirements:**
- ❌ GitHub-only
- ❌ No task management
- ❌ No CLI

**Verdict:** Good RAG pattern reference

---

### supabase/headless-vector-search
**Repository:** https://github.com/supabase/headless-vector-search

**Features:**
- ✅ Vector similarity search
- ✅ Toolkit for knowledge base

**Missing for Our Requirements:**
- ❌ Infrastructure only
- ❌ No application

**Verdict:** Technical reference for vector search

---

## Market Gap Analysis

### What's Missing: The Perfect Personal TODO

Based on research, **no single open-source project combines all these features**:

| Feature | CLI Tools | AI Tools | Self-Hosted | Our System |
|----------|------------|-----------|--------------|-------------|
| CLI-first | ✅ Many | ❌ None | ❌ None | ✅ |
| Docker container | ❌ None | ✅ Some | ✅ Many | ✅ |
| BYOK/OpenRouter | ❌ None | ✅ Taskosaur | ❌ None | ✅ |
| Chat/AI interface | ❌ None | ✅ Taskosaur, todo-for-ai | ❌ None | ✅ |
| Gmail integration | ❌ None | ⚠️ Notifications only | ❌ None | ✅ |
| External attachments (GitHub, etc.) | ❌ None | ❌ None | ⚠️ Super Productivity | ✅ |
| RAG/search across tasks | ❌ None | ❌ None | ❌ None | ✅ |
| Desktop notifications | ❌ None | ❌ None | ❌ None | ✅ |
| Personal focus | ✅ Many | ⚠️ Team-focused | ⚠️ Team-focused | ✅ |

### Unique Selling Points

Our proposed system would be the **first** open-source project to combine:

1. **CLI-first architecture** (like dstask, t)
2. **Modern web chat UI** (like Taskosaur's AI chat)
3. **RAG-powered semantic search** (like doconvo)
4. **Gmail/external attachment integration** (unique)
5. **Desktop notifications** (completely missing in CLI tools)
6. **BYOK + OpenRouter support** (only Taskosaur has this)
7. **Simple, personal-focused** (most AI tools are team-focused)
8. **Docker-ready with auto-start** (many have Docker, none emphasize local auto-start)

### Competitive Advantages

#### vs. dstask/t (CLI tools)
- ✅ AI/chat interface
- ✅ Web UI for rich interactions
- ✅ Attachments (Gmail, GitHub PRs, documents)
- ✅ RAG search across tasks
- ✅ Desktop notifications
- ✅ Docker container with auto-start

#### vs. Taskosaur
- ✅ CLI-first (not web-first)
- ✅ Simpler architecture (FastAPI vs NestJS + Next.js)
- ✅ Gmail integration (not just notifications)
- ✅ Personal-focused (not team)
- ✅ RAG search across attachments
- ✅ Faster setup (less services)

#### vs. todo-for-ai
- ✅ Personal productivity focus
- ✅ Chat interface (not just MCP)
- ✅ CLI tool included
- ✅ RAG search
- ✅ Desktop notifications

#### vs. Super Productivity
- ✅ CLI-first
- ✅ AI/chat interface
- ✅ Gmail integration
- ✅ RAG search
- ✅ BYOK support

---

## Technical Patterns Worth Adapting

### From dstask
- **Git-based sync** (or we can use simpler SQLite with sync)
- **Context/tags filtering system**
- **Shell completion generation**
- **Priority system**

### From Taskosaur
- **BYOK implementation** (OpenRouter, OpenAI, Anthropic)
- **In-app chat interface design**
- **WebSocket for real-time updates**
- **Docker Compose setup**

### From todo-for-ai
- **Gmail integration patterns**
- **GitHub OAuth flow**
- **Modular architecture**

### From doconvo
- **RAG implementation with ChromaDB/FAISS**
- **TUI design patterns** (if we add TUI mode)
- **Multi-LLM provider support**

### From vikunja-mail-parser
- **IMAP email reading pattern**
- **Email parsing and attachment handling**
- **Docker + cron for automation**

---

## Recommended Tech Stack (Based on Research)

### Why Python/FastAPI?

1. **AI ecosystem** - Python has best LLM/RAG libraries (LangChain, ChromaDB, FAISS)
2. **Type hints** - Similar to TypeScript, good for maintainability
3. **Async** - FastAPI is async by default, great for real-time chat
4. **Simple** - Easier to understand than Node.js microservices
5. **Pydantic** - Built-in validation, great for APIs

### Why SQLite + SQLAlchemy?

1. **Simplicity** - No separate DB service needed
2. **Migration ready** - Easy to upgrade to Postgres later
3. **Docker-friendly** - Single file storage, easy volumes
4. **Python native** - Great integration with FastAPI

### Why ChromaDB?

1. **Local only** - No external service needed
2. **Python native** - Easy integration
3. **Open source** - No vendor lock-in
4. **Persistent** - Saves to disk, Docker-friendly

### Why Typer for CLI?

1. **Modern** - Better than argparse/click
2. **Type hints** - First-class support
3. **Auto-help** - Great UX
4. **Testing** - Easy to test CLI commands

### Why HTMX/Alpine.js for Web UI?

1. **Minimal** - Less JS than React/Next.js
2. **Server-rendered** - Simpler than SPAs
3. **Fast** - FastAPI + Jinja2 is very fast
4. **Easy to maintain** - Less code complexity

---

## Implementation Strategy

### Phase 1: MVP (Unique Combination)

**Week 1-2: Core Infrastructure**
- FastAPI backend with SQLite
- Typer CLI for CRUD operations
- Docker Compose with auto-start
- Desktop notifications (plyer)

**Week 3-4: AI Integration**
- OpenRouter integration (BYOK support)
- Simple chat endpoint
- Basic prompt management
- LLM configuration

**Week 5-6: Web UI**
- HTMX + Jinja2 templates
- Chat interface
- Task list view
- Task CRUD

### Phase 2: Differentiators

**Week 7-8: Gmail Integration**
- Google API Python Client
- OAuth flow
- Email fetching and parsing
- Attach emails to tasks

**Week 9-10: GitHub Integration**
- PyGithub
- Fetch PR/issue details
- Attach GitHub items to tasks

**Week 11-12: RAG/Search**
- ChromaDB integration
- Embed tasks and attachments
- Semantic search endpoint
- Chat with RAG

### Phase 3: Polish

**Week 13-14: Notifications & UX**
- Notification scheduler (24hr, 6hr before ETA)
- Notification history
- Better CLI completion
- Shell aliases and setup script

**Week 15-16: Documentation & Deployment**
- Comprehensive README
- Docker setup guide
- Configuration guide
- Backup/restore

---

## Conclusion

**Market Opportunity: HIGH**

There is a clear gap in the open-source market for a **personal, CLI-first task manager with modern AI features**. The existing tools either:

1. Focus on CLI (lack AI, attachments, notifications)
2. Focus on AI (are web-first, team-focused, over-engineered)
3. Focus on Docker (lack CLI, AI, Gmail)
4. Focus on integrations (lack unified system)

Our proposed system uniquely combines all these features in a **simple, personal-focused package**. The closest competitors are:

- **Taskosaur** (over-engineered, team-focused)
- **todo-for-ai** (AI assistant-focused, not personal productivity)
- **dstask** (excellent CLI, but no AI or modern features)

**We can be the first to market with this specific combination.**

---

## Next Steps

1. ✅ **Review this research with user**
2. ⬜ **Refine requirements based on feedback**
3. ⬜ **Finalize tech stack**
4. ⬜ **Begin Phase 1 implementation**
5. ⬜ **Iterate based on usage patterns**

---

## References

- dstask: https://github.com/naggie/dstask
- t: https://github.com/sjl/t
- Taskosaur: https://github.com/Taskosaur/Taskosaur
- todo-for-ai: https://github.com/todo-for-ai/todo-for-ai
- MasteryListGPT: https://github.com/curiousily/MasteryListGPT-Chat-with-your-ToDo-List-with-LangChain-and-ChatGPT
- Super Productivity: https://github.com/johannesjo/super-productivity
- doconvo: https://github.com/MegaGrindStone/doconvo
- Gmail2Notion: https://github.com/Mike7154/Gmail2Notion
- vikunja-mail-parser: https://github.com/weselinka/vikunja-mail-parser
- llm-openrouter: https://github.com/simonw/llm-openrouter
