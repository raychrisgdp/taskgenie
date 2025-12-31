# PR-005-2: Semantic Search API & RAG Context Injection (Spec)

**Status:** Spec Only
**Depends on:** PR-001, PR-003-2, PR-004, PR-005-1
**Last Reviewed:** 2025-12-31

## Goal

Implement semantic search API endpoint and RAG context injection for chat responses, building on ChromaDB indexing from PR-005-1.

## User Value

- Users can search tasks by meaning (not just keywords)
- Chat responses are grounded in relevant task context
- Semantic search finds tasks even without exact word matches

## Scope

### In

- `GET /api/v1/search/semantic` endpoint
- Search with query text, optional filters (status, priority)
- Top-k results with similarity scores
- RAG context building for chat
- Integration with streaming chat endpoint from PR-003-2
- Context budgeting (token limits)

### Out

- Persistent chat history with context retention (future)
- Advanced retrieval strategies (hybrid, reranking)
- Multi-turn RAG with conversation context

## Mini-Specs

- `GET /api/v1/search/semantic` endpoint with filters and scoring
- Search results include snippets + similarity scores for UX
- RAG context builder with an explicit token budget
- Chat endpoint injects RAG context (behind config if needed)

## References

- `docs/01-design/API_REFERENCE.md` (search + chat examples)
- `docs/01-design/DESIGN_CHAT.md` (context injection + prompt assembly)
- `docs/01-design/DESIGN_DATA.md` (RAG document structure)

## Technical Design

### Search Data Models

```python
# backend/schemas/search.py
from pydantic import BaseModel, Field
from typing import Optional

class SearchResult(BaseModel):
    """Single search result."""
    task_id: str
    document: str
    distance: float
    similarity: float
    status: str
    priority: str
    has_attachments: bool
    snippet: str

    class Config:
        from_attributes = True

class SemanticSearchResponse(BaseModel):
    """Semantic search API response."""
    results: list[SearchResult]
    total: int
    query: str
    filters: dict

class RAGContextRequest(BaseModel):
    """Request for RAG context."""
    query: str
    n_results: int = Field(default=3, ge=1, le=10)
    include_metadata: bool = True
    max_tokens: Optional[int] = Field(default=1500, ge=100, le=5000)
```

### Semantic Search Endpoint

```python
# backend/api/search.py
from fastapi import APIRouter, Query
from backend.schemas.search import SemanticSearchResponse, SearchResult
from backend.services.rag_service import rag_service

router = APIRouter(prefix="/api/v1/search", tags=["search"])

@router.get("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    q: str = Query(..., min_length=1, max_length=500),
    status: Optional[str] = Query(None, regex="^(pending|in_progress|completed)$"),
    priority: Optional[str] = Query(None, regex="^(low|medium|high|critical)$"),
    n: int = Query(5, ge=1, le=20),
    min_similarity: float = Query(0.0, ge=0.0, le=1.0),
):
    """
    Semantic search over tasks using vector similarity.

    **Query Parameters:**
    - `q`: Search query (required)
    - `status`: Filter by task status
    - `priority`: Filter by priority
    - `n`: Number of results (default: 5, max: 20)
    - `min_similarity`: Minimum similarity threshold (0.0-1.0)

    **Response:**
    Returns list of results with similarity scores and metadata.
    Results are sorted by similarity (highest first).
    """
    results = await rag_service.search(
        query=q,
        n_results=n,
        filter_status=status,
        filter_priority=priority,
        min_similarity=min_similarity,
    )

    return SemanticSearchResponse(
        results=[SearchResult.from_orm(r) for r in results],
        total=len(results),
        query=q,
        filters={"status": status, "priority": priority},
    )
```

### RAG Context Building

