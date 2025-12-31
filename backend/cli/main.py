"""TaskGenie CLI entrypoint.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import typer
from rich.console import Console

from backend.cli import db

app = typer.Typer(help="TaskGenie CLI (implementation in progress)")
console = Console()

# Add db subcommand group
app.add_typer(db.db_app, name="db")


@app.command(name="list")
def list_tasks(
    status: str = typer.Option(None, "--status", "-s", help="Filter by status"),
    priority: str = typer.Option(None, "--priority", "-p", help="Filter by priority"),
) -> None:
    """
    List all tasks with optional filtering
    """
    console.print("Not implemented yet.")


@app.command(name="add")
def add_task(
    title: str = typer.Argument(..., help="Task title"),
    description: str = typer.Option(None, "--description", "-d", help="Task description"),
    eta: str = typer.Option(
        None, "--eta", "-e", help="Due date/time (e.g., '2025-01-15' or 'tomorrow')"
    ),
    priority: str = typer.Option("medium", "--priority", "-p", help="Priority level"),
) -> None:
    """
    Add a new task
    """
    console.print("Not implemented yet.")


@app.command(name="chat")
def chat() -> None:
    """
    Start AI chat interface
    """
    console.print("Not implemented yet.")


if __name__ == "__main__":
    app()
