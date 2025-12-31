# PR-009: CLI Subcommands (Secondary) (Spec)

**Status:** Spec Only  
**Depends on:** PR-002  
**Last Reviewed:** 2025-12-29

## Goal

Provide non-interactive commands for scripting and automation, while keeping the interactive TUI as the primary UX.

## User Value

- Users can automate workflows (`cron`, shell scripts, quick one-liners).
- Enables easy debugging of API behavior without the TUI.

## Scope

### In

- Subcommands (initial set):
  - `tgenie add`
  - `tgenie list`
  - `tgenie show`
  - `tgenie edit`
  - `tgenie done`
  - `tgenie delete`
  - Output conventions:
    - human-friendly default
    - optional `--json` for scripting (recommended)

### Out

- Full import/export formats (can be added later).
- Power-user TUI features (PR-008 iteration).

## Mini-Specs

- Commands:
  - `tgenie add|list|show|edit|done|delete` (non-interactive).
- Output:
  - human-friendly by default; optional `--json` where useful.
- API integration:
  - commands call the API, not DB directly.
- Error handling:
  - stable exit codes and actionable errors when API is down or args invalid.
- Tests:
  - CLI runner tests for basic flag parsing + JSON output validity.

## References

- `docs/01-design/DESIGN_CLI.md` (command UX and flags)
- `docs/01-design/API_REFERENCE.md` (API endpoints)
- `docs/01-design/DESIGN_TUI.md` (division of responsibilities: TUI vs subcommands, keybindings, screen layout)
- `docs/02-implementation/pr-specs/PR-008-interactive-tui.md` (TUI implementation)

## Technical Design

- Thin client: subcommands call to API, not the DB directly.
- Provide stable scripting behavior:
  - exit code `0` on success, non-zero on errors
  - `--json` prints machine-readable output only (no extra formatting)
  - Prefer consistent flags across commands (e.g., `--status`, `--priority`, `--eta`).

## Appendix: Reference Implementation

### CLI Framework

```python
# backend/cli/main.py
import typer
from typing import Optional

app = typer.Typer(
    name="tgenie",
    help="Personal task management with AI chat",
    no_args_is_help=True,
)

@app.command()
def add(
    title: str,
    description: Optional[str] = typer.Option(None, "-d", "--description"),
    attach: list[str] = typer.Option(None, "-a", "--attach", multiple=True),
    eta: Optional[str] = typer.Option(None, "-e", "--eta"),
    priority: str = typer.Option("medium", "-p", "--priority"),
    status: str = typer.Option("pending", "-s", "--status"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Create a new task."""
    # Implementation would call API or TUI
    typer.echo(f"Task '{title}' created")

@app.command()
def list_cmd(
    status: Optional[str] = typer.Option(None, "--status"),
    priority: Optional[str] = typer.Option(None, "--priority"),
    due: Optional[str] = typer.Option(None, "--due"),
    search: Optional[str] = typer.Option(None, "--search"),
    limit: int = typer.Option(50, "--limit"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """List tasks with optional filters."""
    # Implementation would call API and format output
    typer.echo(f"Listing tasks...")

@app.command()
def show(
    task_id: str,
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show task details."""
    typer.echo(f"Showing task {task_id}")

@app.command()
def edit(
    task_id: str,
    title: Optional[str] = typer.Option(None, "-t", "--title"),
    description: Optional[str] = typer.Option(None, "-d", "--description"),
    status: Optional[str] = typer.Option(None, "-s", "--status"),
    priority: Optional[str] = typer.Option(None, "-p", "--priority"),
    eta: Optional[str] = typer.Option(None, "-e", "--eta"),
):
    """Update task fields."""
    typer.echo(f"Updating task {task_id}")

@app.command()
def done(
    task_id: str,
    note: Optional[str] = typer.Option(None, "--note", help="Add completion note"),
):
    """Mark task as completed."""
    typer.echo(f"Task {task_id} marked as completed")

@app.command()
def delete(
    task_id: str,
    force: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Delete a task."""
    typer.echo(f"Task {task_id} deleted")

if __name__ == "__main__":
    app()
```

## Acceptance Criteria

- [ ] Core subcommands work end-to-end against the API.
- [ ] `--json` output is valid and stable for scripting (where provided).
- [ ] Helpful errors on API-down or invalid arguments.
- [ ] Automated tests cover flag parsing + JSON output + exit codes (see Test Plan).
- [ ] Manual smoke checklist completed (see Test Plan).

