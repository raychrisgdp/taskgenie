import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from ..config import settings

app = typer.Typer(help="Personal TODO - CLI-first AI-native task manager")
console = Console()


@app.command()
def list_tasks(
    status: str = typer.Option(None, "--status", "-s", help="Filter by status"),
    priority: str = typer.Option(None, "--priority", "-p", help="Filter by priority"),
) -> None:
    """
    List all tasks with optional filtering
    """
    console.print("List functionality coming soon!")


@app.command()
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
    rprint(f"[green]✓[/green] Task created with title: {title}")
    if description:
        rprint(f"  Description: {description}")
    if eta:
        rprint(f"  ETA: {eta}")
    if priority:
        rprint(f"  Priority: {priority}")


@app.command()
def chat() -> None:
    """
    Start AI chat interface
    """
    console.print("[bold]🤖 AI Chat - Type 'exit' to quit[/bold]")
    console.print("Starting chat functionality...")


@app.command()
def config_show() -> None:
    """
    Show current configuration
    """
    config_table = Table(title="Current Configuration")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")

    config_table.add_row("LLM Provider", settings.llm_provider)
    config_table.add_row("LLM Model", settings.llm_model)
    config_table.add_row("API Key", f"{'*' * 8 if settings.llm_api_key else 'Not set'}")
    config_table.add_row(
        "Notifications", "Enabled" if settings.notifications_enabled else "Disabled"
    )
    config_table.add_row("Database", settings.database_url)

    console.print(config_table)


if __name__ == "__main__":
    app()
