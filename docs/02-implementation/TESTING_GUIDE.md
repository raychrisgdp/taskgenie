# Testing Guide

## Overview

This guide explains the testing strategy for the TaskGenie system, including unit tests, integration tests, and end-to-end (E2E) tests.

**Coverage Target:** >80%
**Frameworks:** Pytest (unit), HTTPX (integration), Playwright (E2E)

**Per-PR Test Plans:** See `docs/02-implementation/pr-specs/INDEX.md` (each PR mini-spec includes concrete scenarios).

---

## Testing Philosophy

### Unit Tests
- Fast feedback loop during development
- Test business logic in isolation
- Mock external dependencies (LLM, APIs, database)
- Run on every commit (pre-commit hooks)

### Integration Tests
- Validate API contracts (request/response schemas)
- Test database operations with real SQLite (in-memory)
- Test cross-service communication (Task → LLM → Chat)

### E2E Tests
- Validate critical user journeys
- Test the full system as a user would experience it
- Use browser automation (Playwright) or headless testing
- Run before each PR merge

---

## Per-PR Testing Requirements

Every Pull Request MUST include:

### Code Coverage
- [ ] New code has >80% unit test coverage
- [ ] Changed code maintains existing coverage
- [ ] Run `pytest --cov=backend/ --cov-report=html` to verify

### Unit Tests
- [ ] Test new functions/methods
- [ ] Test error handling (try/except blocks)
- [ ] Test edge cases (empty inputs, null values, boundary conditions)
- [ ] Mock external dependencies properly (LLM, HTTP clients)

### Integration Tests
- [ ] New API endpoints have integration tests
- [ ] Test success paths (happy paths)
- [ ] Test error paths (400, 404, 500 errors)
- [ ] Test authentication (if implemented)
- [ ] Test rate limiting behavior
- [ ] Test WebSocket/SSE streaming

### E2E Tests (Critical Journeys Only)
- [ ] Journey 1: Create task via chat
- [ ] Journey 2: Attach URL (auto-detection)
- [ ] Journey 3: Semantic search across tasks and attachments
- [ ] Journey 4: Notification triggers
- [ ] Journey 5: Complete task workflow

### Manual Testing Checklist
- [ ] Run interactive TUI and CLI commands manually (`tgenie`, `tgenie add`, `tgenie list`)
- [ ] Test Web UI in browser
- [ ] Test Docker Compose startup
- [ ] Verify chat streaming works
- [ ] Test notifications appear (if environment allows)

---

## Critical User Journeys

### Journey 1: Create Task via Chat

**Scenario:** User opens chat and asks AI to create a task.

**Steps:**
1. `tgenie` (opens interactive TUI; chat-first once PR-003 is implemented)
2. User types: `Add task "Review PR #123" for tomorrow`
3. LLM parses intent and calls `create_task`
4. Task saved to database
5. RAG service indexes task in ChromaDB
6. Response returned to user

**Tests:**
```python
# tests/test_journeys/test_create_task.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_task_via_chat():
    """Test creating a task through chat interface"""
    async with AsyncClient(app="http://localhost:8080") as client:
        # Start chat session
        response = await client.post("/api/v1/chat", json={
            "message": "Add task 'Review PR #123' for tomorrow"
        })

        # Verify chat response
        assert response.status_code == 200
        data = await response.aread_json()

        # Check for task creation action
        # This would be in suggested_actions or AI response
        # For integration test, we'd verify task was created

        # Verify task exists in DB
        get_response = await client.get(f"/api/v1/tasks/REVIEW_PR_ID")
        assert get_response.status_code == 200
        task_data = await get_response.aread_json()
        assert task_data["title"] == "Review PR #123"
        assert task_data["status"] == "pending"
```

---

### Journey 2: Auto-Attach URL

**Scenario:** User creates a task with a GitHub/Gmail URL. System should auto-detect and attach.

**Steps:**
1. `tgenie add "Review code" -d "Check https://github.com/owner/repo/pull/123"`
2. Link detection service parses URL from description
3. GitHub provider fetches PR content
4. Attachment created in database
5. RAG service indexes attachment content

**Tests:**
```python
# tests/test_journeys/test_auto_attach.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_auto_attach_github_url():
    """Test that URLs in task description trigger auto-attachment"""
    async with AsyncClient(app="http://localhost:8080") as client:
        # Create task with URL in description
        response = await client.post("/api/v1/tasks", json={
            "title": "Review code",
            "description": "Check https://github.com/owner/repo/pull/123"
        })

        task_id = (await response.aread_json())["id"]

        # Verify attachment was created
        attachments_response = await client.get(f"/api/v1/tasks/{task_id}/attachments")
        assert attachments_response.status_code == 200
        attachments = await attachments_response.aread_json()

        # Verify it's a GitHub attachment
        assert len(attachments) == 1
        assert attachments[0]["type"] == "github"
        assert attachments[0]["reference"] == "owner/repo/pull/123"
        assert "content" in attachments[0]  # Content was cached
```

