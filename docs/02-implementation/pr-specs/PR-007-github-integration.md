# PR-007: GitHub Integration (Spec)

**Status:** Spec Only  
**Depends on:** PR-004  
**Last Reviewed:** 2025-12-29

## Goal

Given a GitHub Issue/PR URL attached to a task, fetch the useful content and cache it locally as attachment content.

## User Value

- Tasks that reference GitHub become “self-contained”: the user can see key PR/Issue details without context switching.
- Cached content becomes searchable later (RAG is layered on in PR-005).

## Scope

### In

- Recognize GitHub URLs (issue, pull request).
- Fetch:
  - title
  - description/body
  - key metadata (state, author, repo, number, updated_at)
- Cache fetched content into the attachment record.
- Auth:
  - support `GITHUB_TOKEN` (PAT) for higher rate limits
  - handle unauthenticated mode with stricter limits

### Out

- Full thread/comment ingestion (future / optional).
- Webhooks (future).

## References

- `docs/01-design/INTEGRATION_GUIDE.md` (provider pattern + security)
- `docs/01-design/DESIGN_DATA.md` (attachment cache fields)
- `docs/01-design/DESIGN_BACKGROUND_JOBS.md` (fetch jobs without a queue)

## User Stories

- As a user, I can paste a GitHub PR/Issue URL and see the important details in my task.
- As a user, I get a clear error if the repo is private or my token is invalid.

## Technical Design

### Provider implementation

- Implement a GitHub provider with:
  - `match_url()`, `normalize()`
  - `fetch_content()` returning a concise text payload
  - `metadata()` returning structured fields (repo, number, state, updated_at)

### Fetch + cache

- Cache:
  - `attachment.title` from PR/Issue title
  - `attachment.content` from body + a short metadata header
- Avoid refetching too frequently (cache TTL).

### Auth + rate limits

- Support `GITHUB_TOKEN` (PAT) and graceful unauthenticated mode.
- Map 401/403/404/429 to actionable user messages.

## Acceptance Criteria

- [ ] GitHub PR/Issue URL is recognized and normalized.
- [ ] Content is fetched and cached in the attachment record.
- [ ] Errors are actionable (401/403/404/429 show clear messages).

## Test Plan

### Automated

- Unit: URL parsing/normalization.
- Unit: response → cached content formatting.
- Integration:
  - mock GitHub API responses for PR and Issue endpoints
  - verify caching, rate limit handling, and retries/backoff behavior (if implemented)

### Manual

1. Create a task with a GitHub PR URL in its description (auto-detect should attach it via PR-004).
2. Trigger attachment fetch (explicit command or background fetch).
3. Verify attachment shows title + body summary in task detail.

## Notes / Risks / Open Questions

- Decide whether to include comments later; MVP should keep API calls minimal.
