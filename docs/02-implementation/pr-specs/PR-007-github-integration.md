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

## Mini-Specs

- URL recognition + normalization:
  - issues and pull requests (public + private).
- Fetch + cache:
  - title/body + key metadata cached into the attachment record.
  - TTL/refresh strategy to avoid excessive refetching.
- Auth + rate limits:
  - support `GITHUB_TOKEN` (PAT) and unauthenticated mode.
  - map 401/403/404/429 to actionable user messages.
- Tests:
  - normalize URLs; mocked GitHub API responses for success + error cases.

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
- [ ] Content is fetched and cached in attachment record.
- [ ] Errors are actionable (401/403/404/429 show clear messages).
- [ ] Unauthenticated mode works with public repos.
- [ ] PAT authentication uses token for higher rate limits.
- [ ] Automated tests cover URL parsing + error mapping (see Test Plan).
- [ ] Manual smoke checklist completed (see Test Plan).

## Appendix: Implementation Sketch

### Provider Implementation

```python
# backend/services/github_service.py
import httpx
import re
from dataclasses import dataclass
from backend.config import settings

@dataclass
class GitHubPR:
    """GitHub Pull Request data."""
    number: int
    title: str
    state: str
    author: str
    url: str
    body: str
    additions: int
    deletions: int
    labels: list[str]
    created_at: str
    updated_at: str

@dataclass
class GitHubIssue:
    """GitHub Issue data."""
    number: int
    title: str
    state: str
    author: str
    url: str
    body: str
    labels: list[str]
    created_at: str
    updated_at: str


class GitHubService:
    """GitHub API service wrapper."""

    API_BASE = "https://api.github.com"

    def __init__(self, token: str | None = None):
        self.token = token or settings.github_token
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy-initialize async HTTP client."""
        if self._client is None:
            headers = {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            self._client = httpx.AsyncClient(
                base_url=self.API_BASE,
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_pull_request(
        self, owner: str, repo: str, number: int
    ) -> GitHubPR:
        """Fetch pull request details."""
        response = await self.client.get(f"/repos/{owner}/{repo}/pulls/{number}")
        self._handle_errors(response)
        data = response.json()

        return GitHubPR(
            number=data["number"],
            title=data["title"],
            state=data["state"],
            author=data["user"]["login"],
            url=data["html_url"],
            body=data.get("body") or "",
            additions=data.get("additions", 0),
            deletions=data.get("deletions", 0),
            labels=[l["name"] for l in data.get("labels", [])],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    async def get_issue(self, owner: str, repo: str, number: int) -> GitHubIssue:
        """Fetch issue details."""
        response = await self.client.get(f"/repos/{owner}/{repo}/issues/{number}")
        self._handle_errors(response)
        data = response.json()

        return GitHubIssue(
            number=data["number"],
            title=data["title"],
            state=data["state"],
            author=data["user"]["login"],
            url=data["html_url"],
            body=data.get("body") or "",
            labels=[l["name"] for l in data.get("labels", [])],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    @staticmethod
    def parse_github_url(url: str) -> tuple[str, str, str, int]:
        """
        Parse GitHub URL to extract owner, repo, type, and number.

        Returns: (owner, repo, type, number)
        type is 'pull' or 'issues'
        """
        patterns = [
            r"github\.com/([^/]+)/([^/]+)/(pull|issues)/(\d+)",
            r"^([^/]+)/([^/]+)/(pull|issues)/(\d+)$",
            r"^([^/]+)/([^/]+)#(\d+)$",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                groups = match.groups()
                if len(groups) == 4:
                    return groups[0], groups[1], groups[2], int(groups[3])
                elif len(groups) == 3:
                    return groups[0], groups[1], "issues", int(groups[2])

        raise ValueError(f"Invalid GitHub URL: {url}")

    def _handle_errors(self, response: httpx.Response):
        """Map GitHub API errors to actionable messages."""
        if response.status_code == 401:
            raise ValueError("Invalid GitHub token. Configure GITHUB_TOKEN.")
        elif response.status_code == 403:
            raise ValueError("Forbidden. Check repository access permissions.")
        elif response.status_code == 404:
            raise ValueError("Repository or resource not found.")
        elif response.status_code == 429:
            raise ValueError("Rate limit exceeded. Wait before retrying.")

        response.raise_for_status()
```

## Test Plan

### Automated

