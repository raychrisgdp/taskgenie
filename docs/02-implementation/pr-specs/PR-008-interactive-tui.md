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
- [ ] Automated tests cover core widget/app behavior (see Test Plan).
- [ ] Manual smoke checklist completed (see Test Plan).

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

### Run Commands

```bash
make test
# or
uv run pytest -v
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

### Manual Test Checklist

- [ ] Task CRUD flows work via the TUI without leaving the app.
- [ ] API-down state is recoverable and clearly messaged (retry works).
- [ ] Filters and search produce correct subsets.
- [ ] Destructive actions prompt for confirmation.
- [ ] TUI remains responsive with a moderate number of tasks (no obvious jank).

## Notes / Risks / Open Questions

- If Textual is adopted, we should ensure a non-interactive mode still exists (`tgenie add`, etc.) for scripting (PR-009).

---

## Skill Integration: tui-dev

### Textual Framework Setup

This PR should follow **tui-dev** skill patterns:

**Dependencies**
```bash
uv add textual
uv add --dev textual-dev
```

**Project Structure**
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

### Keybindings Implementation

**Global Bindings**
| Key | Action | Show in UI |
|-----|--------|-------------|
| `q` | Quit app | Yes |
| `?` | Help screen | Yes |
| `r` | Refresh tasks | Yes |
| `/` | Search input | Yes |
| `Escape` | Cancel/close | No |

**Task List Bindings**
| Key | Action | Description |
|-----|--------|-------------|
| `a` | Add task | Open add task form |
| `e` | Edit task | Open edit task form |
| `d` | Mark done | Set status to "completed" |
| `D` | Delete task | Confirm then delete |
| `Enter` | View details | Show task detail panel |
| `j/k` or `↑/↓` | Navigate | Select next/previous task |
| `g/G` | Jump | First/last task |

**Implementation Pattern**
```python
BINDINGS = [
    Binding("q", "quit", "Quit", show=True),
    Binding("a", "add_task", "Add"),
    Binding("d", "complete_task", "Done"),
    # ...
]

async def action_add_task(self):
    from .task_form import TaskFormScreen
    await self.push_screen(TaskFormScreen(mode="add"))
```

### Layout Design

**Main Screen Split View**
```
┌─────────────────────────┬─────────────────────────┐
│ Task List (50%)        │ Task Detail (50%)       │
│                         │                         │
│ ● [HIGH] Fix auth      │ Title: Fix auth        │
│   Login failing...       │ Status: pending         │
│                         │ Priority: high          │
│ ○ [MED] Update docs     │ ETA: 2025-01-15       │
│   API examples          │                         │
│                         │ Attachments:            │
├─────────────────────────┴─────────────────────────┤
│ [a]dd [e]dit [d]one [D]elete [/]search [?]help [q]uit│
└──────────────────────────────────────────────────────────┘
```

**Color Coding**
| Priority | Symbol | Color |
|----------|---------|-------|
| critical | `!` | red |
| high | `●` | orange |
| medium | `◐` | yellow |
| low | `○` | dim |

| Status | Style |
|--------|-------|
| pending | normal |
| in_progress | blue text |
| completed | dim + strikethrough |

### API Client Pattern

**Async HTTP Client**
```python
class TaskAPIClient:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.client = httpx.AsyncClient(
            base_url=base_url, timeout=30.0
        )

    async def list_tasks(self, **params) -> list[dict]:
        resp = await self.client.get("/api/v1/tasks", params=params)
        resp.raise_for_status()
        return resp.json()["tasks"]
```

**Error Handling**
- Catch `httpx.ConnectError` → show "cannot connect" banner
- Catch `httpx.HTTPStatusError` → show error notification
- Implement retry with 'r' key

### State Management

**Reactive State**
```python
from textual.reactive import reactive

class MainScreen(Screen):
    status_filter: reactive[str | None] = reactive(None)

    def watch_status_filter(self, value):
        self._apply_filters()
```

**App State Container**
```python
@dataclass
class AppState:
    tasks: list[dict] = field(default_factory=list)
    selected_task_id: str | None = None
    loading: bool = False
```

### Testing Patterns

**Widget Testing**
```python
# tests/test_tui/test_widgets.py
@pytest.mark.asyncio
async def test_task_row_rendering():
    task = {"id": "1", "title": "Test", "priority": "high"}
    row = TaskRow(task)
    rendered = row.render()
    assert "●" in str(rendered)
```

**App Integration Testing**
```python
@pytest.mark.asyncio
async def test_app_keybindings():
    app = TodoApp()
    async with app.run_test() as pilot:
        await pilot.press("q")
        # App exits
```

**Running Tests**
```bash
# Run TUI tests
pytest tests/test_tui/ -v

# Dev mode for debugging
textual run --dev backend.cli.tui.app:TodoApp
```

### TCSS Styling

**Key Style Classes**
```css
#task-list {
    width: 50%;
    border: solid $primary;
}

#task-detail {
    width: 50%;
    padding: 1;
}

.priority-critical { color: $error; }
.priority-high { color: $warning; }
.status-completed { text-style: strike; opacity: 0.6; }

.empty-state {
    align: center middle;
    color: $text-muted;
}
```

### Error Handling Patterns

**Empty State**
- Show friendly message when no tasks exist
- Display hint: "Press 'a' to add your first task"

**Connection Error**
- Show banner: "Cannot connect to API"
- Display: "Start backend: uv run backend"
- 'r' key retries connection

**Loading State**
- Show spinner during API calls
- Disable interactions while loading

### Performance Considerations

- Lazy-load large attachment lists
- Debounce search input (200ms delay)
- Cache task list during filter changes
- Use reactive variables to minimize re-renders

**See Also**
- Skill doc: `.opencode/skill/tui-dev/`
- Textual docs: https://textual.textualize.io/
