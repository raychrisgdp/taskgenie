# Integration Guide

This guide explains how to add new integrations to the Personal TODO system, following the Provider Protocol pattern.

---

## Integration Provider Interface

All integrations must implement the following protocol:

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class IntegrationProvider(ABC):
    """Base interface for all external service integrations"""

    @abstractmethod
    def match_url(self, url: str) -> bool:
        """
        Check if this provider handles the given URL.

        Returns:
            True if the provider can handle this URL
            False otherwise
        """
        pass

    @abstractmethod
    async def fetch_content(self, reference: str) -> str:
        """
        Fetch and return content from the external service.

        Args:
            reference: The identifier for the external resource
                (e.g., Gmail message ID, GitHub issue URL, Jira ticket ID)

        Returns:
            str: The content to be cached for RAG search
            Should be plain text for optimal vector embeddings

        Raises:
            Exception: If fetching fails (should be caught and handled)
        """
        pass

    @abstractmethod
    async def get_metadata(self, reference: str) -> Dict[str, Any]:
        """
        Extract structured metadata from the fetched content.

        Returns:
            dict: Key-value pairs of metadata (e.g., author, repo, labels)
        """
        pass

    def normalize_url(self, url: str) -> str:
        """
        Convert various URL formats to a canonical reference.

        Args:
            url: Any URL format (short links, web URLs, etc.)

        Returns:
            str: Canonical reference string for storage
        """
        pass
```

---

## Adding a New Integration: Step-by-Step

### Step 1: Create Provider Implementation

**File:** `backend/integrations/<integration_name>.py`

**Example: Jira Integration**

```python
from typing import Dict, Any
import re
from ..integration_provider import IntegrationProvider

class JiraProvider(IntegrationProvider):
    """Jira integration for fetching issue/PR content"""

    def __init__(self, api_url: str, username: str, api_token: str):
        self.api_url = api_url
        self.username = username
        self.api_token = api_token

    def match_url(self, url: str) -> bool:
        # Match: jira.atlassian.net, jira.company.com
        pattern = r'https?://[^/]+\.atlassian\.net'
        return bool(re.search(pattern, url))

    async def fetch_content(self, reference: str) -> str:
        # Reference format: PROJECT-KEY or just issue ID
        # Call Jira API to fetch issue details
        import aiohttp
        headers = {"Authorization": f"Bearer {self.api_token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_url}/rest/api/2/issue/{reference}",
                headers=headers
            ) as response:
                response.raise_for_status()
                data = await response.json()

                # Extract relevant fields for RAG
                fields = data.get("fields", {})
                description = self._get_description_field(fields)

                return f"Issue: {reference}\n\nSummary: {description}"

    async def get_metadata(self, reference: str) -> Dict[str, Any]:
        # Extract structured metadata
        import aiohttp
        headers = {"Authorization": f"Bearer {self.api_token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_url}/rest/api/2/issue/{reference}",
                headers=headers
            ) as response:
                response.raise_for_status()
                data = await response.json()

                return {
                    "integration_type": "jira",
                    "ticket_id": reference,
                    "status": data.get("fields", {}).get("status", {}).get("name"),
                    "priority": data.get("fields", {}).get("priority", {}).get("name"),
                    "assignee": data.get("fields", {}).get("assignee", {}).get("displayName"),
                    "created": data.get("fields", {}).get("created"),
                    "updated": data.get("fields", {}).get("updated")
                }

    def normalize_url(self, url: str) -> str:
        # Extract issue ID from URL
        # Example: https://jira.atlassian.net/browse/PROJ-123
        pattern = r'/browse/([A-Z]+-\d+)'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return url

    def _get_description_field(self, fields: Dict) -> str:
        # Helper to extract description from Jira's complex field structure
        description_field = fields.get("description")
        if description_field:
            return description_field.get("content", "") or ""
        return ""
```

---

### Step 2: Register Provider in Link Detection

**File:** `backend/services/link_detection.py`

```python
from backend.integrations.github import GitHubProvider
from backend.integrations.gmail import GmailProvider
from backend.integrations.jira import JiraProvider

# Registry of all available providers
PROVIDERS = [
    GitHubProvider(),
    GmailProvider(),
    JiraProvider(),
]