```python
# tests/test_services/test_github_service.py
import pytest
from unittest.mock import AsyncMock, patch
import httpx
from backend.services.github_service import GitHubService, GitHubPR

class TestGitHubService:
    """Tests for GitHub API integration"""

    @pytest.mark.asyncio
    async def test_get_pull_request_success(self):
        """Fetch PR details successfully."""
        service = GitHubService(token="test-token")
        mock_client = AsyncMock()

        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "number": 123,
            "title": "Fix authentication bug",
            "state": "open",
            "user": {"login": "developer"},
            "html_url": "https://github.com/owner/repo/pull/123",
            "body": "This PR fixes that issue",
            "additions": 50,
            "deletions": 10,
            "labels": [{"name": "bug"}],
            "created_at": "2025-01-10T10:00:00Z",
            "updated_at": "2025-01-12T15:30:00Z",
        }
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        service._client = mock_client
        pr = await service.get_pull_request("owner", "repo", 123)

        assert pr.number == 123
        assert pr.title == "Fix authentication bug"
        assert "bug" in pr.labels
        mock_client.get.assert_called_once_with("/repos/owner/repo/pulls/123")

    @pytest.mark.asyncio
    async def test_get_issue_success(self):
        """Fetch issue details successfully."""
        service = GitHubService(token="test-token")
        mock_client = AsyncMock()

        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "number": 456,
            "title": "Add new feature",
            "state": "open",
            "user": {"login": "developer"},
            "html_url": "https://github.com/owner/repo/issues/456",
            "labels": [{"name": "enhancement"}],
        }
        mock_response.status_code = 200
        mock_client.get = AsyncMock(return_value=mock_response)
        service._client = mock_client

        issue = await service.get_issue("owner", "repo", 456)
        assert issue.number == 456

    def test_parse_github_url_full(self):
        """Parse full GitHub URL."""
        owner, repo, type_, num = GitHubService.parse_github_url(
            "https://github.com/owner/repo/pull/123"
        )
        assert owner == "owner"
        assert repo == "repo"
        assert type_ == "pull"
        assert num == 123

    def test_parse_github_url_shorthand(self):
        """Parse shorthand owner/repo#123 format."""
        owner, repo, type_, num = GitHubService.parse_github_url("owner/repo#456")
        assert owner == "owner"
        assert repo == "repo"
        assert type_ == "issues"
        assert num == 456

    def test_parse_github_url_invalid(self):
        """Parse invalid URL raises error."""
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            GitHubService.parse_github_url("not-a-valid-url")
```

### Manual

1. Create a task with a GitHub PR URL in its description (auto-detect should attach it via PR-004).
2. Trigger attachment fetch (explicit command or background fetch).
3. Verify attachment shows title + body summary in task detail.

### Manual Test Checklist

- [ ] Works unauthenticated for public repos (within rate limits).
- [ ] With `GITHUB_TOKEN`, fetch succeeds for private repos that token can access.
- [ ] 401/403/404/429 map to actionable messages (token invalid, private repo, not found, rate limit).
- [ ] Cached content is stable and does not refetch excessively (TTL behavior).
- [ ] Update `.env.example` to add `GITHUB_TOKEN`, `GITHUB_USERNAME` variables.

### Run Commands

```bash
make test
# or
uv run pytest -v
```

## Notes / Risks / Open Questions

- Decide whether to include comments later; MVP should keep API calls minimal.

---

## Skill Integration: integration-setup

### GitHub Authentication Setup Guide

This PR should follow **integration-setup** skill patterns:

**Token Generation**
```bash
# Option A: Fine-Grained PAT (Recommended)
1. Go to https://github.com/settings/tokens?type=beta
2. Click "Generate new token"
3. Name: `personal-todo-cli`
4. Expiration: 90 days (recommended)
5. Repository access: Select specific repositories
6. Permissions:
   - Repository permissions:
     - Issues: Read
     - Pull requests: Read
     - Contents: Read (for file references)
   - Account permissions: None needed
7. Copy token (shown only once)

# Option B: Classic PAT
1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. Scopes: `repo`, `read:user`
4. Copy token (shown only once)
```

**Configuration**
```bash
# .env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Config file
# ~/.taskgenie/config.toml
[github]
token = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### Security Best Practices

| Practice | Implementation |
|----------|----------------|
| Fine-grained tokens | Prefer over classic PATs |
| Repository-scoped | Limit to specific repos |
| Short expiration | Set 90-day max expiration |
| Rotate regularly | Regenerate every 90 days |
| Never log tokens | Mask in debug output |
| Never commit | Add to `.gitignore` |

### Troubleshooting

**Error: `401 Bad credentials`**
```
Error: 401 Client Error: Bad credentials
```
**Solutions:**
1. Regenerate token at https://github.com/settings/tokens
2. Update `.env` with new token
3. Verify token hasn't been revoked

**Error: `403 Forbidden`**
```
Error: 403 Client Error: Forbidden
```
**Solutions:**
1. Check repository permissions (read access required)
2. Verify repo is accessible (private vs public)
3. Check token scopes (needs `repo` for private repos)

**Error: `404 Not Found`**
```
Error: 404 Client Error: Not Found
```
**Solutions:**
1. Verify repository URL is correct
2. Check if repo exists
3. Verify issue/PR number is valid

**Error: `403 Rate limit exceeded`**
```
Error: 403 API rate limit exceeded
```
**Solutions:**
1. Use authenticated requests (higher limits)
2. Implement caching for repeated requests
3. Check `X-RateLimit-Reset` header for reset time
4. Wait before retrying (respect Retry-After header)

### Testing Patterns

**Mock GitHub Service**
```python
# tests/test_services/test_github_service.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

