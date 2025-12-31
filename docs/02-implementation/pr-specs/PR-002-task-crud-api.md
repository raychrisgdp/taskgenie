# PR-002: Task CRUD API (Spec)

**Status:** Spec Only  
**Depends on:** PR-001  
**Last Reviewed:** 2025-12-30

## Goal

Provide the minimal API surface to create, read, update, and delete tasks (plus basic filtering/pagination), so UIs can ship early.

## User Value

- Enables the first usable UI (TUI) quickly.
- Establishes a stable contract for future features (attachments, notifications, chat actions).

## Scope

### In

- REST endpoints for tasks:
  - create (`POST /api/v1/tasks`)
  - list (`GET /api/v1/tasks?status=&priority=&due_before=&due_after=&limit=&offset=`)
  - get by id (`GET /api/v1/tasks/{id}`)
  - update (`PATCH /api/v1/tasks/{id}`)
  - delete (`DELETE /api/v1/tasks/{id}`)
- Validation rules (required title, enum validation, timestamps).
- Consistent error format for 400/404/500.

### Out

- Attachments (PR-004).
- Semantic search (PR-005).
- Authentication/multi-user (future).

## Mini-Specs

- API routes:
  - `POST /api/v1/tasks`
  - `GET /api/v1/tasks` (filters + pagination)
  - `GET /api/v1/tasks/{id}`
  - `PATCH /api/v1/tasks/{id}`
  - `DELETE /api/v1/tasks/{id}`
- Validation:
  - `title` required; enums validated; timestamps server-generated.
- Error format:
  - 404 uses `{"error": "...", "code": "TASK_NOT_FOUND"}` (align `API_REFERENCE.md`).
- OpenAPI:
  - Endpoints appear in `/docs` with correct schemas and examples.
- Tests:
  - CRUD happy path + validation errors + list filters/pagination.

## References

- `docs/01-design/DESIGN_DATA.md` (task schema + relationships)
- `docs/01-design/API_REFERENCE.md` (endpoint examples)
- `docs/01-design/DESIGN_CLI.md` (commands that will rely on this API)

## User Stories

- As a user, I can create tasks and see them appear in my task list.
- As a user, I can update task status/priority/ETA and see it reflected everywhere.
- As a user, I can filter tasks by status/priority/due window.

## Technical Design

### Data model (SQLAlchemy)

- `Task` model in `backend/models/task.py`:
  - `id`: UUID (stored as `VARCHAR(36)` / string)
  - `title`: `VARCHAR(255) NOT NULL`
  - `description`: `TEXT NULL`
  - `status`: `VARCHAR(20) NOT NULL` (`pending|in_progress|completed`)
  - `priority`: `VARCHAR(20) NOT NULL` (`low|medium|high|critical`)
  - `eta`: `DATETIME NULL`
  - `created_at`, `updated_at`: `DATETIME NOT NULL`
  - `tags`: `JSON NULL`
  - `metadata`: `JSON NULL`
- Index: `(status, eta)` for common “what’s due?” queries.

### API schemas (Pydantic)

- Use the types in `backend/schemas/task.py`:
  - `TaskCreate`, `TaskUpdate`, `TaskResponse`
  - `TaskStatus` / `TaskPriority` enums validated at the API boundary
  - `TaskListResponse`: `{"tasks": [...], "total": 42, "page": 1, "page_size": 50}`

### API contract

- `POST /api/v1/tasks` → 201 Created
- `GET /api/v1/tasks` → 200 OK
  - Defaults: `limit=50`, `offset=0`
- `GET /api/v1/tasks/{id}` → 200 OK
- `PATCH /api/v1/tasks/{id}` → 200 OK
- `DELETE /api/v1/tasks/{id}` → 204 No Content

### Validation + transitions

- Validate enums at the API boundary.
- Status transitions can be permissive in MVP; tighten later if needed.

### Error format

- Standardize errors:
  - `{"error": "...", "code": "..."}`

## Acceptance Criteria

- [ ] All CRUD endpoints exist under `/api/v1/tasks` and match `docs/01-design/API_REFERENCE.md`.
- [ ] Validation rejects empty title and invalid enums.
- [ ] List supports `status`, `priority`, `due_before`, `due_after`, `limit`, `offset`.
- [ ] 404s return the standard error shape and code.
- [ ] OpenAPI docs render the endpoints + schemas.
- [ ] Automated tests cover CRUD + filters + validation (see Test Plan).
- [ ] Manual smoke checklist completed (see Test Plan).

## Test Plan

### Automated

