# PR-006: Gmail Integration (Spec)

**Status:** Spec Only  
**Depends on:** PR-004  
**Last Reviewed:** 2025-12-29

## Goal

Given a Gmail URL attachment, authenticate via OAuth, fetch email content, and cache
it locally on the attachment.

## User Value

- Email-linked tasks keep essential context without reopening Gmail.
- Cached email content can later be searched via RAG.

## References

- `docs/01-design/INTEGRATION_GUIDE.md`
- `docs/01-design/DESIGN_DATA.md`
- `docs/01-design/DESIGN_BACKGROUND_JOBS.md`

## Scope

### In

- Gmail URL normalization to a stable reference.
- OAuth flow for local machines and secure credential storage.
- Fetch subject/from/to/date/body and store in `attachment.content`.
- Explicit refresh action and/or background fetch for pending attachments.

### Out

- Two-way sync or bulk ingestion.

## Mini-Specs

- Provider that parses Gmail URLs and normalizes to `gmail:<id>`.
- OAuth setup command and token storage under `~/.taskgenie/credentials/` with 0600.
- Fetch pipeline to populate attachment title/content and metadata.
- Optional background job to refresh pending attachments.
- Expose a tool wrapper for attachment refresh (registered in PR-003B).

## User Stories

- As a user, I can paste a Gmail URL and see email context on the task.
- As a user, my OAuth tokens are stored securely and not logged.

## UX Notes (if applicable)

- Provide clear setup instructions when Gmail auth is missing.

## Technical Design

### Architecture

- Gmail provider service with methods: `normalize_url`, `fetch_message`,
  `cache_content`.
- Auth uses Google OAuth InstalledAppFlow with local browser callback.
- A refresh entrypoint (CLI or background job) triggers fetch per attachment.
- Tool wrapper integration is defined in PR-003B and calls the refresh entrypoint.

### Data Model / Migrations

- Store Gmail message metadata in `attachment.metadata` and content in
  `attachment.content`.

### API Contract

- No new public API required beyond attachment refresh endpoint/command.
- If adding API: `POST /api/v1/attachments/{id}/refresh` returns updated attachment.

### Background Jobs

- Optional background loop to process attachments with missing content.

### Security / Privacy

- Store OAuth credentials on disk with 0600 permissions.
- Do not log email bodies or tokens.

### Error Handling

- Map Gmail API errors (401/403/404/429) to user-facing messages.
- Fail fetch gracefully without deleting the attachment.

## Acceptance Criteria

### AC1: OAuth and Credential Persistence

**Success Criteria:**
- [ ] OAuth flow completes and tokens persist with secure permissions.

### AC2: URL Normalization and Fetch

**Success Criteria:**
- [ ] Gmail URLs normalize to stable references and fetch succeeds.

### AC3: Cache Attachment Content

**Success Criteria:**
- [ ] Attachment content includes subject/from/to/date/body excerpt.

## Test Plan

### Automated

- Unit tests for URL normalization and message parsing.
- Integration tests for token storage and refresh behavior (mocked HTTP).

### Manual

- Run OAuth setup, attach a Gmail URL, refresh, and verify cached content.

## Notes / Risks / Open Questions

- Gmail URL formats vary; expand normalization fixtures with real samples.