```python
# backend/services/rag_service.py (continued)

class RAGService:
    # ... existing methods ...

    async def build_context(
        self,
        query: str,
        n_results: int = 3,
        include_metadata: bool = True,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Build context string for LLM prompt.

        **Strategy:**
        1. Retrieve top-n relevant tasks
        2. Format with metadata (status, priority)
        3. Truncate if exceeding token budget
        4. Include similarity scores for transparency
        """
        results = await self.search(query, n_results=n_results)

        if not results:
            return "No relevant tasks found."

        context_parts = ["Relevant tasks:"]

        for i, result in enumerate(results, 1):
            parts = [f"{i}. [{result.task_id}]"]

            if include_metadata:
                parts.append(f"(status: {result.status}, priority: {result.priority})")

            parts.append(f"- {result.snippet}")

            if include_metadata:
                parts.append(f"(similarity: {result.similarity:.2%})")

            context_parts.append(" ".join(parts))

        context = "\n".join(context_parts)

        # Truncate to token budget
        if max_tokens:
            # Rough estimate: 4 chars per token
            max_chars = max_tokens * 4
            if len(context) > max_chars:
                context = context[:max_chars] + "..."

        return context

    async def chat_with_context(
        self,
        user_query: str,
        llm_service: "LLMService",
        n_results: int = 3,
        max_context_tokens: int = 1500,
    ) -> str:
        """
        Answer user query with RAG context.

        **Budget Allocation:**
        - System prompt: ~500 tokens
        - RAG context: ~1500 tokens (configurable)
        - User message: ~200 tokens
        - LLM output: ~800 tokens (reserved)

        **Optimization Strategies:**
        1. Top-k results only (no full vector scan)
        2. Truncate documents to 200 chars each
        3. Preserve task metadata even when content truncated
        """
        context = await self.build_context(
            user_query,
            n_results=n_results,
            max_tokens=max_context_tokens,
        )

        prompt = f"""You are a helpful task management assistant. Use the following context about the user's tasks to answer their question.

{context}

User Question: {user_query}

Provide a helpful, concise response based on the relevant tasks above. If the context doesn't contain relevant information, say so and offer general advice."""

        response = ""
        async for chunk in llm_service.stream_chat([{"role": "system", "content": prompt}]):
            response += chunk

        return response
```

### Chat Endpoint Integration

**Update Chat Endpoint**
```python
# backend/api/chat.py (modified)
from backend.schemas.chat import ChatRequest
from backend.services.rag_service import rag_service

@router.post("")
async def chat(request: ChatRequest):
    """
    Stream chat response with optional RAG context.

    **Flow:**
    1. Build RAG context from user message (if enabled)
    2. Inject context into system prompt
    3. Stream LLM response via SSE
    """
    # Build context (optional, can be disabled)
    context = await rag_service.build_context(
        request.message,
        n_results=3,
        max_tokens=1500,
    )

    # Build messages
    messages = [
        {"role": "system", "content": "You are a helpful task management assistant."},
    ]

    # Inject RAG context
    if context and "No relevant tasks found" not in context:
        messages.insert(1, {
            "role": "system",
            "content": f"Context:\n{context}"
        })

    messages.append({"role": "user", "content": request.message})

    # Stream response
    async def stream_generator():
        try:
            async for chunk in rag_service.chat_with_context(
                user_query=request.message,
                llm_service=llm_service,
            ):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"event: error\ndata: {str(e)}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
```

### Context Budgeting

**Token Budget Allocation**
```python
# backend/services/rag_service.py

CONTEXT_BUDGET_ALLOCATION = {
    "system_prompt": 500,
    "rag_context": 1500,
    "user_message": 200,
    "llm_output": 800,
}

def estimate_tokens(text: str) -> int:
    """Rough token estimation (4 chars per token)."""
    return max(1, len(text) // 4)

def truncate_to_budget(context: str, max_tokens: int) -> str:
    """Truncate context to fit budget."""
    max_chars = max_tokens * 4
    if len(context) <= max_chars:
        return context
    return context[:max_chars] + "... [truncated]"
```

### Search Result Formatting

**Snippet Generation**
```python
class SearchResult:
    # ... existing fields ...

    @property
    def snippet(self) -> str:
        """Get truncated document snippet."""
        if len(self.document) <= 100:
            return self.document
        return self.document[:100] + "..."
```

## Acceptance Criteria

- [ ] `GET /api/v1/search/semantic` endpoint exists
- [ ] Search returns relevant results sorted by similarity
- [ ] Filters (status, priority) work correctly
- [ ] `min_similarity` parameter filters low-quality matches
- [ ] RAG context builder includes task metadata
- [ ] Context truncation respects token budget
- [ ] Chat endpoint injects RAG context into prompts
- [ ] Context shows similarity scores for transparency
- [ ] Unit tests cover search, context building, budgeting
- [ ] Automated tests cover endpoint behavior + chat integration (see Test Plan).
- [ ] Manual smoke checklist completed (see Test Plan).

## Test Plan

### Automated