def detect_and_create_attachments(
    task_id: str,
    text: str
) -> List[dict]:
    """
    Parse text for URLs, match against providers, create attachments.

    Args:
        task_id: The task to attach URLs to
        text: Task title or description to scan

    Returns:
        List of created attachment records
    """
    attachments = []

    # Extract URLs using regex
    import re
    url_pattern = r'https?://[^\s<>"\s]'
    urls = re.findall(url_pattern, text)

    for url in urls:
        # Try each provider
        for provider in PROVIDERS:
            if provider.match_url(url):
                try:
                    # Normalize URL to reference
                    reference = provider.normalize_url(url)

                    # Fetch content
                    content = await provider.fetch_content(reference)
                    metadata = await provider.get_metadata(reference)

                    # Create attachment record
                    attachments.append({
                        "task_id": task_id,
                        "type": provider.__class__.__name__.lower(),  # github, gmail, jira
                        "reference": reference,
                        "title": metadata.get("title", url),
                        "content": content,
                        "metadata": metadata
                    })

                    # Only use first matching provider
                    break
                except Exception as e:
                    # Log error but continue with other URLs
                    print(f"Warning: Failed to fetch {url}: {e}")
                    continue

    return attachments
```

---

### Step 3: Add Attachment Type

**File:** `backend/schemas/attachment.py`

```python
class AttachmentType(str, Enum):
    GMAIL = "gmail"
    GITHUB = "github"
    URL = "url"
    DOC = "doc"
    JIRA = "jira"  # NEW - Add your integration type
    NOTION = "notion"  # Example future integration
    SLACK = "slack"  # Example future integration
```

---

### Step 4: Update RAG Service to Index Attachment Content

**File:** `backend/services/rag_service.py`

```python
async def index_attachment(attachment_id: str, content: str, metadata: dict):
    """
    Generate embedding and store attachment content in ChromaDB.

    Args:
        attachment_id: ID of the attachment
        content: Plain text content from provider
        metadata: Structured metadata from provider
    """
    from chromadb import AsyncClientDB

    # Create document text with metadata for better search
    document_text = f"Attachment Type: {metadata.get('integration_type')}\n\n"
    document_text += f"Title: {metadata.get('title')}\n\n"
    document_text += f"Content:\n{content}\n"

    # Include metadata in the document
    if 'assignee' in metadata:
        document_text += f"Assignee: {metadata['assignee']}\n"
    if 'priority' in metadata:
        document_text += f"Priority: {metadata['priority']}\n"

    # Generate embedding
    embedding = await embedding_model.embed(document_text)

    # Store in ChromaDB
    collection = await chromadb.get_collection("attachments")
    await collection.add(
        ids=[f"attachment-{attachment_id}"],
        documents=[document_text],
        embeddings=[embedding],
        metadatas={
            "type": "attachment",
            "attachment_id": attachment_id,
            **metadata  # Include all metadata for filtering
        }
    )
```

---

## Examples: Adding Popular Integrations

### Example 1: Notion Integration

```python
class NotionProvider(IntegrationProvider):
    """Notion integration for page and database content"""

    def __init__(self, integration_token: str):
        self.token = integration_token

    def match_url(self, url: str) -> bool:
        return "notion.so" in url or "notion.site" in url

    async def fetch_content(self, reference: str) -> str:
        # Notion API: Use internal integration token
        import httpx
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.notion.com/v1/blocks/{reference}",
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

            # Extract text content from blocks
            # Notion blocks are complex - extract text recursively
            text_content = extract_text_from_notion_blocks(data)
            return text_content

    async def get_metadata(self, reference: str) -> Dict[str, Any]:
        return {
            "integration_type": "notion",
            "page_id": reference,
            "last_edited": datetime.utcnow().isoformat()
        }
```

---

### Example 2: Slack Integration

```python
class SlackProvider(IntegrationProvider):
    """Slack integration for messages and threads"""

    def __init__(self, bot_token: str):
        self.token = bot_token

    def match_url(self, url: str) -> bool:
        # Match: https://<workspace>.slack.com/archives/...
        pattern = r'https?://[^/]+\.slack\.com/archives'
        return bool(re.search(pattern, url))

    async def fetch_content(self, reference: str) -> str:
        # Slack API: Use bot token
        import httpx
        headers = {"Authorization": f"Bearer {self.token}"}

        # Parse: C1234567890.123456789 (workspace timestamp, channel)
        import re
        match = re.match(r'([^/]+)/([^/]+)', reference)
        if not match:
            raise ValueError("Invalid Slack reference format")

        workspace, timestamp = match.groups()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://slack.com/api/conversations.info",
                headers=headers,
                params={"channel": timestamp}
            )
            response.raise_for_status()
            data = response.json()

            # Get message history
            messages = await get_channel_history(timestamp)
            return format_slack_messages(messages)

    async def get_metadata(self, reference: str) -> Dict[str, Any]:
        return {
            "integration_type": "slack",
            "channel_id": reference.split('.')[0],  # Extract channel
            "message_ts": reference.split('.')[1]
        }
