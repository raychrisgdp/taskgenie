# PR-008: Interactive TUI (Tasks MVP) (Spec)

**Status:** Spec Only  
**Depends on:** PR-002  
**Last Reviewed:** 2025-12-29

## Goal

Ship a first-class interactive TUI as early as possible so we can iterate on UX from day 1.

## User Value

- The user can actually “try the product” early (add/list/edit/complete tasks).
- UX feedback happens before heavy features (integrations/RAG) lock in assumptions.

## Scope

### In

- `tgenie` launches an interactive TUI by default.
- Core task workflows:
  - view task list
  - view task details
  - create task
  - edit task
  - mark done
- Clear empty/loading/error states.
- A “chat panel” placeholder is allowed, but real LLM chat is PR-003.

### Out

- Full attachment viewing (PR-004).
- LLM-backed chat (PR-003).
- Full web UI (PR-010).

## Mini-Specs

- Entry point:
  - `tgenie` starts the interactive TUI (tasks MVP).
- Screens/widgets:
  - task list + task detail pane, modal flows for add/edit/delete.
- Keybindings:
  - navigation + common actions (add/edit/done/delete/refresh/help/quit).
- API client:
  - calls PR-002 endpoints; clear API-down errors and retry flow.
- Chat panel:
  - placeholder UI until PR-003, but visible and non-crashing.
- Tests:
  - smoke test for app start + basic widget interactions (where feasible).

## References

- `docs/01-design/DESIGN_TUI.md`
- `docs/01-design/DESIGN_ARCHITECTURE.md`
- `docs/01-design/DESIGN_DATA.md`

## User Stories

- As a user, I can open `tgenie` and immediately see my tasks with status/priority.
- As a user, I can create a task quickly without remembering flags.
- As a user, I can edit a task (title/description/eta/priority) and see it update immediately.
- As a user, I can mark a task done and watch it leave the “pending” list.
- As a user, if the API is down, I see a clear “cannot connect” state (not a traceback).

## UX Notes

- MVP is “tasks-first”; chat can be a visible placeholder until PR-003.
- Prefer visible affordances (help bar / action hints) over hidden shortcuts-only UX.
- Destructive actions (delete) require confirmation.

## Technical Design

### TUI framework

- Prefer **Textual** for a modern full-screen TUI and rapid iteration.
- Use httpx.AsyncClient for API calls
- Use reactive variables for state management (filters, loading state)
- Style with TCSS (Textual CSS)

### Architecture

**File Structure:**
```
backend/cli/tui/
├── __init__.py
├── app.py              # TodoApp (main app class)
├── client.py           # TaskAPIClient (async HTTP wrapper)
├── styles.tcss         # TCSS styling
├── screens/
│   ├── __init__.py
│   ├── main.py         # MainScreen (list + detail split view)
│   ├── task_form.py    # TaskFormScreen (add/edit modal)
│   └── help.py         # HelpScreen
└── widgets/
    ├── __init__.py
    ├── task_list.py    # TaskListView + TaskItem + TaskRow
    ├── task_detail.py  # TaskDetailPanel (rich table)
    ├── filter_bar.py   # FilterBar (filter buttons)
    └── status_bar.py   # StatusBar (bottom status)
```

**Component Layout:**
- A Textual app with:
  - task list pane (filterable, left side)
  - task detail pane (selected task, right side)
  - filter bar at top (status/priority filters)
  - status/help bar at bottom (keybindings)
  - chat pane placeholder (stub, for PR-003)

**Message Passing:**
- TaskListView posts TaskSelected message
- MainScreen receives and updates TaskDetailPanel
- TaskFormScreen posts TaskUpdated message on save
- App handles task refresh/notifications

**Thin client principle:**
- all task operations go through the Task CRUD API
- no direct DB access from the TUI
- API base URL configurable via env var/config

### API Contract

- Requires PR-002 endpoints:
  - `POST /api/v1/tasks`
  - `GET /api/v1/tasks`
  - `GET /api/v1/tasks/{id}`
  - `PATCH /api/v1/tasks/{id}`
  - `DELETE /api/v1/tasks/{id}`
- Mark done uses PATCH: `{"status": "completed"}`.

### Resilience

- API unreachable:
  - show non-blocking banner + retry affordance
  - avoid “hanging” renders (timeouts on HTTP calls)

## Acceptance Criteria

- [ ] `tgenie` opens a responsive TUI (no stack traces).
- [ ] Create/list/show/edit/done flows work end-to-end against the API.
- [ ] UI handles empty state and API-down state with clear messaging.
- [ ] Keyboard navigation works (arrows, j/k, g/G, enter, escape).
- [ ] All keybindings work (a/e/d/D/r/?/q).
- [ ] Filter by status/priority works correctly.
- [ ] Task list shows priority colors and status styling.
- [ ] Task detail panel shows formatted table with attachments.
- [ ] Destructive actions (delete) show confirmation modal.

## Test Plan

### Automated

- Unit: UI state reducers / formatting utilities (where applicable).
- Integration (light): API client calls mocked via HTTPX mock transport.
- Widget tests: TaskRow rendering, TaskListView message passing, reactive properties
- App tests: keybindings, screen navigation, error handling with mocked API

**Test structure:**
```
tests/test_tui/
├── __init__.py
├── test_app.py       # TodoApp lifecycle, keybindings, error handling
├── test_widgets.py   # TaskRow, TaskListView, TaskDetailPanel rendering
└── test_screens.py   # MainScreen, TaskFormScreen modal behavior
```

**Running tests:**
```bash
pytest tests/test_tui/ -v
textual run --dev backend.cli.tui.app:TodoApp
```

### Manual

1. Start the API.
2. Run `tgenie`:
   - empty state renders correctly with hint to add task
   - add a task from the UI → task appears in list with correct styling
   - open task detail → shows fields in rich table format
   - edit task title/eta/priority → persists immediately
   - mark task done → status updates in list (strikethrough)
   - delete task → shows confirmation modal
   - test all filters (1/2/3/4 keys for status, p for priority)
   - test search (/ key) → filters by title/description
3. Stop the API and re-run `tgenie`:
   - UI shows "cannot connect" state and recovery guidance
   - 'r' key retries connection
4. Test all keybindings:
   - 'q' quits app
   - '?' shows help screen
   - 'a' opens add task form
   - 'e' opens edit task form
   - 'd' marks task done
   - 'D' deletes task with confirmation
   - arrows/j/k navigate task list
   - g/G jump to top/bottom
   - Enter shows task details

## Notes / Risks / Open Questions

- If Textual is adopted, we should ensure a non-interactive mode still exists (`tgenie add`, etc.) for scripting (PR-009).
