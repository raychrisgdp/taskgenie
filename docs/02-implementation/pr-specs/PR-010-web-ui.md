# PR-010: Web UI (Spec)

**Status:** Spec Only  
**Depends on:** PR-002 (chat optional: PR-003)  
**Last Reviewed:** 2025-12-30

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

## Mini-Specs

- Pages:
  - tasks list + task detail; create/edit flows (HTMX forms).
- Chat (optional):
  - if PR-003 is present, chat page streams responses and handles reconnects.
- Notifications (optional):
  - in-app notification feed view (if PR-011 exists).
- Design:
  - responsive layout; minimal JS (HTMX + Tailwind or equivalent).
- Tests:
  - basic route rendering + API integration smoke tests.

## References

- `docs/01-design/DESIGN_WEB.md` (page layouts + HTMX interactions)
- `docs/01-design/DESIGN_CHAT.md` (streaming/SSE handling)
- `docs/01-design/API_REFERENCE.md` (API endpoints consumed)

## Technical Design

- **Backend:** FastAPI with Jinja2Templates
- **Frontend:**
  - **CSS:** Tailwind CSS (via CDN or standalone CLI)
  - **JS:** HTMX for SPA-like feel without a full framework
- **Patterns:**
  - `GET /tasks` → returns full page
  - `POST /tasks` → returns HTMX fragment (single task row) to be prepended to the list
  - `GET /tasks/{id}/edit` → returns HTMX fragment (form) to swap into the row/modal
- **Chat (optional):**
  - Start with plain SSE via `EventSource` for streaming chat output.
  - If we want tighter HTMX integration later, consider the `htmx-sse` extension.
- **Thin Client:**
  - call the same backend services as the API (no duplicated business logic)
  - rely on the Task API for CRUD

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