**Search Tests**
```python
# tests/test_api/test_search.py
import pytest
from backend.services.rag_service import rag_service

class TestSemanticSearch:
    @pytest.fixture
    async def indexed_tasks(self, db_session, rag_service_test):
        """Pre-index sample tasks."""
        tasks = [
            {"id": "auth-1", "title": "Fix login", "status": "pending"},
            {"id": "auth-2", "title": "Update JWT", "status": "completed"},
            {"id": "ui-1", "title": "Redesign", "status": "pending"},
        ]
        for task in tasks:
            await rag_service_test.index_task(task)
        return tasks

    @pytest.mark.asyncio
    async def test_search_returns_relevant(self, indexed_tasks):
        """Search finds semantically similar tasks."""
        results = await rag_service_test.search("authentication issues", n_results=3)

        assert len(results) > 0
        assert all(r.similarity >= 0.5 for r in results)

    @pytest.mark.asyncio
    async def test_search_with_status_filter(self, indexed_tasks):
        """Filter by status works."""
        results = await rag_service_test.search(
            "task",
            filter_status="pending"
        )

        assert all(r.status == "pending" for r in results)

    @pytest.mark.asyncio
    async def test_search_min_similarity(self, indexed_tasks):
        """Minimum similarity filters results."""
        results = await rag_service_test.search(
            "task",
            min_similarity=0.9
        )

        # Should only return very similar results (if any)
        assert all(r.similarity >= 0.9 for r in results)
```

**Context Building Tests**
```python
class TestRAGContext:
    @pytest.mark.asyncio
    async def test_build_context_includes_metadata(self, indexed_tasks):
        """Context includes task status and priority."""
        context = await rag_service_test.build_context(
            "what tasks?",
            n_results=2,
            include_metadata=True
        )

        assert "status:" in context
        assert "priority:" in context
        assert "similarity:" in context

    @pytest.mark.asyncio
    async def test_build_context_truncates_to_budget(self, indexed_tasks):
        """Context truncates to token budget."""
        context = await rag_service_test.build_context(
            "task" * 100,  # Force long context
            n_results=10,
            max_tokens=500,
        )

        # Should be truncated
        assert len(context) < 500 * 4  # Rough estimate
        assert "..." in context or "[truncated]" in context

    @pytest.mark.asyncio
    async def test_build_context_no_results(self, rag_service_test):
        """Context message when no results."""
        context = await rag_service_test.build_context("xyz123")

        assert "No relevant tasks found" in context
```

**Integration Tests**
```python
class TestChatWithRAG:
    @pytest.mark.asyncio
    async def test_chat_uses_rag_context(self, client: AsyncClient, indexed_tasks):
        """Chat injects RAG context."""
        # Mock LLM service
        mock_llm = AsyncMock()
        mock_llm.stream_chat = AsyncMock(return_value=aiter_chunks(["Response"]))

        with patch("backend.services.llm_service.llm_service", mock_llm):
            response = await client.post("/api/v1/chat", json={"message": "Test"})

            # Verify context was included
            messages = mock_llm.stream_chat.call_args[0][0]
            assert any("Relevant tasks:" in m["content"] for m in messages)
```

### Manual

1. Create several tasks with different topics
2. Test semantic search:
   ```bash
   curl "http://localhost:8080/api/v1/search/semantic?q=login+issues"
   ```
3. Verify results are relevant (not just keyword matches)
4. Test filters:
   ```bash
   curl "http://localhost:8080/api/v1/search/semantic?q=task&status=pending"
   ```
5. Test chat with RAG:
   - Send message: "What authentication tasks do I have?"
   - Verify response references correct tasks
   - Check similarity scores in logs (if enabled)

### Manual Test Checklist

- [ ] Search endpoint returns stable, sorted results with documented fields.
- [ ] Filters and `min_similarity` behave as documented.
- [ ] Context builder respects max token budget and truncates predictably.
- [ ] Chat injection is traceable (logs/markers) and does not leak private data.
- [ ] No-results queries return a safe, user-friendly response.

### Run Commands

```bash
make test
# or
uv run pytest -v
```

## Notes / Risks / Open Questions

- Should we expose similarity scores to API clients?
- Should RAG context injection be configurable (on/off)?
- How to handle queries that return no relevant results?

## Dependencies

- PR-001 (DB + Config)
- PR-003-2 (Streaming Chat API)
- PR-004 (Attachments)
- PR-005-1 (ChromaDB + Embeddings)

## Future Enhancements

- Hybrid search (semantic + keyword)
- Result reranking (cross-encoder)
- Conversation context for multi-turn RAG
- Persistent chat history
- Adaptive context budget (dynamic token limits)

## Related Skills

- **context-optimization**: Context budgeting and token management
- **context-compression**: Chat history summarization (future)
- **rag-testing**: ChromaDB testing patterns