@pytest.fixture
def mock_pr_response():
    """Sample GitHub PR response."""
    return {
        "number": 123,
        "title": "Fix authentication bug",
        "state": "open",
        "user": {"login": "developer"},
        "html_url": "https://github.com/owner/repo/pull/123",
        "body": "This PR fixes that issue",
        "additions": 50,
        "deletions": 10,
        "labels": [{"name": "bug"}],
        "created_at": "2025-01-10T10:00:00Z",
        "updated_at": "2025-01-12T15:30:00Z",
    }

@pytest.fixture
def mock_github_client(mock_pr_response):
    """Mock HTTPX client for GitHub."""
    mock_response = AsyncMock()
    mock_response.json.return_value = mock_pr_response
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get = AsyncMock(return_value=mock_response)
    return mock_client

class TestGitHubService:
    @pytest.mark.asyncio
    async def test_get_pull_request(self, mock_github_client, mock_pr_response):
        """Test fetching PR details."""
        from backend.services.github_service import GitHubService

        service = GitHubService(token="test-token")
        service._client = mock_github_client

        pr = await service.get_pull_request("owner", "repo", 123)

        assert pr.number == 123
        assert pr.title == "Fix authentication bug"
        assert "bug" in pr.labels
        mock_github_client.get.assert_called_once_with("/repos/owner/repo/pulls/123")

    @pytest.mark.asyncio
    async def test_get_issue(self):
        """Test fetching issue details."""
        from backend.services.github_service import GitHubService

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "number": 456,
            "title": "Add new feature",
            "state": "open",
            "user": {"login": "developer"},
            "html_url": "https://github.com/owner/repo/issues/456",
            "labels": [{"name": "enhancement"}],
        }
        mock_response.status_code = 200

        service = GitHubService(token="test-token")
        service._client = AsyncMock()
        service._client.get = AsyncMock(return_value=mock_response)

        issue = await service.get_issue("owner", "repo", 456)

        assert issue.number == 456
        assert issue.state == "open"

    @pytest.mark.asyncio
    async def test_parse_github_url_full(self):
        """Test parsing full GitHub URL."""
        from backend.services.github_service import GitHubService

        owner, repo, type_, num = GitHubService.parse_github_url(
            "https://github.com/owner/repo/pull/123"
        )
        assert owner == "owner"
        assert repo == "repo"
        assert type_ == "pull"
        assert num == 123

    @pytest.mark.asyncio
    async def test_parse_github_url_shorthand(self):
        """Test parsing shorthand owner/repo#123 format."""
        from backend.services.github_service import GitHubService

        owner, repo, type_, num = GitHubService.parse_github_url("owner/repo#456")

        assert owner == "owner"
        assert repo == "repo"
        assert type_ == "issues"
        assert num == 456

    @pytest.mark.asyncio
    async def test_parse_github_url_invalid(self):
        """Test parsing invalid URL raises error."""
        from backend.services.github_service import GitHubService

        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            GitHubService.parse_github_url("not-a-valid-url")

    @pytest.mark.asyncio
    async def test_error_401(self):
        """Test 401 Unauthorized error."""
        from httpx import HTTPStatusError

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Bad credentials"}
        mock_response.raise_for_status = MagicMock(
            side_effect=HTTPStatusError("Bad credentials", request=None, response=mock_response)
        )

        mock_client.get = AsyncMock(return_value=mock_response)
        service = GitHubService(token="test-token")
        service._client = mock_client

        with pytest.raises(HTTPStatusError, match="Bad credentials"):
            await service.get_pull_request("owner", "repo", 123)

    @pytest.mark.asyncio
    async def test_error_429_rate_limit(self):
        """Test 429 rate limit error."""
        from httpx import HTTPStatusError

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"message": "API rate limit exceeded"}
        mock_response.headers = {"X-RateLimit-Reset": "1234567890"}

        mock_response.raise_for_status = MagicMock(
            side_effect=HTTPStatusError("Rate limit exceeded", request=None, response=mock_response)
        )

        mock_client.get = AsyncMock(return_value=mock_response)
        service = GitHubService(token="test-token")
        service._client = mock_client

        with pytest.raises(HTTPStatusError, match="Rate limit exceeded"):
            await service.get_pull_request("owner", "repo", 123)
```

### Integration Test Coverage

| Scenario | Test Type |
|-----------|-----------|
| Fetch PR/Issue | Mock API response |
| Parse GitHub URLs | Unit test |
| Handle 401/403/404/429 | Mock error responses |
| Private repo access | Mock with authentication error |

**See Also**
- Skill doc: `.opencode/skill/integration-setup/`
- GitHub REST API: https://docs.github.com/en/rest
