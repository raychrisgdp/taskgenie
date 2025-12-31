# Skill Enrichment & PR Breakdown Summary

**Last Updated:** 2025-12-31

## Overview

This document summarizes skill enrichments applied to PR specs and the breakdown of complex PRs into smaller, focused units.

---

## Skill Mappings to Existing PRs

| PR | Skill Enriched | Key Guidance Added |
|-----|---------------|------------------|
| **PR-002** (Task CRUD API) | `api-testing` | Test patterns, fixtures, coverage goals (80%+), mock strategies |
| **PR-003-2** (Streaming Chat API) | `api-testing` | SSE streaming test patterns, HTTPX mocking, error-mapping scenarios |
| **PR-003-3** (TUI Chat Integration) | `tui-dev` | Textual patterns for streaming UI, keybindings, and TUI testing guidance |
| **PR-005-1** (ChromaDB + Embeddings) | `rag-testing` | ChromaDB fixtures, embedding determinism tests, indexing tests |
| **PR-005-2** (Semantic Search + RAG) | `rag-testing`, `context-optimization`, `context-compression` *(future)* | Search tests, context budgeting, future chat-history summarization |
| **PR-006** (Gmail Integration) | `integration-setup` | OAuth flow, token storage (0600), security best practices, troubleshooting |
| **PR-007** (GitHub Integration) | `integration-setup` | PAT setup (fine-grained + classic), API client patterns, error handling, mocking |
| **PR-008** (Interactive TUI) | `tui-dev` | Textual framework setup, keybindings, layout design, testing with Pilot, TCSS styling |
| **PR-004** (Attachments + Link Detection) | `task-workflow` | Attachment CRUD workflows, link detection patterns, deduplication, service layer |
| **PR-009** (CLI Subcommands) | `task-workflow` | CLI commands (add/list/show/edit/done/delete), API client integration, output formatting, error handling |
| **PR-011** (Notifications) | `task-workflow` | Notification lifecycle, scheduler logic, deduplication, quiet hours, delivery channels |

---

## PR Breakdowns Adopted

### PR-003 → PR-003-1, PR-003-2, PR-003-3

**Rationale:** PR-003 combined three distinct concerns:
1. LLM provider abstraction and configuration
2. Streaming chat API endpoint
3. TUI chat panel integration

**Benefits of Split:**
- Parallel work: Provider and API can be built concurrently with TUI scaffolding
- Focused testing: Each sub-PR has clear test boundaries
- Faster iteration: API issues don't block TUI development

**New PRs:**
- **PR-003-1: LLM Provider Abstraction & Configuration** (`docs/02-implementation/pr-specs/PR-003-1-llm-provider.md`)
  - `LLMService` class
  - Configuration from env/config
  - OpenRouter/OpenAI support
  - Error handling (401, 429)

- **PR-003-2: Streaming Chat API Endpoint** (`docs/02-implementation/pr-specs/PR-003-2-streaming-chat-api.md`)
  - `POST /api/v1/chat` endpoint
  - SSE streaming format
  - Request validation
  - Error handling

- **PR-003-3: TUI Chat Integration** (`docs/02-implementation/pr-specs/PR-003-3-tui-chat-integration.md`)
  - Chat panel widget
  - SSE streaming integration
  - Error modals
  - Chat history (session-only)

**Skill Enrichment:**
- PR-003-2: `api-testing` (HTTPX mocks + SSE test scenarios)

---

### PR-005 → PR-005-1, PR-005-2

**Rationale:** PR-005 combined three technical areas:
1. ChromaDB setup and embedding generation
2. Semantic search endpoint
3. RAG context injection for chat

**Benefits of Split:**
- Clear separation: Indexing vs retrieval
- Faster testing: ChromaDB tests don't depend on chat integration
- Independent deployment: Can ship indexing first, add search later

**New PRs:**
- **PR-005-1: ChromaDB Setup & Embeddings Pipeline** (`docs/02-implementation/pr-specs/PR-005-1-chromadb-embeddings.md`)
  - `EmbeddingService` class
  - `RAGService` (setup + indexing)
  - ChromaDB persistent client
  - Task/attachment indexing hooks
  - Batch indexing support

- **PR-005-2: Semantic Search API & RAG Context Injection** (`docs/02-implementation/pr-specs/PR-005-2-semantic-search-rag.md`)
  - `GET /api/v1/search/semantic` endpoint
  - `SearchResult` model with similarity scores
  - RAG context building
  - Context budgeting (token limits)
  - Chat endpoint integration

