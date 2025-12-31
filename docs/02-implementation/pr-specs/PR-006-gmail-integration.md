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

## Mini-Specs

- URL recognition + normalization:
  - detect Gmail message URLs and normalize to a stable reference key.
- OAuth + credential storage:
  - `tgenie config --gmail-auth` (or equivalent) to set up tokens.
  - store secrets under `~/.taskgenie/credentials/` with `0600` permissions.
- Fetch + cache:
  - fetch subject/from/date/body and store into `attachment.content`.
- Background fetch:
  - allow explicit refresh and/or background “pending fetch” processing.
- Tests:
  - URL parsing, auth error mapping, and fetch-to-cache pipeline (mocked HTTP).

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
- [ ] Email content is cached and viewable from task attachment.
- [ ] Credentials stored securely with file permissions (0600).
- [ ] Automated tests cover URL normalization + fetch/cache pipeline (see Test Plan).
- [ ] Manual smoke checklist completed (see Test Plan).

## Appendix: Implementation Sketch

### OAuth Flow Implementation

```python
# backend/services/gmail_service.py
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from pathlib import Path
import json

class GmailService:
    def __init__(self):
        self.credentials: Credentials | None = None
        self.SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
        self.CREDENTIALS_DIR = Path.home() / ".taskgenie" / "credentials"
        self.CLIENT_SECRET_PATH = self.CREDENTIALS_DIR / "gmail_client_secret.json"
        self.TOKEN_PATH = self.CREDENTIALS_DIR / "gmail_token.json"

    async def authenticate(self) -> bool:
        """Run OAuth flow for Gmail."""
        # Check for existing token
        if self.TOKEN_PATH.exists():
            self.credentials = Credentials.from_authorized_user_file(
                str(self.TOKEN_PATH), self.SCOPES
            )

            # Refresh if expired
            if self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
                self._save_token()
                return True

        # Run OAuth flow
        if not self.CLIENT_SECRET_PATH.exists():
            raise FileNotFoundError(
                f"Gmail client secret not found at {self.CLIENT_SECRET_PATH}. "
                "Download from Google Cloud Console."
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(self.CLIENT_SECRET_PATH), self.SCOPES
        )

        self.credentials = flow.run_local_server(
            port=0,
            prompt="consent",
            success_message="Authentication successful! You can close this tab."
        )

        self._save_token()
        return True

    def _save_token(self):
        """Save token to file with secure permissions."""
        self.TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Save token
        with open(self.TOKEN_PATH, "w") as f:
            f.write(self.credentials.to_json())

        # Set secure file permissions (owner read/write only)
        self.TOKEN_PATH.chmod(0o600)

    async def get_message(self, message_id: str) -> dict:
        """Fetch Gmail message by ID."""
        if not self.credentials or not self.credentials.valid:
            await self.authenticate()

        service = build("gmail", "v1", credentials=self.credentials)
        message = service.users().messages().get(
            userId="me",
            id=message_id,
            format="full"
        ).execute()

        return self._parse_message(message)

    def _parse_message(self, raw_message: dict) -> dict:
        """Parse Gmail message to structured data."""
        headers = {
            h["name"].lower(): h["value"]
            for h in raw_message.get("payload", {}).get("headers", [])
        }

        # Extract body
        payload = raw_message.get("payload", {})
        body = self._extract_body(payload)

        return {
            "id": raw_message["id"],
            "thread_id": raw_message["threadId"],
            "subject": headers.get("subject", ""),
            "from": headers.get("from", ""),
            "to": headers.get("to", ""),
            "date": headers.get("date", ""),
            "body": body,
            "snippet": raw_message.get("snippet", ""),
        }

    def _extract_body(self, payload: dict) -> str:
        """Extract body from message payload."""
        import base64

        # Try direct body first
        if "body" in payload and payload["body"].get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

        # Try multipart
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                    return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")

        return ""
```

## Test Plan

### Automated