---

## Skill Integration: task-workflow

### CLI Workflow Patterns

This PR should follow **task-workflow** skill patterns:

**Task CRUD Commands**

Add Command:
```bash
# Title only (minimal)
tgenie add "Buy groceries"

# Full task creation
tgenie add "Deploy to production" \
  --description "Complete all tests and deploy" \
  --priority high \
  --eta "2025-01-15" \
  --tags work,deploy
```

List Command:
```bash
# All tasks (default)
tgenie list

# Filter combinations
tgenie list --status pending --priority high
tgenie list --due today --search "urgent"
tgenie list --format json | jq '.tasks | length'
```

Show Command:
```bash
# Show task details
tgenie show abc123

# Show with expanded attachments
tgenie show abc123 --expand-attachments

# JSON output for scripting
tgenie show abc123 --format json
```

Edit Command:
```bash
# Update single field
tgenie edit abc123 --status in_progress

# Multiple updates
tgenie edit abc123 \
  --priority critical \
  --eta "2025-01-20" \
  --add-tags urgent,review

# Add attachment
tgenie edit abc123 --attach github:owner/repo/pull/456
```

Done Command:
```bash
# Mark completed
tgenie done abc123

# With note
tgenie done abc123 --note "Deployed successfully"

# Mark multiple tasks
tgenie done abc123 def456 ghi789
```

Delete Command:
```bash
# Delete with confirmation
tgenie delete abc123

# Skip confirmation
tgenie delete abc123 --yes

# Delete completed tasks older than 30 days
tgenie delete --completed --older-than 30d
```

### API Client Integration

```python
# backend/cli/commands/task_client.py
import httpx
from typing import Optional

class TaskAPIClient:
    """Async API client for CLI commands."""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.client = httpx.AsyncClient(
            base_url=base_url, timeout=30.0
        )

    async def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
        due: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """Fetch tasks with filters."""
        params = {}
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority
        if search:
            params["search"] = search
        if due:
            params["due"] = due
        params["limit"] = limit

        response = await self.client.get("/api/v1/tasks", params=params)
        response.raise_for_status()
        return response.json().get("tasks", [])

    async def get_task(self, task_id: str) -> Optional[dict]:
        """Fetch single task."""
        response = await self.client.get(f"/api/v1/tasks/{task_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def create_task(self, data: dict) -> dict:
        """Create new task."""
        response = await self.client.post("/api/v1/tasks", json=data)
        response.raise_for_status()
        return response.json()

    async def update_task(self, task_id: str, data: dict) -> Optional[dict]:
        """Update task."""
        response = await self.client.patch(
            f"/api/v1/tasks/{task_id}",
            json=data
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def delete_task(self, task_id: str) -> bool:
        """Delete task."""
        response = await self.client.delete(f"/api/v1/tasks/{task_id}")
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return True
```

### Error Handling

```python
# backend/cli/commands/error_handler.py
import typer
import sys

class TaskError(Exception):
    """Task-related error."""

class TaskNotFoundError(TaskError):
    """Task not found."""

class APIError(TaskError):
    """API communication error."""

def handle_error(error: Exception, exit_code: int = 1):
    """Handle errors with user-friendly messages."""
    if isinstance(error, TaskNotFoundError):
        typer.echo(f"Error: Task not found. Use 'list' to see available tasks.", err=True)
    elif isinstance(error, APIError):
        typer.echo(f"Error: Cannot connect to API. Is the server running?", err=True)
    elif isinstance(error, httpx.ConnectError):
        typer.echo(f"Error: Connection refused. Ensure backend is running on {base_url}", err=True)
    else:
        typer.echo(f"Error: {error}", err=True)

    sys.exit(exit_code)
```

### Output Formatting

```python
# backend/cli/commands/formatters.py
from rich.console import Console
from rich.table import Table
import json
from typing import Any

console = Console()

def format_table(tasks: list[dict]) -> None:
    """Format tasks as Rich table."""
    if not tasks:
        console.print("[yellow]No tasks found.[/]")
        return

    table = Table(title="Tasks")
    table.add_column("ID", style="dim")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Priority")
    table.add_column("Due")

    priority_colors = {
        "critical": "red",
        "high": "orange",
        "medium": "yellow",
        "low": "green",
    }

    status_symbols = {
        "pending": "○",
        "in_progress": "●",
        "completed": "✓",
    }

    for task in tasks:
        table.add_row(
            task["id"][:8] + "...",
            task["title"],
            status_symbols.get(task["status"], "?"),
            f"[{priority_colors.get(task['priority'], '')}]{task['priority']}[/]",
            task.get("eta", "None"),
        )

    console.print(table)

def format_json(data: Any) -> None:
    """Format output as JSON (for scripting)."""
    console.print_json(data)

def format_short(tasks: list[dict]) -> None:
    """Format tasks as one line each."""
    for task in tasks:
        priority = task.get("priority", "medium")[0].upper()
        console.print(f"[{priority}] [{task['status']}] {task['title']}")
```

