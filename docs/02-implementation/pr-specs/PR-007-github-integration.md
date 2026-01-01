# PR-007: GitHub Integration (Spec)

**Status:** Spec Only  
**Depends on:** PR-004  
**Last Reviewed:** 2025-12-29

## Goal

Given a GitHub Issue/PR URL attachment, fetch useful content and cache it locally.

## User Value

- GitHub-linked tasks become self-contained with key PR/issue details.
- Cached content becomes searchable via RAG later.

## References

- `docs/01-design/INTEGRATION_GUIDE.md`
- `docs/01-design/DESIGN_DATA.md`
- `docs/01-design/DESIGN_BACKGROUND_JOBS.md`

## Scope

### In

- URL recognition and normalization for issues and pull requests.
- Fetch title/body and key metadata.
- Cache content on the attachment with a refresh strategy.
- Optional `GITHUB_TOKEN` auth with rate-limit handling.

### Out

- Full comment ingestion or webhooks.

## Mini-Specs

- Provider that normalizes GitHub URLs to `github:<owner>/<repo>/<type>/<number>`.
- Fetch pipeline that stores title/body and metadata on the attachment.
- Token-based auth and unauthenticated mode with clear rate-limit messaging.
- Optional TTL to avoid refetching too often.
- Expose a tool wrapper for attachment refresh (registered in PR-003B).

## User Stories

- As a user, I can paste a GitHub URL and see key details in the task.
- As a user, I get a clear error if the repo is private or my token is invalid.

## UX Notes (if applicable)

- Show actionable errors for auth and rate limits.

## Technical Design

### Architecture

- GitHub provider service with `normalize_url`, `fetch_issue`, `fetch_pr`.
- Refresh entrypoint (CLI or background job) triggers fetch per attachment.
- Tool wrapper integration is defined in PR-003B and calls the refresh entrypoint.

### Data Model / Migrations

- Store GitHub metadata (state, author, repo, number, updated_at) in
  `attachment.metadata`.
- Store cached title/body in `attachment.title` and `attachment.content`.

### API Contract

- No new public API required beyond attachment refresh endpoint/command.
- If adding API: `POST /api/v1/attachments/{id}/refresh` returns updated attachment.

### Background Jobs

- Optional background loop to refresh stale attachments based on TTL.

### Security / Privacy

- Read `GITHUB_TOKEN` from env/config; never log token values.

### Error Handling

- Map 401/403/404/429 to actionable user messages.
- Unauthenticated mode works for public repos with lower rate limits.

## Acceptance Criteria

### AC1: URL Recognition and Normalization

**Success Criteria:**
- [ ] GitHub issue/PR URLs normalize to stable references.

### AC2: Fetch and Cache

**Success Criteria:**
- [ ] Attachment content includes title/body and key metadata.

### AC3: Auth and Rate Limits

**Success Criteria:**
- [ ] Authenticated and unauthenticated modes both function with clear errors.

## Test Plan

### Automated

- Unit tests for URL normalization (issues and PRs).
- Integration tests with mocked GitHub API responses and error mapping.

### Manual

- Attach a public PR URL and verify cached content.
- Set/unset `GITHUB_TOKEN` and verify rate-limit/error messaging.

## Notes / Risks / Open Questions

- Decide whether to include comments in a later PR to avoid excessive API calls.