---

### Journey 3: Semantic Search

**Scenario:** User searches for "authentication problems" across tasks and attachments.

**Steps:**
1. User types: `What was that authentication issue?` in chat
2. LLM generates query embedding
3. ChromaDB search returns relevant results
4. Results reranked by relevance score
5. Response formatted for user

**Tests:**
```python
# tests/test_journeys/test_semantic_search.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_semantic_search_across_tasks_and_attachments():
    """Test semantic search across tasks and attachments"""
    # Setup: Create a task and an attachment with "authentication" in content

    # Create test task
    async with AsyncClient(app="http://localhost:8080") as client:
        task_response = await client.post("/api/v1/tasks", json={
            "title": "Fix authentication bug",
            "description": "JWT token expiration handling"
        })
        task_id = (await task_response.aread_json())["id"]

        # Create attachment
        att_response = await client.post("/api/v1/attachments", json={
            "task_id": task_id,
            "type": "github",
            "reference": "https://github.com/owner/repo/pull/123"
        })

        # Semantic search query
        search_response = await client.get("/api/v1/search/semantic", params={
            "q": "authentication problems"
        })

        assert search_response.status_code == 200
        results = await search_response.aread_json()

        # Verify both task and attachment appear in results
        result_types = [r["type"] for r in results["results"]]
        assert "task" in result_types
        assert "attachment" in result_types

        # Verify results are sorted by relevance
        relevance_scores = [r["relevance"] for r in results["results"]]
        assert relevance_scores == sorted(relevance_scores, reverse=True)
```

---

### Journey 4: Notification Triggers

**Scenario:** Task created with ETA 24h in future. System should schedule and send notification.

**Steps:**
1. Task created with `eta: datetime.now() + timedelta(hours=24)`
2. Notification service creates notification record
3. Scheduler checks every 5 minutes
4. At 24h mark, notification sent
5. Desktop notification appears (if running locally)

**Tests:**
```python
# tests/test_journeys/test_notifications.py

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_notification_scheduled_and_sent():
    """Test that notification scheduler creates and sends notifications"""
    async with AsyncClient(app="http://localhost:8080") as client:
        # Create task due in 25 hours
        eta = datetime.utcnow() + timedelta(hours=25)
        task_response = await client.post("/api/v1/tasks", json={
            "title": "Task due tomorrow",
            "eta": eta.isoformat()
        })

        task_id = (await task_response.aread_json())["id"]

        # Check notification was scheduled
        # In real test, this would require waiting for scheduler to run
        # For integration test, verify notification record exists

        # Manually trigger notification (for testing)
        notify_response = await client.post(f"/api/v1/tasks/{task_id}/notify", json={})

        assert notify_response.status_code == 200

        # Verify notification record updated
        notifications_response = await client.get(f"/api/v1/tasks/{task_id}/notifications")
        assert notifications_response.status_code == 200
        notifications = await notifications_response.aread_json()

        # Verify last notification was sent
        sent_notifications = [n for n in notifications if n["status"] == "sent"]
        assert len(sent_notifications) >= 1
        assert sent_notifications[0]["type"] == "due_24h"
```

---

### Journey 5: Complete Task Workflow

**Scenario:** User creates a task, receives notification, clicks notification, and marks task done.

**Steps:**
1. Create task with ETA
2. Notification sent 24h before ETA
3. User clicks notification → opens task in Web UI
4. User marks task as done
5. Completion notification sent
6. Task status updated to "completed"

**Tests:**
```python
# tests/test_journeys/test_complete_workflow.py

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_full_task_lifecycle():
    """Test complete workflow from creation to completion"""
    async with AsyncClient(app="http://localhost:8080") as client:
        # Create task
        eta = datetime.utcnow() + timedelta(hours=2)  # Due in 2 hours
        create_response = await client.post("/api/v1/tasks", json={
            "title": "Test task",
            "eta": eta.isoformat()
        })
        task_id = (await create_response.aread_json())["id"]

        # Mark task as in progress (simulating user action)
        await client.patch(f"/api/v1/tasks/{task_id}", json={"status": "in_progress"})

        # Mark task as done
        done_response = await client.patch(f"/api/v1/tasks/{task_id}", json={"status": "completed"})
        assert done_response.status_code == 200

        # Verify final state
        final_response = await client.get(f"/api/v1/tasks/{task_id}")
        final_data = await final_response.aread_json()

        assert final_data["status"] == "completed"
        assert "updated_at" in final_data
```

