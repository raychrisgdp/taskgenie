# PR-004: Attachments + Link Detection (Spec)

**Status:** Spec Only  
**Depends on:** PR-002  
**Last Reviewed:** 2025-12-30

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

## Mini-Specs

- Data model:
  - `Attachment` schema + DB table aligned with `DESIGN_DATA.md`.
- API endpoints:
  - create/list/delete attachments under `/api/v1/...` (align `API_REFERENCE.md`).
- URL normalization + dedup:
  - normalize provider references (`github:...`, `gmail:...`, generic URLs).
  - prevent duplicates per `(task_id, normalized_reference)`.
- Link detection:
  - parse task title/description and auto-create attachments for supported URLs.
  - provider registry for `match_url` / `normalize` hooks.
- Tests:
  - manual attach, auto-detect, dedup, 404/409 behavior.

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

- Extract URL candidates from `title` and `description` on:
  - task create
  - task update (when title/description changes)
- **Parsing:** Start with a simple regex (e.g., `r"https?://\\S+"`), then:
  - trim common trailing punctuation (e.g., `)`, `]`, `.`, `,`)
  - normalize with `urllib.parse` (lowercase scheme/host, drop obvious tracking params if desired)
- **LinkDetectionService:**
  - Providers:
    - `GitHubProvider`: matches `github.com/(.*)/(.*)/(pull|issues)/(\d+)`
    - `GmailProvider`: matches `mail.google.com/mail/u/\d+/#(inbox|label|all)/(\w+)`
    - `GenericProvider`: matches any other valid URL
- **Deduplication:** Check if `reference` already exists for the given `task_id` before inserting.

### Attachment lifecycle

- Attachments are created immediately with reference URL.
- Cached content is optional at this stage (can be empty until integrations fetch it).

## Acceptance Criteria

- [ ] Users can manually attach a URL to a task.
- [ ] URLs in task description auto-create attachments.
- [ ] Attachments are listed with task and have stable IDs.
- [ ] Link detection correctly identifies GitHub, Gmail, and generic URLs.
- [ ] Deduplication prevents duplicate attachments for same normalized URL.

## Test Plan

### Automated

```python
# tests/test_api/test_attachments.py
import pytest
from httpx import AsyncClient
from backend.services.attachment_service import AttachmentType

class TestAddAttachment:
    """Tests for POST /api/v1/tasks/{id}/attachments"""

    @pytest.mark.asyncio
    async def test_add_github_attachment(self, client: AsyncClient, sample_task):
        """Add GitHub PR attachment."""
        response = await client.post(
            f"/api/v1/tasks/{sample_task.id}/attachments",
            json={
                "type": "github",
                "reference": "https://github.com/owner/repo/pull/123"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "github"

    @pytest.mark.asyncio
    async def test_add_gmail_attachment(self, client: AsyncClient, sample_task):
        """Add Gmail attachment."""
        response = await client.post(
            f"/api/v1/tasks/{sample_task.id}/attachments",
            json={
                "type": "gmail",
                "reference": "gmail:18e4f7a2b3c4d5e"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "gmail"

    @pytest.mark.asyncio
    async def test_add_generic_url_attachment(self, client: AsyncClient, sample_task):
        """Add generic URL attachment."""
        response = await client.post(
            f"/api/v1/tasks/{sample_task.id}/attachments",
            json={
                "type": "url",
                "reference": "https://example.com/docs"
            }
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_add_attachment_task_not_found(self, client: AsyncClient):
        """Return 404 when task doesn't exist."""
        response = await client.post(
            "/api/v1/tasks/nonexistent/attachments",
            json={"type": "url", "reference": "https://example.com"}
        )
        assert response.status_code == 404


class TestLinkDetection:
    """Tests for automatic link detection"""

    @pytest.mark.asyncio
    async def test_detect_github_pr_url(self, db_session):
        """Detect GitHub PR URL in task description."""
        from backend.services.link_detection import LinkDetectionService

        task = await create_task_with_desc(
            "Check https://github.com/owner/repo/pull/123 please"
        )

        detected = await LinkDetectionService.detect_and_create(db_session, task)
        assert len(detected) == 1
        assert detected[0]["type"] == "github"
        assert detected[0]["reference"] == "github:owner/repo/pull/123"

    @pytest.mark.asyncio
    async def test_detect_github_issue_url(self, db_session):
        """Detect GitHub Issue URL."""
        from backend.services.link_detection import LinkDetectionService

        task = await create_task_with_desc(
            "Issue at owner/repo#456"
        )

        detected = await LinkDetectionService.detect_and_create(db_session, task)
        assert len(detected) == 1
        assert detected[0]["type"] == "github"

    @pytest.mark.asyncio
    async def test_detect_gmail_url(self, db_session):
        """Detect Gmail URL."""
        from backend.services.link_detection import LinkDetectionService

        task = await create_task_with_desc(
            "Email https://mail.google.com/mail/u/0/#inbox/18e4f7a2b3c4d5e"
        )

        detected = await LinkDetectionService.detect_and_create(db_session, task)
        assert len(detected) == 1
        assert detected[0]["type"] == "gmail"


class TestDeduplication:
    """Tests for attachment deduplication"""

    @pytest.mark.asyncio
    async def test_same_url_no_duplicate(self, client: AsyncClient, sample_task, db_session):
        """Same URL doesn't create duplicate attachment."""
        from backend.services.link_detection import LinkDetectionService

        # First attachment
        await LinkDetectionService.create_attachment(
            db_session, sample_task.id, "github", "github:owner/repo/pull/123"
        )

        # Try same reference again
        response = await client.post(
            f"/api/v1/tasks/{sample_task.id}/attachments",
            json={"type": "github", "reference": "github:owner/repo/pull/123"}
        )
        assert response.status_code == 409  # Conflict

    @pytest.mark.asyncio
    async def test_normalized_url_no_duplicate(self, client: AsyncClient, sample_task, db_session):
        """Normalized URLs don't create duplicates."""
        from backend.services.link_detection import LinkDetectionService

        # Create with different param in URL
        await LinkDetectionService.create_attachment(
            db_session, sample_task.id, "github", "github:owner/repo/pull/123"
        )

        # Try with query param (normalized to same)
        response = await client.post(
            f"/api/v1/tasks/{sample_task.id}/attachments",
            json={"type": "github", "reference": "github:owner/repo/pull/123?foo=bar"}
        )
        assert response.status_code == 409  # Conflict
```

### Manual

1. Create task with `https://github.com/owner/repo/pull/123` in description.
2. Verify task details show 1 attachment entry.
3. Edit task and add a second URL; verify attachments list updates.

## Notes / Risks / Open Questions

- Decide canonical URL normalization rules early (strip tracking params? keep fragments?).
