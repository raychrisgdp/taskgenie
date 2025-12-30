# PR-002: Task CRUD API (Spec)

**Status:** Spec Only  
**Depends on:** PR-001  
**Last Reviewed:** 2025-12-29

## Goal

Provide the minimal API surface to create, read, update, and delete tasks (plus basic filtering/pagination), so UIs can ship early.

## User Value

- Enables the first usable UI (TUI) quickly.
- Establishes a stable contract for future features (attachments, notifications, chat actions).

## Scope

### In

- REST endpoints for tasks:
  - create (`POST /api/v1/tasks`)
  - list (`GET /api/v1/tasks?status=&priority=&due_before=&due_after=&limit=&offset=`)
  - get by id (`GET /api/v1/tasks/{id}`)
  - update (`PATCH /api/v1/tasks/{id}`)
  - delete (`DELETE /api/v1/tasks/{id}`)
- Validation rules (required title, enum validation, timestamps).
- Consistent error format for 400/404/500.

### Out

- Attachments (PR-004).
- Semantic search (PR-005).
- Authentication/multi-user (future).

## References

- `docs/01-design/DESIGN_DATA.md` (task schema + relationships)
- `docs/01-design/API_REFERENCE.md` (endpoint examples)
- `docs/01-design/DESIGN_CLI.md` (commands that will rely on this API)

## User Stories

- As a user, I can create tasks and see them appear in my task list.
- As a user, I can update task status/priority/ETA and see it reflected everywhere.
- As a user, I can filter tasks by status/priority/due window.

## Technical Design

### Data model

- Implement a `tasks` table/model with at least:
  - `id` (uuid/ulid)
  - `title` (required)
  - `description` (optional)
  - `status` (`pending|in_progress|completed`)
  - `priority` (`low|medium|high|critical`)
  - `eta` (optional datetime)
  - `created_at`, `updated_at`
- Add an index for common queries (status + eta).

### API contract

- `POST /api/v1/tasks` → 201 + created task
- `GET /api/v1/tasks` → 200 + list response (`tasks`, `total`, `limit`, `offset`)
- `GET /api/v1/tasks/{id}` → 200 or 404
- `PATCH /api/v1/tasks/{id}` → 200 or 404
- `DELETE /api/v1/tasks/{id}` → 204 or 404

### Validation + transitions

- Validate enums at the API boundary.
- Status transitions can be permissive in MVP; tighten later if needed.

### Error format

- Standardize errors:
  - `{"error": "...", "code": "..."}`

## Acceptance Criteria

- [ ] CRUD endpoints work with expected HTTP status codes.
- [ ] Filtering and pagination work on `GET /tasks`.
- [ ] Unit + integration tests cover happy path and key error cases.

## Test Plan

### Automated

- Unit: task validation, status transition rules, repository/service layer behavior.
- Integration (HTTPX):
  1. Create task → list shows it → get by id returns it.
  2. Patch task status/priority/eta → values persist.
  3. Delete task → subsequent get returns 404.
  4. Invalid payload (missing title / invalid status) returns 400 with useful message.

### Manual

1. Start API server.
2. `curl -X POST .../tasks` to create.
3. `curl .../tasks` to list and verify filters.
4. `curl -X PATCH .../tasks/{id}` to update.
5. `curl -X DELETE .../tasks/{id}` then `GET` to confirm 404.

## Notes / Risks / Open Questions

- Decide whether list endpoints should default-sort (e.g., ETA ascending, then created_at).
