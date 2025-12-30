# PR-010: Web UI (Spec)

**Status:** Spec Only  
**Depends on:** PR-002 (chat optional: PR-003)  
**Last Reviewed:** 2025-12-29

## Goal

Provide a secondary web interface for:
- managing tasks
- richer viewing of attachments (longer text, links)
- optional chat streaming in the browser (once chat exists)

## User Value

- Easy browsing and reading for long attachments.
- A fallback UX when terminal UI isn’t ideal.

## Scope

### In

- Tasks pages:
  - list + filters
  - detail view
  - create/edit (HTMX forms)
- Optional (if PR-003 exists):
  - chat page with streaming responses

### Out

- Authentication/multi-user (future).
- Mobile-first polish beyond basic responsiveness (future iteration).

## References

- `docs/01-design/DESIGN_WEB.md` (page layouts + HTMX interactions)
- `docs/01-design/DESIGN_CHAT.md` (streaming/SSE handling)
- `docs/01-design/API_REFERENCE.md` (API endpoints consumed)

## Technical Design

- Use server-rendered templates (Jinja2) with HTMX for interactions.
- Keep the UI thin:
  - call the same backend services as the API (no duplicated business logic)
  - rely on the Task API for CRUD
- Chat streaming (if enabled):
  - use SSE and handle disconnects with a retry UX

## Acceptance Criteria

- [ ] Task pages work end-to-end against the API.
- [ ] Basic responsive layout (desktop + narrow viewport).
- [ ] If PR-003 is present: chat page streams responses correctly and handles disconnects gracefully.

## Test Plan

### Automated

- Integration: fetch pages and verify key elements render.
- E2E (optional): Playwright smoke test for task list → create → detail.

### Manual

1. Start API.
2. Open tasks page; verify list renders.
3. Create a task; verify it appears and detail page loads.
4. If chat is enabled, open chat page and send a message; verify streaming.

## Notes / Risks / Open Questions

- Keep web UI optional/secondary; avoid blocking core UX iteration in the TUI.