```python
# tests/test_api/test_tasks_crud.py
import pytest
from httpx import AsyncClient

class TestTasksCRUD:
    """Core CRUD scenarios for /api/v1/tasks."""

    @pytest.mark.asyncio
    async def test_create_list_get_update_delete(self, client: AsyncClient):
        create_resp = await client.post("/api/v1/tasks", json={"title": "Buy groceries"})
        assert create_resp.status_code == 201

        task = create_resp.json()
        task_id = task["id"]
        assert task["title"] == "Buy groceries"
        assert task["status"] == "pending"
        assert task["priority"] == "medium"

        list_resp = await client.get("/api/v1/tasks", params={"limit": 50, "offset": 0})
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert any(t["id"] == task_id for t in list_data["tasks"])
        assert isinstance(list_data["total"], int)

        get_resp = await client.get(f"/api/v1/tasks/{task_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == task_id

        patch_resp = await client.patch(f"/api/v1/tasks/{task_id}", json={"status": "in_progress"})
        assert patch_resp.status_code == 200
        assert patch_resp.json()["status"] == "in_progress"

        del_resp = await client.delete(f"/api/v1/tasks/{task_id}")
        assert del_resp.status_code == 204

        missing_resp = await client.get(f"/api/v1/tasks/{task_id}")
        assert missing_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_validation_errors(self, client: AsyncClient):
        response = await client.post("/api/v1/tasks", json={"title": ""})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_filters(self, client: AsyncClient):
        await client.post("/api/v1/tasks", json={"title": "Pending", "status": "pending"})
        await client.post("/api/v1/tasks", json={"title": "Completed", "status": "completed"})

        response = await client.get("/api/v1/tasks", params={"status": "pending"})
        assert response.status_code == 200
        tasks = response.json()["tasks"]
        assert all(t["status"] == "pending" for t in tasks)
```

### Manual

1. Start the API server.
2. Create:
   - `curl -X POST http://localhost:8080/api/v1/tasks -H 'content-type: application/json' -d '{"title":"Buy groceries"}'`
3. List:
   - `curl http://localhost:8080/api/v1/tasks?limit=50&offset=0`
4. Get by id:
   - `curl http://localhost:8080/api/v1/tasks/<id>`
5. Update:
   - `curl -X PATCH http://localhost:8080/api/v1/tasks/<id> -H 'content-type: application/json' -d '{"status":"in_progress"}'`
6. Delete:
   - `curl -X DELETE http://localhost:8080/api/v1/tasks/<id>`

### Manual Test Checklist

- [ ] Create → list → get → update → delete works end-to-end.
- [ ] Filters (`status`, `priority`, `due_before`, `due_after`) behave as documented.
- [ ] Validation errors are 422s with useful messages.
- [ ] 404 returns standard error shape (`{"error": "...", "code": "..."}`).
- [ ] OpenAPI docs show request/response schemas for all endpoints.
- [ ] Verify `.env.example` still documents all relevant environment variables (no new env vars in this PR).

### Run Commands

```bash
make test
# or
uv run pytest -v
```

## Notes / Risks / Open Questions

- Decide whether list endpoints should default-sort (e.g., ETA ascending, then created_at).

---

## Skill Integration: api-testing

### Testing Guidance

This PR benefits significantly from the **api-testing** skill. Follow these patterns:

**Fixtures Setup**
- Use in-memory SQLite for test isolation
- Create `client` fixture with `httpx.AsyncClient` + `ASGITransport`
- Implement `task_factory` fixture for rapid test data generation
- Override `get_db` dependency for test sessions

**Test Coverage Goals**
| Module | Target Coverage |
|--------|---------------|
| `backend/api/tasks.py` | 90%+ |
| `backend/schemas/task.py` | 85%+ |
| Overall CRUD | 80%+ |

**Testing Patterns**
1. **CRUD Happy Path**: Create → Read → Update → Delete sequence
2. **Validation Errors**: Test 422 responses for invalid inputs (empty title, wrong enums)
3. **Filter Logic**: Verify status/priority filters return correct subsets
4. **Pagination**: Test limit/offset behavior
5. **Error Handling**: 404 for missing tasks, 400 for malformed requests

**Coverage Commands**
```bash
# Run with coverage
pytest tests/test_api/test_tasks_crud.py --cov=backend.api.tasks --cov-report=term-missing

# Check minimum coverage threshold
pytest --cov=backend --cov-fail-under=80
```

**Mocking External Services**
- No external services in this PR (DB is primary dependency)
- Use test database fixture instead of mocking DB layer

**See Also**
- Skill doc: `.opencode/skill/api-testing/`
- Reference: docs/02-implementation/TESTING_GUIDE.md
