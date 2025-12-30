# PR-006: Gmail Integration (Spec)

**Status:** Spec Only  
**Depends on:** PR-004  
**Last Reviewed:** 2025-12-29

## Goal

Given a Gmail URL attached to a task, authenticate via OAuth and fetch the email content, then cache it locally as attachment content.

## User Value

- Email-linked tasks keep the important context without re-opening Gmail.
- Cached email content can later be searched via RAG (PR-005).

## Scope

### In

- Parse Gmail URLs to a stable reference (message id / thread id as appropriate).
- OAuth flow (local machine):
  - open browser for consent
  - store credentials securely on disk
- Fetch:
  - subject
  - from/to
  - date
  - body (plain text preferred; HTML optional)
- Cache fetched content into the attachment record.

### Out

- Two-way sync (labeling, replying, etc.).
- Bulk email ingestion.

## References

- `docs/01-design/INTEGRATION_GUIDE.md` (provider pattern + security)
- `docs/01-design/DESIGN_DATA.md` (attachment cache fields)
- `docs/01-design/DESIGN_BACKGROUND_JOBS.md` (fetch jobs without a queue)

## User Stories

- As a user, I can paste a Gmail URL into a task and see key email context in the attachment.
- As a user, the system handles OAuth securely and doesn’t leak email content into logs.

## Technical Design

### URL-first normalization

- Accept Gmail URLs as the primary input.
- Normalize to a stable identifier (message id and/or thread id) stored in `attachment.reference`.

### OAuth + credential storage

- OAuth flow opens the browser and stores credentials on disk with strict permissions.
- Do not store OAuth secrets inside the main SQLite DB.

### Fetch + cache

- Fetch minimal useful fields (subject, from/to, date, text body).
- Store formatted content into `attachment.content` for later viewing/searching.

### Background fetch

- Fetch can be initiated:
  - explicitly (e.g., “refresh attachment” action), and/or
  - as a background job that processes “pending fetch” attachments.

## Acceptance Criteria

- [ ] OAuth flow works and credentials persist.
- [ ] Gmail URL is normalized and fetch succeeds.
- [ ] Email content is cached and viewable from the task attachment.

## Test Plan

### Automated

- Unit: URL parsing/normalization.
- Integration:
  - mock Gmail API client calls (no network) and verify content formatting/caching.

### Manual

1. Run `tgenie config --gmail-auth` (or equivalent) and complete OAuth in browser.
2. Create task containing a Gmail URL.
3. Trigger fetch and verify attachment shows subject/from/date/body excerpt.

## Notes / Risks / Open Questions

- Gmail URL formats vary; normalization rules should be tested against real examples.
