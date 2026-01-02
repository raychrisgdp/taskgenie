# PR-010: Web UI (Spec)

**Status:** Spec Only  
**Depends on:** PR-002, PR-004 (attachment viewing), PR-003 (chat optional)  
**Last Reviewed:** 2025-12-30

## Goal

Provide a secondary web interface for managing tasks and viewing attachments, with
optional chat streaming.

## User Value

- Easier reading of longer task descriptions and attachments.
- A fallback UX when terminal UI is not ideal.

## References

- `docs/01-design/DESIGN_WEB.md`
- `docs/01-design/DESIGN_CHAT.md`
- `docs/01-design/API_REFERENCE.md`

## Docs Links

- `README.md`
- `docs/INDEX.md`
- `docs/USER_GUIDE.md`
- `docs/01-design/DESIGN_WEB.md`
- `docs/01-design/DESIGN_CHAT.md`
- `docs/01-design/API_REFERENCE.md`

## Scope

### In

- Task list, detail, create, and edit pages (HTMX forms).
- Attachment viewing pages for reading attachment content.
- Basic responsive layout.
- Optional chat page if PR-003 is implemented.

### Out

- Authentication/multi-user.
- Advanced mobile-first polish.

## Mini-Specs

- FastAPI template routes for tasks list/detail and edit/create.
- Attachment viewing pages for displaying attachment content.
- HTMX interactions for inline updates and form submissions.
- Optional chat page using SSE via EventSource.

## User Stories

- As a user, I can view and edit tasks in a browser.
- As a user, I can read long attachment content comfortably.
- As a user, I can use chat in the browser when available.

## UX Notes (if applicable)

- Keep JS minimal and favor HTMX for interactions.

## Technical Design

### Architecture

- FastAPI + Jinja2 templates for server-rendered pages.
- HTMX for partial updates; Tailwind (or equivalent) for styling.

### Data Model / Migrations

- N/A.

### API Contract

- Uses existing task API for CRUD operations.
- Optional chat page uses `/api/v1/chat` SSE.

### Background Jobs

- N/A.

### Security / Privacy

- N/A (no auth in MVP).

### Error Handling

- Render friendly error states when API calls fail.

## Acceptance Criteria

### AC1: Task Pages

**Success Criteria:**
- [ ] List/detail/create/edit flows work against the API.

### AC2: Attachment Viewing

**Success Criteria:**
- [ ] Attachment viewing pages display attachment content correctly.

### AC3: Responsive Layout

**Success Criteria:**
- [ ] Pages remain usable on narrow viewports.

### AC4: Optional Chat UI

**Success Criteria:**
- [ ] If PR-003 is present, chat page streams responses and handles disconnects.

## Test Plan

### Automated

- Integration tests for page rendering and basic actions.
- Optional Playwright smoke test for task flow.

### Manual

- Verify task CRUD in the browser and resize for responsiveness.
- If chat enabled, verify streaming behavior.

## Notes / Risks / Open Questions

- Keep the web UI optional so it does not block core TUI iteration.
