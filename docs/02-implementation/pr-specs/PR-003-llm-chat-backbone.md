# PR-003: LLM + Chat Backbone (Spec)

**Status:** Spec Only  
**Depends on:** PR-001, PR-002, PR-008  
**Last Reviewed:** 2025-12-30

## Goal

Implement provider-agnostic LLM chat with streaming responses and wire it into the TUI.

## User Value

- Chat inside the TUI becomes usable.
- Users can bring their own API keys and models.

## References

- `docs/01-design/DESIGN_CHAT.md`
- `docs/01-design/API_REFERENCE.md`
- `docs/01-design/DESIGN_TUI.md`
- `docs/01-design/DECISIONS.md`

## Scope

### In

- LLM provider abstraction (OpenRouter via OpenAI-compatible SDK).
- Streaming chat API endpoint (SSE).
- TUI chat panel sends messages and renders streamed output.
- Friendly UX for missing/invalid configuration.

### Out

- RAG/semantic search context injection (PR-005).
- Tool-calling foundation (PR-003B).
- Multi-agent orchestration (PR-014).

## Mini-Specs

- Configurable provider settings (`LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`).
- `POST /api/v1/chat` returns SSE with `[DONE]` terminator.
- TUI chat client handles streaming, rate limits, and network errors.
- Structured logging for provider errors without leaking content.

## User Stories

- As a user, I can ask "what is due today?" and get a streamed reply in the TUI.
- As a user, I can use my own API key and switch models/providers.
- As a user, I see clear guidance when my API key is missing or invalid.

## UX Notes (if applicable)

- Show a clear "LLM not configured" state with setup guidance.

## Technical Design

### Architecture

- `LLMService` exposes `stream_chat(messages)` and hides provider details.
- Use OpenAI-compatible client with configurable base URL (OpenRouter default).
- TUI uses `httpx.AsyncClient` streaming to append chunks in real time.

### Data Model / Migrations

- N/A (chat history persistence is out of scope for this PR).

### API Contract

- `POST /api/v1/chat` accepts message list or single message per `API_REFERENCE.md`.
- Response is `text/event-stream` with `data:` chunks and `[DONE]` terminator.

### Background Jobs

- N/A.

### Security / Privacy

- Do not log prompts or responses by default.
- Keys are read from env/config and never persisted to DB.

### Error Handling

- Map provider failures to user-facing errors: missing key, 401 invalid key, 429
  rate limit, and network timeouts.

## Acceptance Criteria

### AC1: Streaming Chat API

**Success Criteria:**
- [ ] Chat endpoint streams SSE chunks and ends with `[DONE]`.

### AC2: TUI Chat Integration

**Success Criteria:**
- [ ] TUI can send a message and display a streamed reply.

### AC3: Configuration and Error UX

**Success Criteria:**
- [ ] Missing or invalid keys produce clear, non-crashing messages.
- [ ] Provider/model configuration works via settings.

## Test Plan

### Automated

- API tests for SSE format and error mapping.
- Unit tests for `LLMService` provider errors.
- TUI client tests using mocked SSE streams.

### Manual

- Configure a valid key and verify streaming replies in the TUI.
- Unset the key and verify setup guidance is shown.

## Notes / Risks / Open Questions

- Keep SSE payload format consistent for TUI and Web UI.
- Tool execution and agent workflows are handled in PR-003B.
