"""Tests for task API endpoints.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from backend import config
from backend.main import app

# Constants
DEFAULT_PAGE_SIZE = 50
DEFAULT_OFFSET = 0


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create a test client with isolated database."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    config.get_settings.cache_clear()

    # Initialize database
    from backend.database import init_db  # noqa: PLC0415

    init_db()

    return TestClient(app)


def test_create_task(client: TestClient) -> None:
    """Test creating a task."""
    response = client.post(
        "/api/v1/tasks",
        json={"title": "Test Task", "description": "Test Description", "status": "pending", "priority": "high"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Test Description"
    assert data["status"] == "pending"
    assert data["priority"] == "high"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert data["attachments"] == []


def test_create_task_with_all_fields(client: TestClient) -> None:
    """Test creating a task with all fields."""
    eta = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    response = client.post(
        "/api/v1/tasks",
        json={
            "title": "Complete Task",
            "description": "Full description",
            "status": "in_progress",
            "priority": "critical",
            "eta": eta,
            "tags": ["tag1", "tag2"],
            "metadata": {"key": "value"},
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Complete Task"
    assert data["description"] == "Full description"
    assert data["status"] == "in_progress"
    assert data["priority"] == "critical"
    assert data["tags"] == ["tag1", "tag2"]
    assert data["metadata"] == {"key": "value"}
    assert data["attachments"] == []


def test_create_task_validation_empty_title(client: TestClient) -> None:
    """Test that empty title is rejected."""
    response = client.post("/api/v1/tasks", json={"title": ""})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_task_validation_invalid_status(client: TestClient) -> None:
    """Test that invalid status is rejected."""
    response = client.post("/api/v1/tasks", json={"title": "Test", "status": "invalid"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_task_validation_invalid_priority(client: TestClient) -> None:
    """Test that invalid priority is rejected."""
    response = client.post("/api/v1/tasks", json={"title": "Test", "priority": "invalid"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_task_validation_title_too_long(client: TestClient) -> None:
    """Test that title exceeding max length is rejected."""
    long_title = "a" * 256
    response = client.post("/api/v1/tasks", json={"title": long_title})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_get_task(client: TestClient) -> None:
    """Test getting a task by ID."""
    # Create a task first
    create_response = client.post("/api/v1/tasks", json={"title": "Get Test Task"})
    assert create_response.status_code == status.HTTP_201_CREATED
    task_id = create_response.json()["id"]

    # Get the task
    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Get Test Task"
    assert data["attachments"] == []


def test_get_task_not_found(client: TestClient) -> None:
    """Test getting a non-existent task returns 404 with standard error shape."""
    response = client.get("/api/v1/tasks/nonexistent-id")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "error" in data
    assert "code" in data
    assert data["code"] == "TASK_NOT_FOUND"


def test_update_task(client: TestClient) -> None:
    """Test updating a task."""
    # Create a task first
    create_response = client.post("/api/v1/tasks", json={"title": "Original Title", "status": "pending"})
    assert create_response.status_code == status.HTTP_201_CREATED
    task_id = create_response.json()["id"]

    # Update the task
    response = client.patch(f"/api/v1/tasks/{task_id}", json={"title": "Updated Title", "status": "in_progress"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["status"] == "in_progress"

    # Verify update persisted
    get_response = client.get(f"/api/v1/tasks/{task_id}")
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()["title"] == "Updated Title"
    assert get_response.json()["status"] == "in_progress"


def test_update_task_partial(client: TestClient) -> None:
    """Test partial update of a task."""
    # Create a task first
    create_response = client.post(
        "/api/v1/tasks", json={"title": "Original", "description": "Original Description", "priority": "low"}
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    task_id = create_response.json()["id"]

    # Update only title
    response = client.patch(f"/api/v1/tasks/{task_id}", json={"title": "Updated"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Updated"
    assert data["description"] == "Original Description"  # Unchanged
    assert data["priority"] == "low"  # Unchanged


def test_update_task_all_fields_individually(client: TestClient) -> None:
    """Test updating each field individually to cover all update paths."""
    # Create a task
    create_response = client.post(
        "/api/v1/tasks", json={"title": "Original", "description": "Original", "status": "pending", "priority": "low"}
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    task_id = create_response.json()["id"]

    # Update status
    response = client.patch(f"/api/v1/tasks/{task_id}", json={"status": "in_progress"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "in_progress"

    # Update priority
    response = client.patch(f"/api/v1/tasks/{task_id}", json={"priority": "high"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["priority"] == "high"

    # Update description
    response = client.patch(f"/api/v1/tasks/{task_id}", json={"description": "New Description"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["description"] == "New Description"

    # Update eta
    eta_dt = datetime.now(UTC)
    eta_str = eta_dt.isoformat().replace("+00:00", "Z")
    response = client.patch(f"/api/v1/tasks/{task_id}", json={"eta": eta_str})
    assert response.status_code == status.HTTP_200_OK
    # Response may not include 'Z' suffix, so compare datetime objects
    response_eta_str = response.json()["eta"]
    if response_eta_str.endswith("Z"):
        response_eta = datetime.fromisoformat(response_eta_str.replace("Z", "+00:00"))
    else:
        response_eta = datetime.fromisoformat(response_eta_str).replace(tzinfo=UTC)
    assert abs((response_eta - eta_dt).total_seconds()) < 1  # Within 1 second

    # Update tags
    response = client.patch(f"/api/v1/tasks/{task_id}", json={"tags": ["tag1", "tag2"]})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["tags"] == ["tag1", "tag2"]

    # Update metadata
    response = client.patch(f"/api/v1/tasks/{task_id}", json={"metadata": {"key": "value"}})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["metadata"] == {"key": "value"}

    # Update title (to cover title update path)
    response = client.patch(f"/api/v1/tasks/{task_id}", json={"title": "Updated Title"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == "Updated Title"

    # Test setting nullable fields to None (to cover None value paths)
    response = client.patch(f"/api/v1/tasks/{task_id}", json={"description": None})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["description"] is None

    response = client.patch(f"/api/v1/tasks/{task_id}", json={"eta": None})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["eta"] is None

    response = client.patch(f"/api/v1/tasks/{task_id}", json={"tags": None})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["tags"] is None

    response = client.patch(f"/api/v1/tasks/{task_id}", json={"metadata": None})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["metadata"] is None


def test_update_task_not_found(client: TestClient) -> None:
    """Test updating a non-existent task returns 404 with standard error shape."""
    response = client.patch("/api/v1/tasks/nonexistent-id", json={"title": "Updated"})
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "error" in data
    assert "code" in data
    assert data["code"] == "TASK_NOT_FOUND"


def test_delete_task(client: TestClient) -> None:
    """Test deleting a task."""
    # Create a task first
    create_response = client.post("/api/v1/tasks", json={"title": "Task to Delete"})
    assert create_response.status_code == status.HTTP_201_CREATED
    task_id = create_response.json()["id"]

    # Delete the task
    response = client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify task is deleted
    get_response = client.get(f"/api/v1/tasks/{task_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_task_not_found(client: TestClient) -> None:
    """Test deleting a non-existent task returns 404 with standard error shape."""
    response = client.delete("/api/v1/tasks/nonexistent-id")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "error" in data
    assert "code" in data
    assert data["code"] == "TASK_NOT_FOUND"
    assert data["error"] == "Task not found"


def test_list_tasks_empty(client: TestClient) -> None:
    """Test listing tasks when none exist."""
    response = client.get("/api/v1/tasks")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["tasks"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["page_size"] == DEFAULT_PAGE_SIZE


def test_list_tasks_defaults(client: TestClient) -> None:
    """Test list tasks with default pagination."""
    # Create some tasks
    for i in range(3):
        client.post("/api/v1/tasks", json={"title": f"Task {i}"})

    response = client.get("/api/v1/tasks")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["tasks"]) == 3  # noqa: PLR2004
    assert data["total"] == 3  # noqa: PLR2004
    assert data["page"] == 1
    assert data["page_size"] == DEFAULT_PAGE_SIZE


def test_list_tasks_pagination(client: TestClient) -> None:
    """Test list tasks with pagination."""
    # Create 5 tasks
    for i in range(5):
        client.post("/api/v1/tasks", json={"title": f"Task {i}"})

    # Get first page (limit=2, offset=0)
    response = client.get("/api/v1/tasks?limit=2&offset=0")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["tasks"]) == 2  # noqa: PLR2004
    assert data["total"] == 5  # noqa: PLR2004
    assert data["page"] == 1
    assert data["page_size"] == 2  # noqa: PLR2004

    # Get second page (limit=2, offset=2)
    response = client.get("/api/v1/tasks?limit=2&offset=2")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["tasks"]) == 2  # noqa: PLR2004
    assert data["total"] == 5  # noqa: PLR2004
    assert data["page"] == 2  # noqa: PLR2004
    assert data["page_size"] == 2  # noqa: PLR2004


def test_list_tasks_filter_status(client: TestClient) -> None:
    """Test filtering tasks by status."""
    # Create tasks with different statuses
    client.post("/api/v1/tasks", json={"title": "Pending Task", "status": "pending"})
    client.post("/api/v1/tasks", json={"title": "In Progress Task", "status": "in_progress"})
    client.post("/api/v1/tasks", json={"title": "Completed Task", "status": "completed"})

    # Filter by pending
    response = client.get("/api/v1/tasks?status=pending")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["status"] == "pending"
    assert data["total"] == 1


def test_list_tasks_filter_priority(client: TestClient) -> None:
    """Test filtering tasks by priority."""
    # Create tasks with different priorities
    client.post("/api/v1/tasks", json={"title": "Low Priority", "priority": "low"})
    client.post("/api/v1/tasks", json={"title": "High Priority", "priority": "high"})
    client.post("/api/v1/tasks", json={"title": "Medium Priority", "priority": "medium"})

    # Filter by high priority
    response = client.get("/api/v1/tasks?priority=high")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["priority"] == "high"
    assert data["total"] == 1


def test_list_tasks_filter_due_before(client: TestClient) -> None:
    """Test filtering tasks by due_before."""
    now = datetime.now(UTC)
    before = (now.replace(hour=10, minute=0, second=0, microsecond=0)).isoformat().replace("+00:00", "Z")
    after = (now.replace(hour=14, minute=0, second=0, microsecond=0)).isoformat().replace("+00:00", "Z")

    # Create tasks with different ETAs
    client.post("/api/v1/tasks", json={"title": "Early Task", "eta": before})
    client.post("/api/v1/tasks", json={"title": "Late Task", "eta": after})

    # Filter by due_before (noon)
    noon = (now.replace(hour=12, minute=0, second=0, microsecond=0)).isoformat().replace("+00:00", "Z")
    response = client.get(f"/api/v1/tasks?due_before={noon}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["title"] == "Early Task"
    assert data["total"] == 1


def test_list_tasks_filter_due_after(client: TestClient) -> None:
    """Test filtering tasks by due_after."""
    now = datetime.now(UTC)
    before = (now.replace(hour=10, minute=0, second=0, microsecond=0)).isoformat().replace("+00:00", "Z")
    after = (now.replace(hour=14, minute=0, second=0, microsecond=0)).isoformat().replace("+00:00", "Z")

    # Create tasks with different ETAs
    client.post("/api/v1/tasks", json={"title": "Early Task", "eta": before})
    client.post("/api/v1/tasks", json={"title": "Late Task", "eta": after})

    # Filter by due_after (noon)
    noon = (now.replace(hour=12, minute=0, second=0, microsecond=0)).isoformat().replace("+00:00", "Z")
    response = client.get(f"/api/v1/tasks?due_after={noon}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["title"] == "Late Task"
    assert data["total"] == 1


def test_list_tasks_invalid_status(client: TestClient) -> None:
    """Test that invalid status enum value returns 422."""
    response = client.get("/api/v1/tasks?status=invalid_status")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_list_tasks_invalid_priority(client: TestClient) -> None:
    """Test that invalid priority enum value returns 422."""
    response = client.get("/api/v1/tasks?priority=invalid_priority")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_list_tasks_ordering(client: TestClient) -> None:
    """Test that tasks are ordered by created_at DESC, id ASC."""
    # Create tasks (they will have different created_at timestamps)
    _ = client.post("/api/v1/tasks", json={"title": "Task 1"})
    _ = client.post("/api/v1/tasks", json={"title": "Task 2"})
    _ = client.post("/api/v1/tasks", json={"title": "Task 3"})

    response = client.get("/api/v1/tasks")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    tasks = data["tasks"]

    # Verify we got all 3 tasks
    assert len(tasks) == 3  # noqa: PLR2004

    # Verify created_at is descending (or equal)
    created_dates = [datetime.fromisoformat(t["created_at"].replace("Z", "+00:00")) for t in tasks]
    # Check that dates are in descending order (or equal)
    for i in range(len(created_dates) - 1):
        assert created_dates[i] >= created_dates[i + 1], "Tasks should be ordered by created_at DESC"

    # Verify that when created_at is equal, id is ascending
    # Group tasks by created_at and verify id ordering within each group
    tasks_by_date: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for task in tasks:
        tasks_by_date[task["created_at"]].append(task)

    for date_key, date_tasks in tasks_by_date.items():
        if len(date_tasks) > 1:
            # Within same created_at, ids should be in ascending order
            ids = [t["id"] for t in date_tasks]
            assert ids == sorted(ids), "When created_at is equal, tasks should be ordered by id ASC"


def test_list_tasks_limit_enforcement(client: TestClient) -> None:
    """Test that limit is enforced."""
    # Create 10 tasks
    for i in range(10):
        client.post("/api/v1/tasks", json={"title": f"Task {i}"})

    # Request with limit=3
    response = client.get("/api/v1/tasks?limit=3")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["tasks"]) == 3  # noqa: PLR2004
    assert data["total"] == 10  # noqa: PLR2004
    assert data["page_size"] == 3  # noqa: PLR2004


def test_list_tasks_offset(client: TestClient) -> None:
    """Test that offset works correctly."""
    # Create 5 tasks
    task_ids = []
    for i in range(5):
        response = client.post("/api/v1/tasks", json={"title": f"Task {i}"})
        task_ids.append(response.json()["id"])

    # Get all tasks to see order
    all_response = client.get("/api/v1/tasks")
    all_tasks = all_response.json()["tasks"]
    all_task_ids = [t["id"] for t in all_tasks]

    # Get with offset=2
    response = client.get("/api/v1/tasks?limit=2&offset=2")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["tasks"]) == 2  # noqa: PLR2004
    # Should get tasks starting from index 2
    assert data["tasks"][0]["id"] == all_task_ids[2]  # noqa: PLR2004
    assert data["tasks"][1]["id"] == all_task_ids[3]  # noqa: PLR2004
    assert data["page"] == 2  # noqa: PLR2004  # offset=2, limit=2 -> page 2


def test_list_tasks_empty_result_set(client: TestClient) -> None:
    """Test list_tasks with filters that return no results to cover empty list path."""
    # Create a task with specific attributes
    client.post("/api/v1/tasks", json={"title": "Task", "status": "pending", "priority": "low"})

    # Filter that returns no results
    response = client.get("/api/v1/tasks?status=completed")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["tasks"]) == 0
    assert data["total"] == 0
    assert data["page"] == 1


def test_list_tasks_with_all_filters(client: TestClient) -> None:
    """Test list_tasks with all filters applied simultaneously."""
    now = datetime.now(UTC)
    eta1 = (now.replace(hour=10, minute=0, second=0, microsecond=0)).isoformat().replace("+00:00", "Z")
    eta2 = (now.replace(hour=14, minute=0, second=0, microsecond=0)).isoformat().replace("+00:00", "Z")

    # Create tasks with different attributes
    client.post("/api/v1/tasks", json={"title": "Task 1", "status": "pending", "priority": "low", "eta": eta1})
    client.post("/api/v1/tasks", json={"title": "Task 2", "status": "completed", "priority": "high", "eta": eta2})
    client.post("/api/v1/tasks", json={"title": "Task 3", "status": "pending", "priority": "high", "eta": eta1})

    # Filter with all parameters
    noon = (now.replace(hour=12, minute=0, second=0, microsecond=0)).isoformat().replace("+00:00", "Z")
    response = client.get(f"/api/v1/tasks?status=pending&priority=high&due_before={noon}&due_after={eta1}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # Should match Task 3
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["title"] == "Task 3"


def test_task_response_includes_attachments(client: TestClient) -> None:
    """Test that task responses include attachments field as empty list."""
    response = client.post("/api/v1/tasks", json={"title": "Test Task"})
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "attachments" in data
    assert data["attachments"] == []


def test_list_tasks_with_multiple_tasks_ensures_conversion_path(client: TestClient) -> None:
    """Test list_tasks with multiple tasks to ensure task conversion path is covered."""
    # Create multiple tasks to ensure the list comprehension path is covered
    for i in range(5):
        client.post("/api/v1/tasks", json={"title": f"Task {i}"})

    response = client.get("/api/v1/tasks")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["tasks"]) == 5  # noqa: PLR2004
    # Verify all tasks have attachments field
    for task in data["tasks"]:
        assert "attachments" in task
        assert task["attachments"] == []


def test_list_tasks_page_calculation_edge_cases(client: TestClient) -> None:
    """Test list_tasks page calculation with various offset/limit combinations."""
    # Create 10 tasks
    for i in range(10):
        client.post("/api/v1/tasks", json={"title": f"Task {i}"})

    # Test with limit=3, offset=0 (page 1)
    response = client.get("/api/v1/tasks?limit=3&offset=0")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["page"] == 1

    # Test with limit=3, offset=3 (page 2)
    response = client.get("/api/v1/tasks?limit=3&offset=3")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["page"] == 2  # noqa: PLR2004

    # Test with limit=3, offset=6 (page 3)
    response = client.get("/api/v1/tasks?limit=3&offset=6")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["page"] == 3  # noqa: PLR2004


def test_get_task_exception_handler_path(client: TestClient) -> None:
    """Test that get_task endpoint exception handler is hit."""
    # This test ensures the exception handler in get_task_endpoint is executed
    response = client.get("/api/v1/tasks/nonexistent-task-id")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "error" in data
    assert "code" in data
    assert data["code"] == "TASK_NOT_FOUND"


def test_update_task_exception_handler_path(client: TestClient) -> None:
    """Test that update_task endpoint exception handler is hit."""
    # This test ensures the exception handler in update_task_endpoint is executed
    response = client.patch("/api/v1/tasks/nonexistent-task-id", json={"title": "Updated"})
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "error" in data
    assert "code" in data
    assert data["code"] == "TASK_NOT_FOUND"


def test_delete_task_success_path(client: TestClient) -> None:
    """Test that delete_task endpoint success path (returning 204) is covered."""
    # Create a task
    create_response = client.post("/api/v1/tasks", json={"title": "Task to Delete"})
    task_id = create_response.json()["id"]

    # Delete it - this should hit the success path returning 204
    delete_response = client.delete(f"/api/v1/tasks/{task_id}")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    # Verify task is actually deleted
    get_response = client.get(f"/api/v1/tasks/{task_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_update_task_all_fields_at_once(client: TestClient) -> None:
    """Test updating all fields in a single update to cover all update paths."""
    # Create a task with initial values
    create_response = client.post(
        "/api/v1/tasks",
        json={
            "title": "Original Title",
            "description": "Original Description",
            "status": "pending",
            "priority": "low",
            "tags": ["old_tag"],
            "metadata": {"old": "value"},
        },
    )
    task_id = create_response.json()["id"]

    # Update all fields at once (including setting some to None)
    eta_dt = datetime.now(UTC)
    eta_str = eta_dt.isoformat().replace("+00:00", "Z")
    update_response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={
            "title": "Updated Title",
            "description": "Updated Description",
            "status": "completed",
            "priority": "critical",
            "eta": eta_str,
            "tags": ["new_tag1", "new_tag2"],
            "metadata": {"new": "value"},
        },
    )
    assert update_response.status_code == status.HTTP_200_OK
    data = update_response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated Description"
    assert data["status"] == "completed"
    assert data["priority"] == "critical"
    assert data["tags"] == ["new_tag1", "new_tag2"]
    assert data["metadata"] == {"new": "value"}


def test_update_task_with_none_for_optional_fields(client: TestClient) -> None:
    """Test updating with None values for optional fields to cover None check paths."""
    # Create a task with all fields set
    eta_dt = datetime.now(UTC)
    eta_str = eta_dt.isoformat().replace("+00:00", "Z")
    create_response = client.post(
        "/api/v1/tasks",
        json={
            "title": "Full Task",
            "description": "Full Description",
            "status": "in_progress",
            "priority": "high",
            "eta": eta_str,
            "tags": ["tag1"],
            "metadata": {"key": "value"},
        },
    )
    task_id = create_response.json()["id"]

    # Update status and priority to None (should not update since they're required enums)
    # But update other optional fields to None
    update_response = client.patch(
        f"/api/v1/tasks/{task_id}", json={"description": None, "eta": None, "tags": None, "metadata": None}
    )
    assert update_response.status_code == status.HTTP_200_OK
    data = update_response.json()
    assert data["description"] is None
    assert data["eta"] is None
    assert data["tags"] is None
    assert data["metadata"] is None
    # Status and priority should remain unchanged
    assert data["status"] == "in_progress"
    assert data["priority"] == "high"


def test_update_task_null_title_rejected(client: TestClient) -> None:
    """Test that PATCH with title: null is rejected with 422 validation error."""
    # Create a task first
    create_response = client.post("/api/v1/tasks", json={"title": "Test Task"})
    assert create_response.status_code == status.HTTP_201_CREATED
    task_id = create_response.json()["id"]

    # Attempt to update title to null (should be rejected)
    response = client.patch(f"/api/v1/tasks/{task_id}", json={"title": None})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Verify task title is unchanged
    get_response = client.get(f"/api/v1/tasks/{task_id}")
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()["title"] == "Test Task"