**Skill Enrichment:**
- PR-005-1: `rag-testing` (ChromaDB fixtures, embedding tests, indexing tests)
- PR-005-2: `rag-testing` (search tests, context building tests), `context-optimization` (budgeting, truncation), `context-compression` (future chat history)

---

## Skills Without Direct PR Mappings (Future Work)

| Skill | Potential New PR | Description |
|--------|----------------|-------------|
| **multi-agent-patterns** | PR-013 | Multi-agent chat system (specialized agents for parsing, task ops, retrieval) |
| **tool-design** | PR-014 | Tool abstraction layer for agent tools in PR-013 |
| **memory-systems** | PR-015 | Persistent conversation memory and entity tracking |
| **context-fundamentals** | - | Applied via existing context-optimization/compression skills |

---

## Updated Execution Sequence

With breakdowns, the recommended sequence becomes:

1. PR-001: Database & Configuration
2. PR-002: Task CRUD API → `api-testing`
3. PR-008: Interactive TUI (Tasks MVP) → `tui-dev`
4. PR-003-1: LLM Provider → (parallel with 008)
5. PR-003-2: Streaming Chat API → `api-testing`
6. PR-003-3: TUI Chat Integration → `tui-dev`
7. PR-009: CLI Subcommands → `task-workflow`
8. PR-004: Attachments + Link Detection → `task-workflow`
9. PR-011: Notifications → `task-workflow`
10. PR-007: GitHub Integration → `integration-setup`
11. PR-006: Gmail Integration → `integration-setup`
12. PR-005-1: ChromaDB + Embeddings → `rag-testing`
13. PR-005-2: Semantic Search + RAG → `rag-testing`, `context-optimization`, `context-compression` (future)
14. PR-010: Web UI
15. PR-012: Deployment + Docs

---

## Files Created/Modified

**New PR Specs Created:**
- `docs/02-implementation/pr-specs/PR-003-1-llm-provider.md`
- `docs/02-implementation/pr-specs/PR-003-2-streaming-chat-api.md`
- `docs/02-implementation/pr-specs/PR-003-3-tui-chat-integration.md`
- `docs/02-implementation/pr-specs/PR-005-1-chromadb-embeddings.md`
- `docs/02-implementation/pr-specs/PR-005-2-semantic-search-rag.md`

**Existing PR Specs Enriched:**
- `docs/02-implementation/pr-specs/PR-002-task-crud-api.md` (+ `api-testing`)
- `docs/02-implementation/pr-specs/PR-004-attachments-link-detection.md` (+ `task-workflow`)
- `docs/02-implementation/pr-specs/PR-005-rag-semantic-search.md` (+ `rag-testing`, `context-optimization`, `context-compression`)
- `docs/02-implementation/pr-specs/PR-006-gmail-integration.md` (+ `integration-setup`)
- `docs/02-implementation/pr-specs/PR-007-github-integration.md` (+ `integration-setup`)
- `docs/02-implementation/pr-specs/PR-008-interactive-tui.md` (+ `tui-dev`)
- `docs/02-implementation/pr-specs/PR-009-cli-subcommands.md` (+ `task-workflow`)
- `docs/02-implementation/pr-specs/PR-011-notifications.md` (+ `task-workflow`)

**Planning Docs Updated:**
- `docs/02-implementation/PR-PLANS.md` (Updated dependency diagram and timeline)

---

## Next Steps

1. **Optional cleanup:**
   - Decide whether to mark `PR-003-llm-chat-backbone.md` and `PR-005-rag-semantic-search.md` as archived (kept for reference) now that PR-003-1/2/3 and PR-005-1/2 exist.
   - Keep endpoint examples consistent with `docs/01-design/API_REFERENCE.md` (notably base URL/port).

2. **Consider New PRs:**
   - PR-013: Multi-agent chat system (`multi-agent-patterns`)
   - PR-014: Tool abstraction layer (`tool-design`)
   - PR-015: Persistent memory system (`memory-systems`)

3. **Implementation:**
   - Begin with PR-001, PR-002, PR-008 (Foundation)
   - Then execute PR-003-1/2/3 (Chat)
   - Then add intelligence (PR-005-1/2)
   - Then integrations and polish
