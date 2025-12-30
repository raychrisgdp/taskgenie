# PR-003: LLM + Chat Backbone (Spec)

**Status:** Spec Only  
**Depends on:** PR-001, PR-002, PR-008  
**Last Reviewed:** 2025-12-29

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

- Implement an LLM service with:
  - provider selection via config/env
  - model selection via config/env
  - a single “stream chat completion” method returning incremental tokens/chunks

### API contract (streaming)

- Prefer SSE (`text/event-stream`) as described in `DESIGN_CHAT.md`.
- `POST /api/v1/chat` accepts JSON:
  - `message` (required)
  - optional: `session_id`, `task_context`, `stream` flag (design-dependent)
- Response:
  - streaming `data:` chunks, terminating with `[DONE]`

### TUI integration

- Chat panel:
  - sends user input to the chat endpoint
  - renders streamed chunks incrementally
  - shows inline errors for 401/429/timeouts

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

## Test Plan

### Automated

- Unit: provider selection, request shaping, error mapping.
- Integration:
  - Chat endpoint with a mocked LLM client returns streamed chunks.
  - Error cases: missing key, provider returns 401/429.

### Manual

1. Configure a valid API key and model.
2. Start API and run `tgenie`:
   - send “What tasks are due today?”
   - verify response streams and renders correctly
3. Unset API key and retry:
   - verify UI explains how to configure LLM and does not crash

## Notes / Risks / Open Questions

- Keep SSE payload format consistent across TUI and Web UI to avoid divergence.
- Avoid logging prompts/responses by default (privacy).
