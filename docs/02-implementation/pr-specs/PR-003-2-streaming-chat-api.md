# PR-003-2: Streaming Chat API Endpoint (Spec)

**Status:** Spec Only
**Depends on:** PR-001, PR-002, PR-003-1
**Last Reviewed:** 2025-12-31

## Goal

Create a FastAPI streaming chat endpoint that integrates with the LLM service from PR-003-1 and returns responses via Server-Sent Events (SSE).

## User Value

- API clients (TUI, Web UI) can stream chat responses in real-time
- Server-Sent Events provide standard streaming protocol
- Errors are handled gracefully with clear messages

## Scope

### In

- `POST /api/v1/chat` endpoint
- SSE streaming response format (`text/event-stream`)
- Integration with `LLMService` from PR-003-1
- Request validation (message required, optional context)
- Error handling for missing/invalid LLM configuration
- OpenAPI documentation for streaming endpoint

### Out

- RAG context injection (PR-005-2)
- Tool calling / agent actions (future)
- WebSocket streaming (SSE is sufficient for MVP)

## Mini-Specs

- `POST /api/v1/chat` returns SSE (`text/event-stream`)
- Strict request validation (non-empty message)
- Clear error mapping for missing/invalid LLM config and rate limits
- Automated tests cover SSE parsing and error cases

## References

- `docs/01-design/API_REFERENCE.md` (endpoint contract + examples)
- `docs/01-design/DESIGN_CHAT.md` (SSE + streaming behavior)

## Technical Design

### API Contract

**Request**
```http
POST /api/v1/chat
Content-Type: application/json

{
  "message": "What tasks are due today?",
  "context": null  // Optional: pre-injected context (future PR-005-2)
}
```

**Response (SSE)**
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache

data: You have 3 tasks due today:
data: 
data: 1. [HIGH] Review PR #123 - Fix authentication
data: 
data: 2. [MED] Update documentation
data: 
data: 3. [LOW] Clean up old tasks
data: [DONE]

```

**Errors**
```json
// 500 Internal Server Error - LLM not configured
{
  "error": "LLM not configured. Set LLM_API_KEY in .env or config file.",
  "code": "LLM_NOT_CONFIGURED"
}

// 500 Internal Server Error - Rate limit
{
  "error": "Rate limit exceeded. Please try again later.",
  "code": "LLM_RATE_LIMIT"
}

// 422 Validation Error - Empty message
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Implementation

**Pydantic Schemas**
```python
# backend/schemas/chat.py
from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    context: Optional[str] = Field(None, max_length=5000)
```

**FastAPI Endpoint**
```python
# backend/api/chat.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.schemas.chat import ChatRequest
from backend.services.llm_service import llm_service

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

@router.post("")
async def chat(request: ChatRequest):
    """Stream chat response via SSE."""
    try:
        # Build messages
        messages = [
            {"role": "system", "content": "You are a helpful task management assistant."},
            {"role": "user", "content": request.message},
        ]

        # Add context if provided
        if request.context:
            messages.insert(1, {
                "role": "system",
                "content": f"Context:\n{request.context}"
            })

        # Stream response
        async def stream_generator():
            try:
                async for chunk in llm_service.stream_chat(messages):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            except ValueError as e:
                # Missing API key
                yield f"event: error\ndata: {str(e)}\n\n"
            except Exception as e:
                # LLM provider error
                yield f"event: error\ndata: {str(e)}\n\n"

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Register Router**
```python
# backend/main.py
from backend.api.chat import router as chat_router

app.include_router(chat_router)
```

### Error Handling

**LLMService Errors**

| Exception | HTTP Status | Error Code | Message |
|-----------|--------------|-------------|----------|
| `ValueError` (no API key) | 500 | `LLM_NOT_CONFIGURED` | "LLM not configured..." |
| `AuthenticationError` (401) | 500 | `LLM_AUTH_FAILED` | "Invalid API key..." |
| `RateLimitError` (429) | 500 | `LLM_RATE_LIMIT` | "Rate limit exceeded..." |
| `ConnectionError` | 500 | `LLM_CONNECTION_ERROR` | "Cannot reach LLM provider..." |

**Validation Errors**
- Empty/missing `message`: 422 (Pydantic validation)
- Message > 10,000 chars: 422 (max_length validation)

### OpenAPI Documentation

**FastAPI Auto-Gen**
The endpoint will automatically appear in `/docs` with:
- Request body schema (ChatRequest)
- Response description (SSE streaming)
- Error responses (500 examples)

**Custom Documentation**
Add SSE protocol explanation in endpoint docstring:
```python
@router.post(
    "",
    responses={
        200: {"description": "SSE stream of text chunks"},
        500: {"description": "LLM provider error"},
    },
)
async def chat(...):
    """
    Stream chat response using Server-Sent Events.

    **SSE Format:**
    - Each chunk: `data: <text>\n\n`
    - End marker: `data: [DONE]\n\n`
    - Errors: `event: error\ndata: <error>\n\n`

    **Client Implementation:**
    ```python
    async with httpx.stream("POST", "/api/v1/chat", ...) as resp:
        async for line in resp.aiter_lines():
            if line.startswith("data:"):
                chunk = line[5:].strip()
                if chunk == "[DONE]":
                    break
                print(chunk, end="")
    ```
    """
