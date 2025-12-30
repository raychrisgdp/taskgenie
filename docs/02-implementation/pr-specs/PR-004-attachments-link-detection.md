# PR-004: Attachments + Link Detection (Spec)

**Status:** Spec Only  
**Depends on:** PR-002  
**Last Reviewed:** 2025-12-29

## Goal

Enable “context-first tasks” by supporting attachments and auto-detecting URLs in task content.

## User Value

- Users can capture a task and paste a URL (GitHub PR, Gmail, doc) and know it will be saved + surfaced later.
- This unlocks integrations incrementally (GitHub/Gmail can be layered on without changing core flows).

## Scope

### In

- Attachment model + schema (type, reference URL, title, cached content, timestamps).
- Attachment CRUD endpoints (at least: create/list/delete; update optional).
- Link detection service that scans task title/description for URLs and creates attachments automatically.
- Minimal provider registry:
  - `match_url(url) -> bool`
  - `normalize(url) -> reference`
  - default provider for “generic url”

### Out

- Fetching content from external services (PR-006/PR-007).
- RAG indexing (PR-005).

## References

- `docs/01-design/DESIGN_DATA.md` (attachment schema)
- `docs/01-design/INTEGRATION_GUIDE.md` (provider protocol pattern)
- `docs/01-design/API_REFERENCE.md` (attachments endpoints, if/when defined)

## User Stories

- As a user, I can attach a URL to a task and see it listed on the task.
- As a user, when I paste a URL into a task description, an attachment is created automatically.
- As a user, I don’t get duplicate attachments for the same link pasted twice.

## Technical Design

### Attachment model

- Attachments belong to a task (`task_id` foreign key).
- Store:
  - `type` (e.g., `url|github|gmail|notion|...`)
  - `reference` (canonical/normalized reference)
  - `title` (optional)
  - `content` (optional cached content; may be empty until integrations run)
  - timestamps

### Endpoints (minimum)

- Create attachment:
  - `POST /api/v1/tasks/{id}/attachments` (or `POST /api/v1/attachments` with `task_id`)
- List attachments for a task:
  - `GET /api/v1/tasks/{id}/attachments`
- Delete attachment:
  - `DELETE /api/v1/attachments/{attachment_id}`

### Auto-detection behavior

- Trigger on:
  - task create
  - task update (title/description changes)
- Deduplicate:
  - avoid creating duplicate attachments for the same normalized URL.

### Attachment lifecycle

- Attachments are created immediately with reference URL.
- Cached content is optional at this stage (can be empty until integrations fetch it).

## Acceptance Criteria

- [ ] Users can manually attach a URL to a task.
- [ ] URLs in task description auto-create attachments.
- [ ] Attachments are listed with the task and have stable IDs.

## Test Plan

### Automated

- Unit: URL extraction + normalization + deduplication.
- Integration:
  1. Create task with URL in description → attachment exists.
  2. Update description to add another URL → new attachment exists.
  3. Update description with same URL formatting (extra params) → no duplicate if normalized.

### Manual

1. Create task with `https://github.com/owner/repo/pull/123` in the description.
2. Verify task details show 1 attachment entry.
3. Edit task and add a second URL; verify attachments list updates.

## Notes / Risks / Open Questions

- Decide canonical URL normalization rules early (strip tracking params? keep fragments?).
