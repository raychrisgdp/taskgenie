# PR-005: RAG + Semantic Search (Spec)

**Status:** Spec Only  
**Depends on:** PR-003, PR-004  
**Last Reviewed:** 2025-12-29

## Goal

Add semantic recall across tasks and cached attachment content, and improve chat answers by injecting the most relevant context.

## User Value

- “Where did I put that?” becomes fast: semantic search finds tasks/attachments by meaning.
- Chat becomes more accurate because it can ground responses in local data.

## Scope

### In

- Local vector store (ChromaDB).
- Embedding pipeline for:
  - tasks
  - attachments (cached content)
- Semantic search endpoint (query → top-k results with scores).
- Chat integration:
  - retrieve top context snippets
  - inject into prompt (bounded by token limits)

### Out

- Cross-user/multi-tenant search.
- Remote vector DB.

## References

- `docs/01-design/DESIGN_CHAT.md` (RAG strategy + prompt assembly)
- `docs/01-design/DESIGN_DATA.md` (RAG document structure)
- `docs/01-design/API_REFERENCE.md` (semantic search endpoint examples)

## User Stories

- As a user, I can search by meaning (“login issues”) and find the right task.
- As a user, chat answers can reference the correct task/attachment context.

## Technical Design

### Indexing triggers

- Index tasks:
  - on task create/update
- Index attachments:
  - when attachment content is fetched/updated (PR-006/PR-007)

### Embeddings

- Use a sentence-transformer embedding model (local-first).
- Store vectors in ChromaDB with metadata:
  - `type: task|attachment`
  - `task_id`, `attachment_id`
  - title, timestamps

### Retrieval + response format

- Semantic search endpoint returns:
  - top-k results with scores
  - short excerpts for display
- Chat integration:
  - retrieve top snippets
  - inject into prompt within a strict token budget
  - (optional) include “sources” in response for traceability

## Acceptance Criteria

- [ ] Tasks and cached attachments are embedded and indexed automatically.
- [ ] Semantic search returns relevant results for representative queries.
- [ ] Chat responses cite retrieved task/attachment context where applicable.

## Test Plan

### Automated

- Unit: chunking logic, prompt assembly, context truncation.
- Integration:
  1. Create two tasks with different topics; query semantic search; verify ranking.
  2. Add attachment content; query that content; verify attachment appears in results.
  3. Chat query uses retrieved context (verify via stubbed “context used” markers).

### Manual

1. Create tasks “Fix auth bug” and “Plan vacation”.
2. Search “login issues” → should surface the auth task.
3. Ask chat “What’s the status of the login work?” → response should reference the correct task.

## Notes / Risks / Open Questions

- Decide whether to store embeddings for task description only vs (title + description).
