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

## Technical Design

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
