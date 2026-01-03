# PR-002: Task CRUD API (Spec)

**Status:** Spec Only  
**Depends on:** PR-001  
**Last Reviewed:** 2026-01-02

## Goal

Provide the minimal API surface to create, read, update, and delete tasks with basic
filtering and pagination.

## User Value

- Enables the first usable UI (TUI) quickly.
- Establishes a stable contract for later features.

## References

- `docs/01-design/DESIGN_DATA.md`
- `docs/01-design/API_REFERENCE.md`
- `docs/01-design/DESIGN_CLI.md`

## Docs Links

- `README.md`
- `docs/INDEX.md`
- `docs/USER_GUIDE.md`
- `docs/01-design/DESIGN_DATA.md`
- `docs/01-design/API_REFERENCE.md`
- `docs/01-design/DESIGN_CLI.md`

## Scope

### In

- REST endpoints for task CRUD.
- Basic filters (status, priority, due_before, due_after) and pagination.
- Input validation and consistent error shape.
- Task responses include `attachments: []` until PR-004 lands (no attachment joins).

### Out

- Attachments (PR-004).
- Semantic search (PR-005).
- Event system and realtime updates (PR-013).
- Agent tool schema and actions (PR-003B).
- Authentication/multi-user.

## Mini-Specs

- Implement `/api/v1/tasks` CRUD endpoints with pagination defaults.
- Validate enums and required fields at the API boundary.
- Standardize error responses (404 and validation).
- Publish OpenAPI schemas with examples aligned to `API_REFERENCE.md`.
- List responses include `total`, `page`, and `page_size` (page derived from limit/offset).
- Default ordering: `created_at DESC, id ASC` for stable pagination.

## User Stories

- As a user, I can create tasks and see them appear in my task list.
- As a user, I can update task status/priority/ETA and see it reflected everywhere.
- As a user, I can filter tasks by status, priority, and due window.

## UX Notes (if applicable)

- N/A.

## Technical Design

### Architecture

- FastAPI router with service/repository layer; no direct DB access from clients.
- Use async SQLAlchemy sessions.

### Data Model / Migrations

- `Task` fields: id (UUID string), title, description, status, priority, eta,
  created_at, updated_at, tags, metadata.
- Use existing indexes from PR-001 (`status`, `priority`, `eta`, `created_at`); no new migrations.

### API Contract

- `POST /api/v1/tasks` -> 201 Created.
- `GET /api/v1/tasks` -> 200 OK, supports filters and `limit`/`offset` (defaults 50/0).
- `GET /api/v1/tasks/{id}` -> 200 OK.
- `PATCH /api/v1/tasks/{id}` -> 200 OK, partial update.
- `DELETE /api/v1/tasks/{id}` -> 204 No Content.
- Error shape: `{"error": "...", "code": "TASK_NOT_FOUND"}` for 404s.
- List response shape: `{ "tasks": [...], "total": <int>, "page": <int>, "page_size": <int> }`
  where `page = floor(offset / limit) + 1` and `page_size = limit`.
- Task response includes `attachments: []` until PR-004.

### Background Jobs

- N/A.

### Security / Privacy

- N/A (no auth in MVP).

### Error Handling

- Validation errors return 422 with clear field errors.
- Not found uses standard error shape and code.

## Acceptance Criteria

### AC1: CRUD Endpoints

**Success Criteria:**
- [ ] All CRUD endpoints exist and match `API_REFERENCE.md`.
- [ ] OpenAPI docs render endpoints and schemas.

### AC2: Validation and Error Shape

**Success Criteria:**
- [ ] Empty titles and invalid enums are rejected.
- [ ] 404 responses use the standard error shape and code.

### AC3: Filters and Pagination

**Success Criteria:**
- [ ] List endpoint supports status, priority, due_before, due_after.
- [ ] Limit/offset default to 50/0 and are enforced.
- [ ] List response includes `total`, `page`, and `page_size` consistent with limit/offset.
- [ ] Default sort order is `created_at DESC, id ASC`.

## Test Plan

### Automated

- API tests for CRUD, validation, and 404s.
- API tests for filters and pagination ordering.
- API tests for list response shape (`total`, `page`, `page_size`) and default ordering.
- API tests confirm `attachments` is an empty list for tasks.

### Manual

- Use curl to create/list/get/update/delete tasks.
- Verify filtering results for status and due windows.

## Notes / Risks / Open Questions

- None.
