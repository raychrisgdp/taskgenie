# PR-003-1: LLM Provider Abstraction & Configuration (Spec)

**Status:** Spec Only
**Depends on:** PR-001
**Last Reviewed:** 2025-12-31

## Goal

Implement the core LLM provider abstraction and configuration system that supports multiple providers (OpenRouter, OpenAI, custom endpoints) with a unified interface.

## User Value

- Users can configure any OpenAI-compatible LLM provider
- Model selection is flexible (configurable via env vars or config file)
- Provider configuration is centralized and testable

## Scope

### In

- `LLMService` class in `backend/services/llm_service.py`
- Support for OpenRouter via OpenAI SDK (OpenAI-compatible)
- Configuration via settings (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`)
- Stream generation interface: `async def stream_chat(messages) -> AsyncIterator[str]`
- Error handling for missing/invalid credentials
- Singleton instance pattern

### Out

- RAG context injection (PR-003-3)
- Tool calling / agent spawning (future)
- Multiple concurrent providers (single provider only)

## Mini-Specs

- Provider abstraction via `LLMService`
- OpenAI-compatible client with configurable base URL
- Streaming generation: `stream_chat(...) -> AsyncIterator[str]`
- Clear error mapping for auth/rate limits/network

## References

- `docs/01-design/DESIGN_CHAT.md` (chat architecture + streaming expectations)
- `docs/01-design/API_REFERENCE.md` (chat endpoint shape)

## Technical Design

### Provider Interface

```python
class LLMService:
    """LLM provider abstraction."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "openai/gpt-4o-mini",
    ):
        self.api_key = api_key or settings.llm_api_key
        self.base_url = base_url or settings.llm_base_url
        self.model = model or settings.llm_model
        self._client: AsyncOpenAI | None = None

    @property
    def client(self) -> AsyncOpenAI:
        """Lazy-initialize OpenAI client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "LLM_API_KEY not configured. "
                    "Set environment variable or config file."
                )
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._client

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream chat response."""
        if not self.api_key:
            raise ValueError("LLM not configured")

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            **kwargs,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
```

### Configuration

**Environment Variables**
```bash
# .env
LLM_API_KEY=sk-ant-api03-...
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=openai/gpt-4o-mini
```

**Config File**
```toml
# ~/.taskgenie/config.toml
[llm]
api_key = "sk-ant-api03-..."
base_url = "https://openrouter.ai/api/v1"
model = "openai/gpt-4o-mini"
```

### Error Mapping

| Error Type | User Message | Action |
|------------|--------------|--------|
| `ValueError` (no API key) | "Configure LLM: Set LLM_API_KEY in .env or config file" | User setup |
| `AuthenticationError` (401) | "Invalid API key. Check LLM_API_KEY configuration" | User setup |
| `RateLimitError` (429) | "Rate limit exceeded. Try again later." | Wait/retry |
| `ConnectionError` | "Cannot reach LLM provider. Check LLM_BASE_URL" | Network issue |

## Acceptance Criteria

- [ ] `LLMService` class implements stream_chat interface
- [ ] Configuration loads from env vars and config file
- [ ] Missing API key raises clear `ValueError` with setup instructions
- [ ] Invalid API key (401) raises `AuthenticationError`
- [ ] OpenRouter integration works end-to-end
- [ ] Unit tests cover configuration and error paths
- [ ] Automated tests cover streaming + error mapping (see Test Plan).
- [ ] Manual smoke checklist completed (see Test Plan).

## Test Plan

### Automated

```python
# tests/test_services/test_llm_service.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

class TestLLMServiceConfiguration:
    """Test configuration and initialization."""

    def test_loads_from_env_vars(self, monkeypatch):
        """Load config from environment variables."""
        monkeypatch.setenv("LLM_API_KEY", "test-key")
        monkeypatch.setenv("LLM_BASE_URL", "https://test.api")
        monkeypatch.setenv("LLM_MODEL", "test-model")

        service = LLMService()
        assert service.api_key == "test-key"
        assert service.base_url == "https://test.api"
        assert service.model == "test-model"

    def test_missing_api_key_raises_error(self, monkeypatch):
        """Missing API key raises clear error."""
        monkeypatch.delenv("LLM_API_KEY", raising=False)

        service = LLMService()
        with pytest.raises(ValueError, match="LLM_API_KEY not configured"):
            _ = service.client

class TestLLMServiceStream:
    """Test streaming chat."""

    @pytest.mark.asyncio
    async def test_stream_chat_yields_chunks(self):
        """Stream yields text chunks."""
        mock_client = AsyncMock()

        # Mock streaming response
        chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=" "))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content="world"))]),
        ]
        mock_client.chat.completions.create = AsyncMock(
            return_value=aiter_mock(chunks)
        )

        service = LLMService(api_key="test")
        service._client = mock_client

        result = []
        async for chunk in service.stream_chat([{"role": "user", "content": "test"}]):
            result.append(chunk)

        assert result == ["Hello", " ", "world"]

    @pytest.mark.asyncio
    async def test_stream_chat_missing_api_key(self):
        """Missing API key raises error."""
        service = LLMService(api_key=None)

        with pytest.raises(ValueError, match="LLM not configured"):
            async for _ in service.stream_chat([{"role": "user", "content": "test"}]):
                pass

    @pytest.mark.asyncio
    async def test_stream_chat_401_error(self):
        """401 error raises AuthenticationError."""
        from openai import AuthenticationError

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=AuthenticationError("Invalid API key")
        )

        service = LLMService(api_key="test")
        service._client = mock_client

        with pytest.raises(AuthenticationError):
            async for _ in service.stream_chat([{"role": "user", "content": "test"}]):
                pass
```

### Manual

1. Configure OpenRouter API key in `.env`
2. Run Python REPL:
   ```python
   from backend.services.llm_service import llm_service
   import asyncio

   async def test():
       async for chunk in llm_service.stream_chat([
           {"role": "user", "content": "Say hello"}
       ]):
           print(chunk, end="", flush=True)

   asyncio.run(test())
   ```
3. Verify response streams correctly
4. Remove API key and verify error message is clear

### Manual Test Checklist

- [ ] `LLMService` reads `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL` from settings.
- [ ] Missing key produces a clear, actionable error (no stack traces).
- [ ] Streaming yields chunks incrementally (not buffered until end).
- [ ] Auth (401) and rate limit (429) paths map to actionable messaging.
- [ ] Update `.env.example` to add `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL` variables.

### Run Commands

```bash
make test
# or
uv run pytest -v
```

## Notes / Risks / Open Questions

- Should we support multiple provider instances (e.g., for A/B testing models)?
- Should model defaults vary by provider (e.g., OpenRouter vs OpenAI)?

## Dependencies

- `openai` SDK: `uv add openai`
- Environment configuration: PR-001

## Next PRs

- **PR-003-2**: Streaming Chat API Endpoint (uses this service)
- **PR-003-3**: TUI Chat Integration (uses PR-003-1 + PR-003-2)