### Testing Patterns

**CLI Integration Tests**
```python
# tests/test_cli/test_commands.py
from typer.testing import CliRunner
from backend.cli.main import app
import json

class TestAddCommand:
    def test_add_minimal(self):
        """Add task with title only."""
        result = runner.invoke(app, ["add", "Test task"])
        assert result.exit_code == 0
        assert "Created" in result.output

    def test_add_with_all_options(self):
        """Add task with all fields."""
        result = runner.invoke(app, [
            "add", "Full task",
            "--description", "Test description",
            "--priority", "high",
            "--eta", "2025-01-15",
            "--status", "in_progress",
            "--tags", "test,cli",
            "--json"
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["priority"] == "high"

    def test_add_invalid_priority(self):
        """Reject invalid priority."""
        result = runner.invoke(app, ["add", "Test", "--priority", "super-high"])
        assert result.exit_code != 0
        assert "Invalid" in result.output or "Error" in result.output

class TestListCommand:
    def test_list_json_output(self):
        """List with JSON output."""
        result = runner.invoke(app, ["list", "--json"])
        assert result.exit_code == 0

        # Verify valid JSON
        import json
        data = json.loads(result.output)
        assert "tasks" in data

    def test_list_with_filters(self):
        """List with status and priority filters."""
        # Add a task first
        runner.invoke(app, ["add", "Test task"])

        result = runner.invoke(app, ["list", "--status", "pending"])
        assert result.exit_code == 0

class TestEditCommand:
    def test_edit_status(self):
        """Update task status."""
        result = runner.invoke(app, ["edit", "task-123", "-s", "in_progress"])
        assert result.exit_code == 0

    def test_edit_not_found(self):
        """Error on non-existent task."""
        # Mock API to return 404
        result = runner.invoke(app, ["edit", "nonexistent", "-s", "done"])
        assert result.exit_code != 0

class TestDoneCommand:
    def test_done_success(self):
        """Mark task as completed."""
        result = runner.invoke(app, ["done", "task-123"])
        assert result.exit_code == 0
        assert "completed" in result.output.lower()

    def test_done_with_note(self):
        """Mark task completed with note."""
        result = runner.invoke(app, ["done", "task-123", "--note", "Deployed successfully"])
        assert result.exit_code == 0
```

**API Client Tests**
```python
# tests/test_cli/test_api_client.py
import pytest
from backend.cli.commands.task_client import TaskAPIClient
from unittest.mock import AsyncMock, patch

class TestTaskAPIClient:
    @pytest.mark.asyncio
    async def test_list_tasks(self):
        """List tasks successfully."""
        mock_client = AsyncMock()
        mock_client.get.return_value.json.return_value = {
            "tasks": [{"id": "1", "title": "Task 1"}]
        }

        with patch("httpx.AsyncClient", return_value=mock_client):
            client = TaskAPIClient()
            tasks = await client.list_tasks()
            assert len(tasks) == 1
            assert tasks[0]["title"] == "Task 1"

    @pytest.mark.asyncio
    async def test_create_task(self):
        """Create task successfully."""
        mock_client = AsyncMock()
        mock_client.post.return_value.json.return_value = {
            "id": "abc123",
            "title": "New task",
        }

        with patch("httpx.AsyncClient", return_value=mock_client):
            client = TaskAPIClient()
            task = await client.create_task({"title": "New task"})
            assert task["id"] == "abc123"

    @pytest.mark.asyncio
    async def test_task_not_found(self):
        """Handle 404 gracefully."""
        mock_client = AsyncMock()
        mock_client.get.return_value.status_code = 404

        with patch("httpx.AsyncClient", return_value=mock_client):
            client = TaskAPIClient()
            task = await client.get_task("nonexistent")
            assert task is None
```

**See Also**
- Skill doc: `.opencode/skill/task-workflow/`
- Reference: docs/01-design/DESIGN_CLI.md

