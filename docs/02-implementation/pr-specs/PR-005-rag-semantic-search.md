# PR-005: RAG + Semantic Search (Spec)

**Status:** Spec Only  
**Depends on:** PR-003, PR-004  
**Last Reviewed:** 2025-12-30

## Goal

Add semantic search across tasks and cached attachment content, and use retrieved
context to improve chat responses.

## User Value

- Users can find tasks by meaning, not just keywords.
- Chat responses can reference local context.

## References

- `docs/01-design/DESIGN_CHAT.md`
- `docs/01-design/DESIGN_DATA.md`
- `docs/01-design/API_REFERENCE.md`

## Docs Links

- `README.md`
- `docs/INDEX.md`
- `docs/USER_GUIDE.md`
- `docs/01-design/DESIGN_CLI.md`
- `docs/01-design/API_REFERENCE.md`

## Scope

### In

- Local vector store (ChromaDB) and embeddings pipeline.
- Indexing for tasks and cached attachment content.
- Semantic search endpoint returning ranked results.
- Chat context injection with strict token limits.

### Out

- Multi-tenant or remote vector databases.
- Hybrid keyword search, re-ranking, and query expansion (future).

## Mini-Specs

- Configurable embedding model and vector store location.
- Indexing triggers on task create/update and attachment content updates.
- `/api/v1/search/semantic` endpoint returning top-k results with scores.
- Prompt assembly that injects retrieved context within a token budget.

## User Stories

- As a user, I can search by meaning and find relevant tasks.
- As a user, chat answers reference the right tasks or attachments.

## UX Notes (if applicable)

- N/A.

## Technical Design

### Architecture

- Embedding service creates chunks and writes to ChromaDB.
- Retrieval service returns top-k snippets with scores and metadata.
- Chat pipeline requests top snippets and injects them into the prompt.

### Data Model / Migrations

- Vector store collection `taskgenie_items` with metadata:
  id, source_type (task|attachment), parent_task_id, text, embedding_version.

### API Contract

- `GET /api/v1/search/semantic?query=...&limit=...` returns results with id, type,
  score, snippet, and task linkage.

### Background Jobs

- Optional background indexing for large attachment content to avoid blocking
  requests.

### Security / Privacy

- Do not log raw content or prompts by default.
- Embeddings are stored locally in the app data directory.

### Error Handling

- Empty index returns empty results (200 OK).
- Embedding failures return actionable errors and do not crash chat.

## Acceptance Criteria

### AC1: Indexing Pipeline

**Success Criteria:**
- [ ] Tasks and cached attachments are embedded and indexed automatically.

### AC2: Semantic Search API

**Success Criteria:**
- [ ] Search returns relevant results for representative queries.

### AC3: Chat Context Injection

**Success Criteria:**
- [ ] Chat responses include retrieved context when available and respect token
  limits.

## Test Plan

### Automated

- Unit tests for chunking, prompt assembly, token budgeting.
- Integration tests for search ranking with a small fixture corpus.

### Manual

- Create tasks and attachments and query semantic search.
- Ask chat a question that should be grounded in a task.

## Notes / Risks / Open Questions

- Decide whether embeddings include title only or title + description.
- Consider hybrid search and re-ranking in a follow-on PR for higher precision.