```python
# tests/test_services/test_gmail_service.py
import pytest
from unittest.mock import MagicMock, patch
from backend.services.gmail_service import GmailService

class TestGmailOAuth:
    """Tests for Gmail OAuth flow"""

    @pytest.mark.asyncio
    async def test_authenticate_creates_token(self, tmp_path):
        """OAuth flow creates token file."""
        gmail = GmailService()

        # Mock OAuth flow
        mock_flow = MagicMock()
        mock_flow.run_local_server.return_value = MagicMock(
            to_json=lambda: '{"refresh_token": "test-refresh", "token": "test-token"}'
        )

        with patch("backend.services.gmail_service.InstalledAppFlow", return_value=mock_flow):
            await gmail.authenticate()

            # Verify token was saved
            assert gmail.TOKEN_PATH.exists()

            # Check file permissions
            import os
            assert os.stat(gmail.TOKEN_PATH).st_mode == 0o600

    @pytest.mark.asyncio
    async def test_authenticate_loads_existing_token(self, tmp_path):
        """Existing token is loaded and refreshed if needed."""
        gmail = GmailService()

        # Create valid token file
        gmail.TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(gmail.TOKEN_PATH, "w") as f:
            f.write('{"refresh_token": "valid", "token": "valid"}')

        # Load (should not run OAuth flow)
        mock_flow = MagicMock()
        with patch("backend.services.gmail_service.InstalledAppFlow", return_value=mock_flow):
            await gmail.authenticate()

            # Verify existing token was used
            mock_flow.run_local_server.assert_not_called()


class TestGmailMessageParsing:
    """Tests for Gmail message parsing"""

    def test_parse_simple_message(self):
        """Parse simple text message."""
        gmail = GmailService()
        raw = {
            "id": "msg-123",
            "threadId": "thread-456",
            "snippet": "Test message",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "sender@example.com"}
                ],
                "body": {"data": "SGVsbG8gV29ybGQ="}  # "Hello World"
            }
        }

        result = gmail._parse_message(raw)
        assert result["subject"] == "Test Subject"
        assert result["body"] == "Hello World"

    def test_parse_multipart_message(self):
        """Parse multipart message."""
        gmail = GmailService()
        raw = {
            "id": "msg-123",
            "payload": {
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": "TWVsbG8gV29ybGQ="}
                    }
                ]
            }
        }

        result = gmail._parse_message(raw)
        assert result["body"] == "Hello World"
```

### Manual

1. Run `tgenie config --gmail-auth` (or equivalent) and complete OAuth in browser.
2. Create task containing a Gmail URL.
3. Trigger fetch and verify attachment shows subject/from/date/body excerpt.

### Manual Test Checklist

- [ ] OAuth credentials are stored outside SQLite with `0600` permissions.
- [ ] Gmail URL normalization is stable across common Gmail URL variants.
- [ ] Fetch populates `attachment.content` and does not leak secrets into logs.
- [ ] Missing/expired credentials produce actionable errors and a re-auth path.
- [ ] Update `.env.example` to add `GMAIL_ENABLED`, `GMAIL_CREDENTIALS_PATH` variables.

### Run Commands

```bash
make test
# or
uv run pytest -v
```

## Notes / Risks / Open Questions

- Gmail URL formats vary; normalization rules should be tested against real examples.

---

## Skill Integration: integration-setup

### Gmail OAuth Setup Guide

This PR should follow **integration-setup** skill patterns:

**Step 1: Google Cloud Console**
1. Create project: `personal-todo-gmail`
2. Enable Gmail API (APIs & Services → Library)
3. Create OAuth credentials (Desktop app)
4. Configure OAuth consent screen (External, add test user email)
5. Download client_secret.json

**Step 2: Token Storage**
- Store tokens in `~/.taskgenie/credentials/gmail_token.json`
- Set file permissions: `0600` (owner read/write only)
- Never commit tokens to repository

**Step 3: CLI Authentication Command**
```bash
tgenie config --gmail-auth
```
Opens browser, captures authorization code, stores token.

**Environment Variables**
```bash
# .env (optional for development)
GMAIL_CLIENT_ID=your-client-id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your-client-secret
```

### Security Best Practices

| Practice | Implementation |
|----------|----------------|
| Minimum scopes | Only `gmail.readonly` |
| Token refresh | Auto-rotate on expiry |
| No secrets in logs | Mask tokens in debug output |
| Secure storage | File permissions 0600 |
| Never commit | Add `*.json` to `.gitignore` |

### Troubleshooting

**Error: `invalid_grant`**
- Delete `~/.taskgenie/credentials/gmail_token.json`
- Re-run `tgenie config --gmail-auth`
- Check if access was revoked in Google Account settings

**Error: `access_denied`**
- Add your email to OAuth consent screen test users
- Verify redirect URI matches configuration

**Error: `Failed to load credentials`**
- Check client_secret.json exists in correct location
- Verify file is valid JSON
- Ensure app has file read permissions

### Testing Patterns

**Mock Gmail Service**
```python
# Use unittest.mock for Gmail API calls
@pytest.fixture
def mock_gmail_service():
    mock = MagicMock()
    mock.get_message.return_value = {
        "id": "msg-123",
        "subject": "Test Email",
        "from": "sender@example.com",
        "body": "Email content",
    }
    return mock
```

**Test URL Parsing**
```python
# Test various Gmail URL formats
"https://mail.google.com/mail/u/0/#inbox/18e4f7a2b3c4d5e" → extract message ID
"mailto:?messageId=18e4f7a2b3c4d5e" → extract message ID
```

**Test OAuth Flow**
- Mock `InstalledAppFlow.run_local_server()`
- Verify token saved to correct path
- Check file permissions (0o600)

**Test Message Parsing**
- Simple message (plain text body)
- Multipart message (text/plain and text/html)
- Missing body (handle gracefully)

### Integration Test Coverage

| Scenario | Test Type |
|-----------|-----------|
| OAuth flow completes | Mock + manual |
| Token refreshes automatically | Mock |
| Message fetches correctly | Mock |
| URL normalization | Unit |
| Error handling (401, 403) | Mock |

**See Also**
- Skill doc: `.opencode/skill/integration-setup/`
- Gmail API: https://developers.google.com/gmail/api
