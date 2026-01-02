# PR-004: Attachments + Link Detection (Spec)

**Status:** Spec Only  
**Depends on:** PR-002  
**Last Reviewed:** 2025-12-30

## Goal

Support task attachments and automatically detect URLs in task content.

## User Value

- Users can attach links to tasks and keep context nearby.
- Integrations can be layered later without changing the core workflow.

## References

- `docs/01-design/DESIGN_DATA.md`
- `docs/01-design/INTEGRATION_GUIDE.md`
- `docs/01-design/API_REFERENCE.md`

## Docs Links

- `README.md`
- `docs/INDEX.md`
- `docs/USER_GUIDE.md`
- `docs/01-design/DESIGN_CLI.md`
- `docs/01-design/API_REFERENCE.md`

## Scope

### In

- Attachment model and DB table.
- Attachment CRUD endpoints (create/list/delete; update optional).
- Link detection on task create/update with URL normalization and dedup.
- Provider registry with `match_url` and `normalize` hooks.

### Out

- Fetching content from external services (PR-006/PR-007).
- RAG indexing (PR-005).

## Mini-Specs

- Attachment schema aligned with `DESIGN_DATA.md`.
- Endpoints for creating/listing/deleting attachments under `/api/v1`.
- URL normalization to stable references; dedup per task and reference.
- Auto-detection runs on task create/update for title/description.
- Attachment service exposes safe methods that can be wrapped as tools (PR-003B).

## User Stories

- As a user, I can attach a URL to a task and see it listed.
- As a user, URLs pasted into task content create attachments automatically.
- As a user, duplicate URLs do not create duplicate attachments.

## UX Notes (if applicable)

- N/A.

## Technical Design

### Architecture

- `LinkDetectionService` parses URLs and calls the provider registry.
- Provider registry includes GitHub, Gmail, and generic URL providers.
- Attachment service handles create/list/delete with dedup checks.
- Provide a thin tool wrapper layer in PR-003B (no tool execution here).

### Data Model / Migrations

- `Attachment` fields: id, task_id (FK), type, reference, title, content,
  created_at, updated_at.
- Unique constraint on `(task_id, reference)` to prevent duplicates.

### API Contract

- `POST /api/v1/tasks/{id}/attachments` (or `/api/v1/attachments` with `task_id`).
- `GET /api/v1/tasks/{id}/attachments`.
- `DELETE /api/v1/attachments/{attachment_id}`.

### Background Jobs

- N/A.

### Security / Privacy

- Only store references; no external fetching in this PR.

### Error Handling

- 404 for missing task/attachment.
- 409 conflict for duplicate normalized references.

## Acceptance Criteria

### AC1: Manual Attachment CRUD

**Success Criteria:**
- [ ] Users can add, list, and delete attachments for a task.

### AC2: Auto-Detect URLs

**Success Criteria:**
- [ ] URLs in title/description create attachments automatically.

### AC3: Normalization and Deduplication

**Success Criteria:**
- [ ] Providers normalize URLs to stable references.
- [ ] Duplicate references for a task are rejected or no-op per design.

## Test Plan

### Automated

- API tests for attachment CRUD.
- Unit tests for URL parsing, normalization, and dedup.

### Manual

- Create tasks with URLs in description; verify attachments created.
- Paste duplicate links; verify no duplicate attachments.

## Notes / Risks / Open Questions

- Finalize normalization rules (tracking params, fragments).