---

## Unit Testing Best Practices

### Test Organization

**Avoid common pitfalls:**
- **Duplicate tests**: Check for duplicate test function names before adding new tests
- **Incomplete test functions**: Ensure all test functions have complete definitions (no broken `async` without `def`)
- **Test isolation**: Use `tmp_path` + `monkeypatch` to ensure tests don't interfere with each other
- **Import patterns**: When importing inside test functions (to avoid circular imports), add `# noqa: PLC0415`

**Example:**
```python
def test_config_load_toml_os_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _load_toml_config with OSError."""
    config_file = tmp_path / "config.toml"
    monkeypatch.setenv("TASKGENIE_CONFIG_FILE", str(config_file))

    # Intentional import inside function to avoid circular import
    from backend.config import _load_toml_config  # noqa: PLC0415

    with patch.object(Path, "open", side_effect=OSError("Permission denied")):
        config = _load_toml_config()
        assert config == {}
```

### Test Structure

```
tests/
├── unit/
│   ├── test_task_service.py
│   ├── test_llm_service.py
│   ├── test_rag_service.py
│   ├── test_notification_service.py
│   └── test_link_detection.py
├── integration/
│   ├── test_tasks_api.py
│   ├── test_chat_api.py
│   ├── test_attachments_api.py
│   └── test_search_api.py
├── journeys/
│   ├── test_create_task.py
│   ├── test_auto_attach.py
│   ├── test_semantic_search.py
│   ├── test_notifications.py
│   └── test_complete_workflow.py
└── conftest.py
```

### Fixtures

```python
# tests/conftest.py

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient

@pytest.fixture
async def db_session():
    """In-memory SQLite database for testing"""
    # Would use a test database instance
    pass

@pytest.fixture
async def authenticated_client():
    """HTTP client with test API key"""
    return AsyncClient(
        base_url="http://localhost:8080",
        headers={"Authorization": "Bearer test-api-key"}
    )

@pytest.fixture
def mock_llm_service():
    """Mock LLM service for tests"""
    # Would mock OpenRouter/OpenAI responses
    pass

@pytest.fixture
def mock_chromadb():
    """Mock ChromaDB for tests"""
    # Would use in-memory vector store
    pass
```

### Running Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage report
pytest --cov=backend/ --cov-report=html

# Run specific test file
pytest tests/unit/test_task_service.py -v

# Run only failed tests
pytest --lf

# Run tests matching pattern
pytest -k "test_create" -v
```

---

## Integration Testing

### API Testing with HTTPX

```python
# tests/integration/test_tasks_api.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_task_success():
    async with AsyncClient(app="http://localhost:8080") as client:
        response = await client.post("/api/v1/tasks", json={
            "title": "Test task",
            "description": "Integration test"
        })

        assert response.status_code == 201
        data = await response.aread_json()
        assert "id" in data
        assert data["title"] == "Test task"

@pytest.mark.asyncio
async def test_create_task_validation_error():
    async with AsyncClient(app="http://localhost:8080") as client:
        response = await client.post("/api/v1/tasks", json={
            # Missing required field
            "description": "Test task"
        })

        assert response.status_code == 422  # Unprocessable Entity
        data = await response.aread_json()
        assert "error" in data
```

### Database Integration Tests

```python
# tests/integration/test_database_operations.py

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def test_db():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    return Session()

def test_task_crud_operations(test_db):
    """Test full CRUD cycle on database"""
    session = test_db()

    # Create
    # (Your ORM create logic here)

    # Read
    # (Your ORM read logic here)

    # Update
    # (Your ORM update logic here)

    # Delete
    # (Your ORM delete logic here)

    session.close()
```

---

## E2E Testing with Playwright

```python
# tests/e2e/test_chat_interface.py

from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_chat_create_task_flow(browser_page):
    """Test creating a task through chat interface"""

    # Navigate to chat
    await page.goto("http://localhost:8080/")

    # Type message
    await page.fill('[data-testid="chat-input"]', "Add task 'Write documentation'")
    await page.click('[data-testid="send-button"]')

    # Wait for response
    await page.wait_for_selector('[data-testid="chat-response"]', timeout=5000)

    # Verify task was created
    response_text = await page.text_content('[data-testid="chat-response"]')
    assert "Write documentation" in response_text

@pytest.mark.asyncio
async def test_task_list_navigation(browser_page):
    """Test navigating task list and filtering"""

    await page.goto("http://localhost:8080/")
    await page.click('[data-testid="tasks-tab"]')

    # Wait for tasks to load
    await page.wait_for_selector('[data-testid="task-item"]', timeout=3000)

    # Verify filter works
    await page.click('[data-testid="filter-high-priority"]')

    # Verify filtered results
    high_priority_tasks = await page.all('[data-testid="task-item"][data-priority="high"]')
    assert len(high_priority_tasks) >= 0
