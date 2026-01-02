# PR-008: Interactive TUI (Tasks MVP) (Spec)

**Status:** Spec Only  
**Depends on:** PR-002  
**Last Reviewed:** 2025-12-29

## Goal

Ship a first-class interactive TUI so we can iterate on UX early.

## User Value

- Users can try the product quickly and give feedback.
- Provides a primary workflow before integrations and RAG.

## References

- `docs/01-design/DESIGN_TUI.md`
- `docs/01-design/DESIGN_ARCHITECTURE.md`
- `docs/01-design/DESIGN_DATA.md`

## Docs Links

- `README.md`
- `docs/INDEX.md`
- `docs/USER_GUIDE.md`
- `docs/01-design/DESIGN_CLI.md`
- `docs/01-design/API_REFERENCE.md`

## Scope

### In

- `tgenie` launches the interactive TUI by default.
- Task list, detail, create/edit, and mark-done flows.
- Empty/loading/error states and confirmation for destructive actions.
- Placeholder chat panel (no LLM yet).

### Out

- Attachment viewing (PR-004).
- LLM-backed chat (PR-003).
- Agent panel and tool execution UI (PR-015).
- Full web UI (PR-010).

## Mini-Specs

- Textual-based app with list/detail split view and modal forms.
- Keybindings for navigation and common actions.
- Async API client for PR-002 endpoints with retry flow.
- Clear UI states for empty list and API-down scenarios.

## User Stories

- As a user, I can open `tgenie` and see my tasks.
- As a user, I can create and edit tasks without leaving the UI.
- As a user, I can mark tasks done and see status update.
- As a user, I see a clear error when the API is unavailable.

## UX Notes (if applicable)

- Prefer visible affordances (help bar, hints) over hidden shortcuts.
- Destructive actions require confirmation.

## Technical Design

### Architecture

- Textual app in `backend/cli/tui/` with screens and widgets for list/detail/forms.
- Thin client: all task mutations go through the API.

### Data Model / Migrations

- N/A.

### API Contract

- Uses PR-002 task endpoints for all CRUD operations.

### Background Jobs

- N/A.

### Security / Privacy

- N/A.

### Error Handling

- Timeouts and connection failures show a banner/state and allow retry.
- API errors are surfaced as friendly messages, not stack traces.

## Acceptance Criteria

### AC1: Tasks MVP Flows

**Success Criteria:**
- [ ] `tgenie` opens a responsive TUI without tracebacks.
- [ ] Create/list/show/edit/done flows work against the API.

### AC2: Navigation and Keybindings

**Success Criteria:**
- [ ] Navigation keys and action bindings work consistently.
- [ ] Delete requires confirmation.

### AC3: Empty and Error States

**Success Criteria:**
- [ ] Empty list and API-down states are clear and recoverable.

## Test Plan

### Automated

- Widget tests for rendering and message passing.
- App tests for keybindings and error handling with mocked API client.

### Manual

- Run the API and verify task flows end to end.
- Stop the API and verify the TUI shows a recoverable error state.

## Notes / Risks / Open Questions

- Ensure non-interactive CLI commands remain available (PR-009).