## Test Plan

### Automated

```python
# tests/test_cli/test_commands.py
import pytest
from typer.testing import CliRunner
from backend.cli.main import app

@pytest.fixture
def runner():
    return CliRunner()

class TestAddCommand:
    """Tests for 'tgenie add' command"""

    def test_add_minimal(self, runner):
        """Add task with title only."""
        result = runner.invoke(app, ["add", "Buy groceries"])
        assert result.exit_code == 0
        assert "Created" in result.output

    def test_add_with_all_options(self, runner):
        """Add task with all fields."""
        result = runner.invoke(app, [
            "add", "Complete project",
            "-d", "Finish implementation",
            "-p", "high",
            "-e", "2025-01-15",
            "-s", "in_progress",
            "--json"
        ])
        assert result.exit_code == 0
        assert json.loads(result.output)["priority"] == "high"

    def test_add_invalid_priority(self, runner):
        """Reject invalid priority."""
        result = runner.invoke(app, ["add", "Test", "-p", "super-high"])
        assert result.exit_code != 0
        assert "Invalid" in result.output or "Error" in result.output


class TestListCommand:
    """Tests for 'tgenie list' command"""

    def test_list_json_output(self, runner):
        """List with JSON output."""
        result = runner.invoke(app, ["list", "--json"])
        assert result.exit_code == 0

        # Verify valid JSON
        import json
        data = json.loads(result.output)
        assert "tasks" in data

    def test_list_with_filters(self, runner):
        """List with status and priority filters."""
        # Add a task first
        runner.invoke(app, ["add", "Test task"])

        result = runner.invoke(app, ["list", "--status", "pending"])
        assert result.exit_code == 0


class TestEditCommand:
    """Tests for 'tgenie edit' command"""

    def test_edit_status(self, runner):
        """Update task status."""
        result = runner.invoke(app, ["edit", "task-123", "-s", "in_progress"])
        assert result.exit_code == 0

    def test_edit_not_found(self, runner):
        """Error on non-existent task."""
        # Mock API to return 404
        result = runner.invoke(app, ["edit", "nonexistent", "-s", "done"])
        assert result.exit_code != 0


class TestDoneCommand:
    """Tests for 'tgenie done' command"""

    def test_done_success(self, runner):
        """Mark task as completed."""
        result = runner.invoke(app, ["done", "task-123"])
        assert result.exit_code == 0
        assert "completed" in result.output.lower()

    def test_done_with_note(self, runner):
        """Mark task completed with note."""
        result = runner.invoke(app, ["done", "task-123", "--note", "Deployed successfully"])
        assert result.exit_code == 0


class TestDeleteCommand:
    """Tests for 'tgenie delete' command"""

    def test_delete_requires_confirmation(self, runner):
        """Delete requires confirmation without --yes."""
        result = runner.invoke(app, ["delete", "task-123"])
        assert result.exit_code != 0  # Typer should prompt for confirmation

    def test_delete_with_force(self, runner):
        """Delete with --yes skips confirmation."""
        result = runner.invoke(app, ["delete", "task-123", "--yes"])
        assert result.exit_code == 0


class TestExitCodes:
    """Tests for proper exit codes"""

    def test_success_returns_zero(self, runner):
        """Successful commands return exit code 0."""
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0

    def test_api_error_returns_nonzero(self, runner):
        """API errors return non-zero exit code."""
        # Mock HTTP client to return 500
        result = runner.invoke(app, ["list"])
        assert result.exit_code != 0
```

### Manual

1. Start API.
2. Run:
   - `tgenie add "Test task"`
   - `tgenie list`
   - `tgenie show <id>`
   - `tgenie done <id>`
3. Stop API; verify commands fail with clear guidance.

### Manual Test Checklist

- [ ] All core subcommands return exit code 0 on success, non-zero on failure.
- [ ] `--json` prints machine-readable JSON only (no extra logs on stdout).
- [ ] API-down scenarios print clear guidance and return non-zero exit codes.
- [ ] Destructive commands (delete) prompt unless `--yes` is provided.

### Run Commands

```bash
make test
# or
uv run pytest -v
```

## Notes / Risks / Open Questions

- Confirm where CLI gets API base URL (env var/config) and document it consistently.
- Keep `--json` outputs stable (avoid adding human text/logging on stdout).
- Decide whether `tgenie delete` prompts by default in non-interactive shells (TTY detection).
