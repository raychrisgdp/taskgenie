# Interactive TUI Design (Textual)

**Status:** Spec Only  
**Last Reviewed:** 2025-12-29

## Goals

- **TUI-first UX:** `tgenie` launches an interactive terminal UI by default.
- **Fast iteration:** optimize for usability feedback early (before integrations/RAG).
- **Thin client:** the TUI calls the API (no duplicated business logic).
- **Works offline-ish:** clear “API down” state with recovery guidance (and optional local-only mode later).

## Non-Goals

- Perfect feature parity with web UI.
- Full “power user” scripting (handled via CLI subcommands).
- Multi-user auth, remote hosting, or cross-device sync.

## Entry Points

- **Interactive:** `tgenie` → full-screen Textual app.
- **One-shot (optional):** `tgenie "What’s due today?"` → sends a chat query (requires chat backend).
- **Scripting:** `tgenie add/list/show/...` (non-interactive subcommands).

## Screen Layout (MVP)

```
┌─────────────────────────────────────────────────────────────────────┐
│ tgenie                                         [Filter: All]      │
├─────────────────────────┬───────────────────────────────────────────┤
│ Task List               │ Task Detail                               │
│                         │                                           │
│ ● [HIGH] Review PR #123  │ Title: Review PR #123                     │
│   Fix authentication bug │ Status: pending                           │
│   Due: Jan 15, 2025     │ Priority: high                            │
│                         │ ETA: 2025-01-15                            │
│ ○ [MED] Update docs     │                                           │
│   Add API examples      │ Description:                              │
│   Due: Jan 20, 2025     │ Fix authentication bug in login flow     │
│                         │ Needs security team review before merging   │
│ ○ [LOW] Clean up tasks  │                                           │
│   Archive completed     │ Attachments:                              │
│                         │ • github: owner/repo/pull/123             │
│                         │ • gmail: 18e4f7a2b3c4d5e                   │
├─────────────────────────┴───────────────────────────────────────────┤
│ [a]dd  [e]dit  [d]one  [D]elete  [/]search  [?]help  [q]uit        │
└─────────────────────────────────────────────────────────────────────┘
```

### Color Coding

| Priority | Color | Symbol |
|----------|-------|--------|
| critical | red | `!` |
| high | orange | `●` |
| medium | yellow | `◐` |
| low | dim | `○` |

| Status | Style |
|--------|-------|
| pending | normal |
| in_progress | blue text |
| completed | dim + strikethrough |

### Key UX requirements (MVP)

- **Fast navigation:** arrow keys / j-k optional later, but must support at least arrows + enter.
- **Predictable actions:** Add/Edit/Done/Delete accessible via a small, visible command bar (not only hidden shortcuts).
- **Clear states:** empty tasks, loading, API-down, validation errors.
- **No surprises:** destructive actions require confirmation.

## Interaction Model

### Navigation

- Focus can move between:
  1) task list
  2) detail pane
  3) chat panel / command input
- A single “command palette” (`/` or `:`) is optional, but can be added later.

### Suggested shortcuts (subject to iteration)

- `a`: add task
- `e`: edit selected task
- `d`: mark done
- `x`: delete (confirm)
- `r`: refresh
- `?`: help
- `q`: quit

## Architecture

### Components

```
backend/cli/tui/
├── app.py                 # Main TodoApp (Textual app)
├── client.py              # TaskAPIClient (async HTTP client)
├── styles.tcss            # TCSS styling
├── screens/
│   ├── main.py           # MainScreen (task list + detail)
│   ├── task_detail.py    # TaskDetailScreen (modal)
│   ├── task_form.py      # TaskFormScreen (add/edit modal)
│   └── help.py           # HelpScreen
└── widgets/
    ├── task_list.py      # TaskListView (list container)
    ├── task_item.py      # TaskItem (single row)
    ├── task_detail.py    # TaskDetailPanel (detail view)
    ├── filter_bar.py     # FilterBar (filter controls)
    └── status_bar.py     # StatusBar (bottom status)
```

**Core Components:**

- `TodoApp` (Textual app)
  - Manages API client connection
  - Handles global keybindings (q, ?, r)
  - Coordinates screen navigation
  - Maintains task list state

- `MainScreen`
  - Split layout: TaskListView (left) + TaskDetailPanel (right)
  - FilterBar at top
  - Handles task selection events
  - Task actions: add, edit, complete, delete

- `TaskListView`
  - Renders task list with priority/status styling
  - Sends TaskSelected message on selection
  - Supports keyboard navigation (j/k/g/G/arrows)

