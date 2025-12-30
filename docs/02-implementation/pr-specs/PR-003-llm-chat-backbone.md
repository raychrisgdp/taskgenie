# PR-003: LLM + Chat Backbone (Spec)

**Status:** Spec Only  
**Depends on:** PR-001, PR-002, PR-008  
**Last Reviewed:** 2025-12-30

## Goal

Make chat real:
- implement multi-provider LLM service (OpenRouter/BYOK)
- expose a streaming Chat API
- wire the interactive TUI chat panel to the backend

## User Value

- The primary interaction mode (chat inside the TUI) becomes usable.
- Users can ask questions and trigger task actions without leaving the TUI.

## Scope

### In

- LLM provider abstraction (at minimum OpenRouter via OpenAI SDK; optional OpenAI-compatible providers).
- Chat endpoint supporting streaming.
- TUI chat view talks to the API and renders streaming responses.
- “No LLM configured” is a first-class UX (clear message, no crash).

### Out

- RAG/semantic search context injection (PR-005).
- Advanced tool-calling / agent spawning (future).

## Mini-Specs

- LLM provider configuration:
  - OpenRouter via OpenAI SDK (OpenAI-compatible `base_url` + `api_key`).
  - model selection via config (`LLM_MODEL`, etc).
- Streaming chat endpoint:
  - `POST /api/v1/chat` returns SSE (chunked `data:` messages + `[DONE]`).
- TUI wiring:
  - chat panel sends user messages and renders streaming output.
  - friendly UX for “not configured”, 401, rate limit, and network errors.
- Observability:
  - structured logs for provider errors (no secrets in logs).

## References

- `docs/01-design/DESIGN_CHAT.md` (streaming + error handling)
- `docs/01-design/API_REFERENCE.md` (chat endpoint shape)
- `docs/01-design/DESIGN_TUI.md` (TUI chat panel wiring)
- `docs/01-design/DECISIONS.md` (provider strategy)

## User Stories

- As a user, I can ask “what’s due today?” from inside the TUI and get a streamed response.
- As a user, I can use my own API key (BYOK) and switch models/providers.
- As a user, if my API key is missing/invalid, the UI tells me exactly what to configure.

## Technical Design

### Provider abstraction

- `LLMService` in `backend/services/llm_service.py`:
  - `async def stream_chat(messages: List[Dict[str, str]]) -> AsyncIterator[str]`
  - Configurable `base_url` and `api_key` for OpenRouter/OpenAI compatibility.

### API contract (streaming)

- `POST /api/v1/chat` (see `docs/01-design/API_REFERENCE.md` for request fields)
- Request: `application/json`
- Response: Server-Sent Events (SSE) stream (`text/event-stream`)
  - Each chunk: `data: <text chunk>\n\n`
  - Terminator: `data: [DONE]\n\n`

### TUI integration

- `ChatPanel` widget:
  - Uses `httpx.AsyncClient` with `stream=True`
  - Appends streamed text chunks to the chat transcript incrementally
  - Handles `ConnectTimeout` and `401 Unauthorized` with user-friendly modals

### Error mapping

- Normalize common failures:
  - missing API key → “configure LLM” message
  - 401 → “invalid key”
  - 429 → “rate limit” + retry suggestion
  - network error → “cannot reach provider”

## Acceptance Criteria

- [ ] Chat endpoint returns a streaming response.
- [ ] TUI can send a message and display a streamed reply.
- [ ] Missing/invalid API key results in a clear error message (in TUI and API).
- [ ] Provider selection (model/base_url) works via config.

## Test Plan

### Automated

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
        mock_llm = AsyncMock()
        mock_llm.stream_chat = AsyncMock(return_value=async_gen_chunks(["Hello", " ", "world", "!"]))

        with patch("backend.services.llm_service.llm_service.stream_chat", mock_llm):
            response = await client.post("/api/v1/chat", json={"message": "Hello"})
            assert response.status_code == 200

            # Verify SSE stream format
            content = response.text
            assert "data:" in content
            assert "[DONE]" in content

    @pytest.mark.asyncio
    async def test_chat_missing_api_key(self, client: AsyncClient):
        """Missing API key returns clear error."""
        with patch("backend.services.llm_service.llm_service", side_effect=ValueError("API key not configured")):
            response = await client.post("/api/v1/chat", json={"message": "test"})
            assert response.status_code == 500
            assert "configure" in response.json()["detail"].lower()


class TestLLMService:
    """Tests for LLM provider abstraction"""

    @pytest.mark.asyncio
    async def test_stream_chat_openrouter(self):
        """OpenRouter integration works."""
        from backend.services.llm_service import LLMService
        from unittest.mock import AsyncMock

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.aiter_bytes.return_value = [b"data: Hello", b"data: World", b"data: [DONE]"]
        mock_client.stream.return_value = mock_response

        service = LLMService(api_key="test-key", base_url="https://openrouter.ai/api")
        service._client = mock_client

        chunks = []
        async for chunk in service.stream_chat([{"role": "user", "content": "test"}]):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0].decode() == "data: Hello"
        assert chunks[2].decode() == "data: [DONE]"

    @pytest.mark.asyncio
    async def test_error_handling_401(self):
        """401 Unauthorized returns clear error."""
        from backend.services.llm_service import LLMService
        from unittest.mock import AsyncMock, MagicMock

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Invalid API key"}
        mock_client.stream.return_value = mock_response

        service = LLMService(api_key="bad-key")
        service._client = mock_client

        with pytest.raises(ValueError, match="Invalid API key"):
            async for _ in service.stream_chat([{"role": "user", "content": "test"}]):
                pass
```

```python
# tests/test_services/test_rag_context.py
import pytest

class TestRAGContext:
    """Tests for RAG context building"""

    @pytest.mark.asyncio
    async def test_build_context_includes_metadata(self, rag_service_test):
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
    async def test_build_context_no_results(self, rag_service_test):
        """Context message when no relevant results."""
        mock_search = AsyncMock(return_value=[])
        rag_service_test.search = mock_search

        context = await rag_service_test.build_context("test query", n_results=3)
        assert "No relevant tasks found" in context
```

### Manual

1. Configure a valid API key and model.
2. Start API and run `tgenie`:
   - send "What tasks are due today?"
   - verify response streams and renders correctly
3. Unset API key and retry:
   - verify UI explains how to configure LLM and does not crash

## Notes / Risks / Open Questions

- Keep SSE payload format consistent across TUI and Web UI to avoid divergence.
- Avoid logging prompts/responses by default (privacy).