```

---

### Example 3: Linear Integration

```python
class LinearProvider(IntegrationProvider):
    """Linear integration for issue tracking"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def match_url(self, url: str) -> bool:
        return "linear.app" in url or "linear.app" in url

    async def fetch_content(self, reference: str) -> str:
        import httpx
        headers = {"Authorization": f"{self.api_key}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.linear.app/graphql",
                headers=headers,
                json={
                    "query": f"""
                    query Issue {{
                        issue(id: "{reference}") {{
                            title
                            description
                            status
                            assignee {{
                                name
                            displayName
                            avatarUrl
                            id
                            email
                            organization {{
                                teamKey
                                name
                            }}
                        }}
                    }}
                    """
                }
            )
            response.raise_for_status()
            data = response.json()

            issue = data.get("data", {}).get("issue")

            # Format for RAG
            text = f"Issue: {issue.get('id')}\n"
            text += f"Title: {issue.get('title')}\n"
            text += f"Status: {issue.get('status', {}).get('name')}\n"
            text += f"Assignee: {issue.get('assignee', {}).get('name')}\n"
            text += f"\nDescription:\n{issue.get('description', '')}"

            return text

    async def get_metadata(self, reference: str) -> Dict[str, Any]:
        # This would be parsed from the GraphQL response
        return {"integration_type": "linear"}
```

---

## Configuration

Add integration configuration to `~/.taskgenie/config.toml`:

```toml
[gmail]
enabled = true
credentials_path = "~/.taskgenie/credentials.json"

[github]
enabled = true
token = "ghp_..."  # Personal access token or OAuth

[jira]  # NEW
enabled = false
api_url = "https://your-domain.atlassian.net"
username = "your-username"
api_token = "your-api-token"

[notion]  # NEW (future)
enabled = false
integration_token = "secret_..."

[slack]  # NEW (future)
enabled = false
bot_token = "xoxb-..."

[linear]  # NEW (future)
enabled = false
api_key = "lin_api_..."
```

---

## Testing

### Test Your Integration

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_jira_provider_match_url():
    provider = JiraProvider(api_url="https://test.atlassian.net", username="test", api_token="test")
    assert provider.match_url("https://test.atlassian.net/browse/PROJ-123") == True
    assert provider.match_url("https://github.com/owner/repo/pull/123") == False

@pytest.mark.asyncio
async def test_jira_provider_fetch():
    provider = JiraProvider(api_url="https://test.atlassian.net", username="test", api_token="test")

    # Mock the HTTP call in real tests
    content = await provider.fetch_content("PROJ-123")
    assert "Issue: PROJ-123" in content

@pytest.mark.asyncio
async def test_link_detection():
    from backend.services.link_detection import detect_and_create_attachments

    # Create a test task
    task_id = "test-task-123"
    text = "Check https://jira.atlassian.net/browse/PROJ-123 for details"

    attachments = await detect_and_create_attachments(task_id, text)
    assert len(attachments) == 1
    assert attachments[0]["type"] == "jira"
    assert attachments[0]["reference"] == "PROJ-123"
```

---

## Error Handling

All integrations should handle these error cases gracefully:

### 1. Authentication Errors

```python
try:
    content = await provider.fetch_content(reference)
except aiohttp.ClientResponseStatus as e:
    if e.status == 401:
        raise AuthenticationError("Invalid API token")
    elif e.status == 403:
        raise AuthenticationError("Insufficient permissions")
    else:
        raise IntegrationError(f"API error: {e.status}")
```

### 2. Rate Limiting

```python
from httpx import HTTPStatusError, TooManyRequests

try:
    content = await provider.fetch_content(reference)
except TooManyRequests:
    # Log warning and schedule retry
    logger.warning(f"Rate limited for {provider.__class__.__name__}")
    raise RetryableError("Rate limited. Please try again later.")
```

### 3. Network Errors

```python
import asyncio

try:
    content = await provider.fetch_content(reference)
except (aiohttp.ClientError, asyncio.TimeoutError) as e:
    logger.error(f"Network error: {e}")
    raise RetryableError(f"Network error: {str(e)}")
```

---

## Best Practices

### 1. Async I/O

All integration methods should be async to avoid blocking the main application:

```python
# ✅ Good: Async
async def fetch_content(self, reference: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text

# ❌ Bad: Sync
def fetch_content(self, reference: str) -> str:
    response = requests.get(url)  # Blocks event loop
    return response.text
```

### 2. Content Caching

Cache fetched content to avoid repeated API calls:

```python
from datetime import datetime, timedelta
from functools import lru_cache

class CachedIntegrationProvider:
    def __init__(self, ttl_hours: int = 1):
        self.ttl = timedelta(hours=ttl_hours)
        self._cache = {}

    async def fetch_content_cached(self, reference: str) -> str:
        cache_key = f"{self.__class__.__name__}:{reference}"

        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.utcnow() - cached["timestamp"] < self.ttl:
                return cached["content"]

        # Fetch and cache
        content = await self.fetch_content(reference)
        self._cache[cache_key] = {
            "content": content,
            "timestamp": datetime.utcnow()
        }
        return content
```

### 3. Minimal API Calls

Fetch only what's needed for RAG search:

```python
# ✅ Good: Fetch only issue description
async def fetch_for_rag(self, reference: str) -> str:
    issue = await self.api.get_issue(reference)
    return f"{issue['title']}\n{issue['description']}"

# ❌ Bad: Fetch entire thread with comments
async def fetch_all(self, reference: str) -> str:
    issue = await self.api.get_issue(reference)
    comments = await self.api.get_comments(reference)
    return format_full_thread(issue, comments)  # Wastes API quota
```

### 4. User-Agent

Set appropriate user-agent for API requests:

```python
import httpx

USER_AGENT = "Personal TODO/1.0 (+https://github.com/user/personal-todo)"

async def fetch_content(self, reference: str) -> str:
    headers = {
        "User-Agent": USER_AGENT,
        "Authorization": f"Bearer {self.token}"
    }

    async with httpx.AsyncClient(headers=headers) as client:
        response = await client.get(url)
        return response.text
```

---

## Security Considerations

### API Token Storage

- ✅ Store in `~/.taskgenie/config.toml` (file permissions: 600)
- ✅ Add `config.toml` to `.gitignore`
- ❌ Never commit tokens to repository
- ❌ Never log tokens in application logs

### OAuth Flows

For OAuth-based integrations (like Gmail):

```python
# OAuth credentials should be stored separately
OAUTH_CREDENTIALS_PATH = "~/.taskgenie/credentials.json"

# Credentials file should have restrictive permissions
# File: ~/.taskgenie/credentials.json
# Permissions: 600 (read/write for owner only)
```

### Content Sanitization

Before sending content to RAG, sanitize:

```python
def sanitize_for_rag(content: str) -> str:
    """
    Remove or sanitize content that shouldn't be embedded.

    Removes:
    - API keys/tokens
    - Email addresses (partial)
    - Phone numbers
    - SQL injection attempts

    Keeps:
    - Structured text
    - Code blocks (for technical integrations)
    """
    import re

    # Remove API keys
    content = re.sub(r'(sk-[a-zA-Z0-9]{20,})', '***REDACTED***', content)

    # Remove email addresses (keep first char)
    content = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\b', '***@***.***', content)

    # Remove phone numbers
    content = re.sub(r'\b\d{3}[-.\s]?\d{3}\b', '***PHONE***', content)

    return content
```

---

## Future Enhancements

### Webhook Support

Allow integrations to push updates back to the TODO system:

```python
class WebhookIntegrationProvider(IntegrationProvider):
    """
    Base class for integrations that support webhooks.

    Integrations would register a webhook endpoint, and external services
    would POST updates when relevant resources change.
    """

    @abstractmethod
    def register_webhook(self) -> str:
        """Register webhook URL and return webhook endpoint path"""
        pass

    @abstractmethod
    async def handle_webhook(self, payload: dict) -> Dict[str, Any]:
        """Process incoming webhook payload"""
        pass
```

### Real-time Sync

For chat systems like Slack or Discord:

```python
class RealtimeIntegrationProvider(IntegrationProvider):
    """
    Base class for real-time integrations.

    Instead of polling, these integrations would use WebSocket or SSE
    to receive real-time updates.
    """

    @abstractmethod
    async def subscribe_to_updates(self, reference: str):
        """Subscribe to real-time updates for a resource"""
        pass
```

---

## Troubleshooting

### Common Issues

**Issue:** "Integration not found" error
**Solution:** Check that provider is registered in `PROVIDERS` list in `link_detection.py`

**Issue:** "Rate limit exceeded" when fetching
**Solution:** Implement exponential backoff and cache content longer (increase TTL from 1h to 24h)

**Issue:** Content appears blank in RAG search
**Solution:** Check `fetch_content()` returns plain text (not HTML). Add HTML stripping logic.

**Issue:** Authentication fails repeatedly
**Solution:** Verify API token is valid, has correct permissions. Check provider documentation for required scopes.

---

## Version History

| Version | Date | Changes |
|----------|-------|----------|
| 1.0 | 2025-01-29 | Initial integration guide with Provider Protocol |