- `TaskDetailPanel`
  - Shows selected task details
  - Rich table formatting
  - Displays attachments with type indicators

- `TaskFormScreen` (modal)
  - Add/edit task form
  - Field validation
  - Submits to API on save

### State Management

**UI State Object:**
```python
@dataclass
class AppState:
    tasks: list[dict]
    selected_task_id: str | None
    loading: bool
    error: str | None
    status_filter: str | None
    priority_filter: str | None
    search_query: str | None
```

**Reactive Updates:**
- Status/priority filters trigger automatic list refresh
- Search query updates filtered task view
- Loading state disables actions during API calls

### Keybindings

**Global:**

| Key | Action | Description |
|-----|--------|-------------|
| `q` | Quit | Exit the application |
| `?` | Help | Show help screen |
| `r` | Refresh | Reload tasks from API |
| `/` | Search | Open search input |
| `Escape` | Cancel | Close modal/cancel action |

**Task List:**

| Key | Action | Description |
|-----|--------|-------------|
| `a` | Add | Open new task form |
| `e` | Edit | Edit selected task |
| `d` | Done | Mark selected task complete |
| `D` | Delete | Delete selected task (with confirm) |
| `Enter` | Details | Show task details modal |
| `j` / `Down` | Next | Select next task |
| `k` / `Up` | Previous | Select previous task |
| `g` | Top | Jump to first task |
| `G` | Bottom | Jump to last task |
| `Space` | Toggle | Toggle task selection |

**Filters:**

| Key | Action | Description |
|-----|--------|-------------|
| `1` | All | Show all tasks |
| `2` | Pending | Show pending only |
| `3` | In Progress | Show in_progress only |
| `4` | Completed | Show completed only |
| `p` | Priority | Cycle priority filter |

### API client

- API base URL configurable (env/config).
- Client supports:
  - task CRUD calls
  - (later) chat streaming, attachments endpoints, notifications endpoints

## Error Handling

- **API down:** show a banner ("Cannot connect to backend"), keep UI usable for viewing cached state (if any), and provide retry.
- **Validation errors:** show inline next to the field (create/edit forms).
- **Transient errors:** allow retry without losing user input.
- **Empty state:** Show "No tasks found. Press 'a' to add your first task!"
- **Loading state:** Disable actions, show spinner or loading indicator

## Styling (TCSS)

**Global styles:**
- Surface colors from palette ($surface, $primary, $accent)
- Responsive layout with flexbox
- Modal centering with `align: center middle`

**Component-specific:**
- Task list: 50% width, border, hover effects
- Detail panel: 50% width, rich table formatting
- Filter bar: dark background, button spacing
- Status bar: full width, primary background

**Priority colors:**
- `.priority-critical` → $error (red)
- `.priority-high` → $warning (orange)
- `.priority-medium` → $primary
- `.priority-low` → $text-muted (dim)

**Status styles:**
- `.status-completed` → text-style: strike, opacity: 0.6
- `.status-in-progress` → color: $primary

## Testing

**Widget Testing:**
- Test rendering (priority symbols, status styles)
- Test message passing (TaskSelected)
- Test reactive properties (filter changes)

**App Integration Testing:**
- Mock API client with httpx.AsyncMock
- Test app lifecycle (mount → load tasks → quit)
- Test keybindings (q, ?, r, a, e, d, D)
- Test error handling (API down, validation errors)

**Manual Testing:**
1. Start API server
2. Run `textual run --dev backend.cli.tui.app:TodoApp`
3. Test all workflows: add/edit/complete/delete
4. Test filters (status, priority, search)
5. Stop API and verify error state

**Run tests:**
```bash
pytest tests/test_tui/ -v
textual run --dev backend.cli.tui.app:TodoApp
```

## Design References

- `docs/01-design/DESIGN_ARCHITECTURE.md` (system boundaries)
- `docs/01-design/DESIGN_DATA.md` (task fields)
- `docs/01-design/DESIGN_CHAT.md` (streaming and chat UX)
- `docs/01-design/DESIGN_WEB.md` (states and error patterns to mirror)
- `docs/02-implementation/pr-specs/PR-008-interactive-tui.md` (implementation spec)

## External References

- Textual docs: https://textual.textualize.io/
- Textual widgets: https://textual.textualize.io/widget_gallery/
- Textual testing: https://textual.textualize.io/guide/testing/
- TCSS reference: https://textual.textualize.io/guide/CSS/