```

## Acceptance Criteria

- [ ] `POST /api/v1/chat` endpoint exists and is documented
- [ ] Response uses `text/event-stream` content type
- [ ] SSE format matches spec (`data:` prefix, `[DONE]` terminator)
- [ ] Missing LLM API key returns 500 with clear error
- [ ] Invalid API key (401) returns 500 with clear error
- [ ] OpenAPI docs include SSE protocol explanation
- [ ] Unit tests cover happy path and error cases
- [ ] Automated tests cover streaming format + validation (see Test Plan).
- [ ] Manual smoke checklist completed (see Test Plan).

## Test Plan

### Automated

**Happy Path Tests**
```python
# tests/test_api/test_chat.py
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock

class TestChatEndpoint:
    """Tests for POST /api/v1/chat"""

    @pytest.mark.asyncio
    async def test_chat_streams_response(self, client: AsyncClient):
        """Chat endpoint returns SSE stream."""
        # Mock LLM service
        mock_llm = AsyncMock()
        mock_llm.stream_chat = AsyncMock(return_value=aiter_chunks([
            "Hello", " ", "world", "!"
        ]))

        with patch("backend.services.llm_service.llm_service", mock_llm):
            response = await client.post(
                "/api/v1/chat",
                json={"message": "Say hello"}
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"

            content = response.text
            assert "data: Hello" in content
            assert "data: [DONE]" in content

    @pytest.mark.asyncio
    async def test_chat_with_context(self, client: AsyncClient):
        """Context is passed to LLM service."""
        mock_llm = AsyncMock()
        mock_llm.stream_chat = AsyncMock(return_value=aiter_chunks(["Response"]))

        with patch("backend.services.llm_service.llm_service", mock_llm):
            await client.post(
                "/api/v1/chat",
                json={
                    "message": "Test",
                    "context": "Context: Task 1, Task 2"
                }
            )

            # Verify context was added
            messages = mock_llm.stream_chat.call_args[0][0]
            assert any("Context: Task 1, Task 2" in m["content"] for m in messages)
```

**Error Handling Tests**
```python
    @pytest.mark.asyncio
    async def test_chat_missing_api_key(self, client: AsyncClient):
        """Missing API key returns 500 error."""
        mock_llm = AsyncMock()
        mock_llm.stream_chat = AsyncMock(
            side_effect=ValueError("LLM not configured")
        )

        with patch("backend.services.llm_service.llm_service", mock_llm):
            response = await client.post(
                "/api/v1/chat",
                json={"message": "Test"}
            )

            assert response.status_code == 500
            assert "LLM not configured" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_chat_invalid_message(self, client: AsyncClient):
        """Empty message returns 422 validation error."""
        response = await client.post("/api/v1/chat", json={"message": ""})
        assert response.status_code == 422
        assert "message" in str(response.json())

    @pytest.mark.asyncio
    async def test_chat_missing_message(self, client: AsyncClient):
        """Missing message field returns 422."""
        response = await client.post("/api/v1/chat", json={})
        assert response.status_code == 422
```

**Helper: Mock Async Iterator**
```python
async def aiter_chunks(chunks: list[str]):
    """Create async iterator from list."""
    for chunk in chunks:
        yield chunk
```

### Manual

1. Start API server
2. Test with curl:
   ```bash
   curl -N http://localhost:8080/api/v1/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Say hello"}'
   ```
3. Verify SSE stream format (each `data:` line, `[DONE]` at end)
4. Test error case: remove `LLM_API_KEY` and verify 500 error
5. Open `/docs` and verify chat endpoint is documented

### Manual Test Checklist

- [ ] Streaming response emits `Content-Type: text/event-stream`.
- [ ] Each token/chunk is delivered as `data: ...` lines; terminates with `[DONE]`.
- [ ] Empty/missing `message` returns 422 validation error.
- [ ] Missing/invalid LLM config returns a clear, actionable error response.
- [ ] `/docs` explains the streaming format clearly for clients.

### Run Commands

```bash
make test
# or
uv run pytest -v
```

### Integration with PR-003-1

- Ensure `LLMService` from PR-003-1 is imported correctly
- Test with actual OpenRouter API key (manual test)
- Verify streaming works end-to-end

## Notes / Risks / Open Questions

- Should we support streaming with WebSocket instead of SSE for web clients?
- How should we handle partial SSE messages (network interruptions)?
- Should we add rate limiting at the API level (beyond provider limits)?

## Dependencies

- PR-001 (DB + Config)
- PR-002 (Task CRUD API)
- PR-003-1 (LLM Provider Service)

## Next PRs

- **PR-003-3**: TUI Chat Integration (uses this endpoint)
- **PR-005-2**: RAG Context Injection (adds context parameter)
