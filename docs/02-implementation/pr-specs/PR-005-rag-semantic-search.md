# PR-005: RAG + Semantic Search (Spec)

**Status:** Spec Only  
**Depends on:** PR-003, PR-004  
**Last Reviewed:** 2025-12-30

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

## Mini-Specs

- Embeddings:
  - choose default embedding model/provider (configurable).
- Indexing:
  - tasks + cached attachments are embedded and stored in ChromaDB.
  - re-index on create/update and after attachment fetch.
- Query:
  - semantic search API (`GET /api/v1/search/semantic`) returns ranked results.
- Chat augmentation:
  - retrieve top snippets and inject into chat prompt (bounded by token limits).
- Tests:
  - small fixture corpus; validate top-k results for representative queries.

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

- **Model:** `sentence-transformers/all-MiniLM-L6-v2` (via `sentence-transformers`; make configurable later)
- **Vector Store:** ChromaDB (running in-process)
- **Collection Naming:** `taskgenie_items`
- **Document Metadata:**
  - `id`: task or attachment ID
  - `source_type`: `task | attachment`
  - `parent_task_id`: ID of the task
  - `text`: the chunked content

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
- [ ] Automated tests cover indexing + retrieval + context building (see Test Plan).
- [ ] Manual smoke checklist completed (see Test Plan).

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

### Manual Test Checklist

- [ ] New/updated tasks get indexed automatically.
- [ ] Cached attachment content is indexed when available.
- [ ] Search results are stable and include similarity/scoring as documented.
- [ ] Chat context injection respects a token budget and is traceable (sources or markers).
- [ ] No sensitive content is logged by default.

### Run Commands

```bash
make test
# or
uv run pytest -v
```

## Notes / Risks / Open Questions

- Decide whether to store embeddings for task description only vs (title + description).

---

## Skill Integration: rag-testing

### Testing Guidance

This PR should follow **rag-testing** skill patterns:

**ChromaDB Setup**
- Use in-memory ChromaDB client for tests (`chromadb.Client()`)
- Create test collection with cosine similarity
- Reset collection between tests with `collection.delete()`

**Embedding Service Tests**
```python
# Verify embedding dimension (384 for all-MiniLM-L6-v2)
# Test deterministic generation (same text → same embedding)
# Test similarity calculation (same text ≈ 1.0, different texts < 0.5)
# Batch generation tests
```

**Indexing Tests**
- Index single task → verify in collection
- Index tasks with attachments → verify content combined
- Delete task → verify removal from vector store
- Test metadata persistence (status, priority, has_attachments)

**Search Tests**
```python
# Create corpus with different topics
tasks = [
    {"id": "1", "title": "Fix login bug", "status": "pending"},
    {"id": "2", "title": "Plan vacation", "status": "pending"},
]
# Query "authentication issues" → should return task 1 with high similarity
# Query "travel" → should return task 2
# Test filter_status="pending" → only pending tasks
# Test min_similarity=0.7 → filter low-quality matches
```

**Context Building Tests**
- Verify context string includes relevant tasks
- Test "no results" fallback message
- Verify metadata inclusion (status, priority, similarity scores)

**Coverage Goals**
| Module | Target |
|--------|---------|
| `backend/services/rag_service.py` | 85%+ |
| `backend/services/embedding_service.py` | 90%+ |

**See Also**
- Skill doc: `.opencode/skill/rag-testing/`

---

## Skill Integration: context-optimization

### RAG Context Budget Management

This PR should implement context budgeting from **context-optimization** skill:

**Budget Allocation**
When injecting RAG context into chat prompts, allocate tokens strategically:
- System prompt: ~500 tokens (fixed)
- RAG context: ~1000-1500 tokens (variable)
- User message: ~200-500 tokens (variable)
- LLM output budget: ~800 tokens (reserved)

**Compaction Strategies**
When RAG context exceeds budget:
1. Prioritize by similarity score (keep top 3-5 results)
2. Truncate documents to first 200 chars each
3. Preserve task metadata (id, status) even when content truncated
4. Include "similarity: X%" for transparency

**Observation Masking**
For cached attachment content:
- Store full attachment in DB (for viewing)
- Inject only snippets/summaries into RAG context
- Provide "expand" action to fetch full content if needed

**Cache Optimization**
- Order ChromaDB query results by relevance before adding to context
- Reuse embeddings for unchanged content (hash-based cache)
- Lazy-load embedding model on first use

**Performance Targets**
- Semantic search latency: < 200ms (5 results)
- Context assembly time: < 100ms
- Token budget adherence: 95%+ of requests within limits

**See Also**
- Skill doc: `.opencode/skill/context-optimization/`

---

## Skill Integration: context-compression

### Chat History Management (Future)

This PR establishes foundation for **context-compression** patterns (full implementation future):

**Anchored Iterative Summarization**
When chat sessions grow long (100+ messages):
1. Maintain structured summary with sections:
   ```markdown
   ## Session Intent
   ## Tasks Referenced
   ## Decisions Made
   ## Current State
   ## Next Steps
   ```
2. Trigger compression at 70-80% context utilization
3. Summarize only newly-truncated span
4. Merge with existing summary incrementally

**Artifact Trail for Tasks**
Track which tasks were mentioned/modified in chat:
- Task IDs referenced in conversation
- Actions taken (created/updated/completed)
- Decisions about priority/status changes

**Compression Trigger Signals**
- Chat history exceeds 10,000 tokens
- RAG context + history > 70% of window
- Session duration > 30 minutes

**Probe-Based Evaluation**
Test compression quality by asking:
- "What tasks were we discussing?"
- "What did we decide about priority?"
- "What should we do next?"

**Note**: Full chat history compression is out-of-scope for this PR. RAG context budgeting (above) is the immediate priority.

**See Also**
- Skill doc: `.opencode/skill/context-compression/`