```

---

## Coverage Requirements

### Minimum Coverage by Component

| Component | Minimum Coverage | Rationale |
|------------|-------------------|-----------|
| **Task Service** | 80% | Core business logic |
| **LLM Service** | 75% | External dependency, harder to test |
| **RAG Service** | 80% | Core search functionality |
| **Chat API** | 85% | Critical user interface |
| **Notification Service** | 75% | External dependency (plyer) |
| **Attachment API** | 80% | CRUD operations |
| **Link Detection** | 90% | Pure logic, easy to test |

### Overall Target: >80%

---

## Continuous Integration

### Pre-commit Hooks

```bash
# .pre-commit-config.yaml

repos:
  - repo: local
    hooks:
      - id: pytest
        name: Run unit tests
        entry: pytest tests/unit/
        language: system
        pass_files: ^backend/.*\.py$
        types: [python]

      - id: coverage
        name: Check coverage
        entry: pytest --cov=backend/ --cov-fail-under=80
        language: system
        pass_files: ^backend/.*\.py$
        types: [python]
```

### GitHub Actions CI

```yaml
# .github/workflows/test.yml

name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      - name: Run unit tests
        run: |
          pytest --cov=backend/ --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

---

## Performance Testing

### Load Testing

```python
# tests/performance/test_load.py

import pytest
import asyncio
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_chat_concurrent_requests():
    """Test that chat API handles multiple concurrent requests"""
    async with AsyncClient(app="http://localhost:8080") as client:

        # Send 10 concurrent requests
        tasks = [
            client.post("/api/v1/chat", json={"message": f"Message {i}"})
            for i in range(10)
        ]

        responses = await asyncio.gather(*tasks)

        # Verify all succeeded
        for response in responses:
            assert response.status_code in [200, 429]  # 429 for rate limit
```

---

## Testing Checklist for Each PR

Before submitting a PR, verify:

- [ ] All new code has unit tests
- [ ] Unit tests pass locally
- [ ] Integration tests added for new endpoints
- [ ] Manual testing completed (if applicable)
- [ ] Test coverage >80%
- [ ] No tests skipped without comment
- [ ] **Precommit passes**: `make precommit` (checks formatting, linting, type checking, docs validation)
- [ ] No duplicate test functions
- [ ] All test functions are complete (no broken definitions)
- [ ] Unused variables prefixed with `_` or removed

---

## Common Test Scenarios

### Error Scenarios
- Network timeout → System handles gracefully
- LLM rate limit → Falls back to basic search
- Database lock → Retry with exponential backoff
- Invalid input → Returns 400 with clear error message
- Unauthorized → Returns 401 with authentication instructions

### Edge Cases
- Empty task list → Returns empty array, not null
- Very long task titles → Handled correctly
- Special characters in titles → Properly escaped/encoded
- Duplicate task creation → Returns conflict error
- Invalid date format → Returns 400 with error details

### Security Tests
- SQL injection attempts → Parameterized queries used
- XSS in task titles → Sanitized before storage
- Unauthorized API access → Returns 403 Forbidden
- API key validation → Rejects invalid keys

---

## Troubleshooting

### Precommit Failures

**Issue:** `make precommit` fails with linting/type errors

**Common fixes:**
```bash
# 1. Format code
make format

# 2. Fix linting issues
ruff check --fix .

# 3. Fix type errors (add type: ignore comments if needed)
mypy backend/ tests/

# 4. Remove duplicate tests
# Check for duplicate test function names and remove duplicates

# 5. Fix incomplete test functions
# Ensure all test functions have complete definitions
```

**Common error patterns:**
- `PLC0415`: Import inside function → Add `# noqa: PLC0415` if intentional
- `F841`: Unused variable → Prefix with `_` or remove
- `F811`: Duplicate function → Remove duplicate
- `call-overload`: Type error with Path.open mock → Add `# type: ignore[call-overload]`

### Tests Failing Locally but Passing in CI

**Issue:** Database file exists from previous run

**Solution:**
```bash
# Clean test database before running tests
rm -f ~/.taskgenie/test_*.db
pytest tests/ -v
```

---

### Debug Mode

Enable debug output to see test execution:

```bash
# Run with verbose output
pytest -v -s

# Run with debug breakpoints
pytest --pdb
```

---

## Version History

| Version | Date | Changes |
|----------|-------|----------|
| 1.0 | 2025-01-29 | Initial testing guide |
