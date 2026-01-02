# PR-015: Agent UX Panel (Spec)

**Status:** Spec Only  
**Depends on:** PR-008, PR-003B, PR-013, PR-014  
**Last Reviewed:** 2026-01-01

## Goal

Add a TUI panel for agent runs, tool execution status, and controls.

## User Value

- Users can see what the agent is doing and intervene when needed.
- Tool execution is transparent and traceable.

## References

- `docs/01-design/DESIGN_TUI.md`
- `docs/01-design/DESIGN_CHAT.md`

## Docs Links

- `README.md`
- `docs/INDEX.md`
- `docs/USER_GUIDE.md`
- `docs/01-design/DESIGN_CLI.md`
- `docs/01-design/API_REFERENCE.md`

## Scope

### In

- Agent panel in the TUI showing run status and recent actions.
- Tool execution timeline with success/failure states.
- Controls to pause, resume, and cancel agent runs.
- Real-time updates via event stream (PR-013).

### Out

- Web UI for agent runs.
- Multi-agent visualization dashboards.

## Mini-Specs

- New TUI screen/panel showing agent run list and details.
- Status indicator (running/paused/failed/completed) with timestamps.
- Keybindings for pause/resume/cancel actions.
- Inline view of recent tool calls and results.

## User Stories

- As a user, I can see when an agent starts, progresses, and finishes.
- As a user, I can pause or cancel a run from the TUI.

## UX Notes (if applicable)

- Avoid showing hidden reasoning; show tool actions and status only.

## Technical Design

### Architecture

- TUI panel subscribes to SSE events for agent run updates.
- Agent controls call agent run endpoints (`/api/v1/agents/...`).

### Data Model / Migrations

- N/A.

### API Contract

- Uses PR-014 run endpoints and PR-013 event stream.

### Background Jobs

- N/A.

### Security / Privacy

- Do not display or log raw prompts by default.

### Error Handling

- If event stream disconnects, show a recoverable error state and retry option.

## Acceptance Criteria

### AC1: Agent Panel Rendering

**Success Criteria:**
- [ ] Agent panel renders and updates in real time.

### AC2: Tool Execution Visibility

**Success Criteria:**
- [ ] Tool calls and results appear in the timeline with statuses.

### AC3: Run Controls

**Success Criteria:**
- [ ] Pause/resume/cancel actions work from the TUI.

## Test Plan

### Automated

- TUI widget tests for agent panel rendering.
- Integration tests with mocked SSE events and agent API calls.

### Manual

- Start an agent run and verify live status updates and controls.

## Notes / Risks / Open Questions

- Decide how much tool detail to surface without overwhelming users.
