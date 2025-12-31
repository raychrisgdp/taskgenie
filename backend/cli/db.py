"""Database CLI commands.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import sqlite3
from pathlib import Path

import alembic.command
import alembic.config
import typer
from rich.console import Console
from rich.prompt import Confirm
from typer import Typer

import backend.config

console = Console()
db_app = Typer(help="Database management commands")


def get_alembic_cfg() -> alembic.config.Config:
    """Get Alembic configuration."""
    backend_dir = Path(__file__).resolve().parents[1]
    project_root = backend_dir.parent
    migrations_dir = backend_dir / "migrations"
    alembic_ini = migrations_dir / "alembic.ini"

    if not alembic_ini.exists():
        console.print(f"[yellow]⚠[/yellow]  alembic.ini not found at {alembic_ini}, using defaults")
        cfg = alembic.config.Config()
    else:
        cfg = alembic.config.Config(str(alembic_ini))

    cfg.set_main_option("prepend_sys_path", str(project_root))
    cfg.set_main_option("script_location", str(migrations_dir))

    # Override database URL from settings
    cfg.set_main_option("sqlalchemy.url", backend.config.get_settings().database_url_resolved)
    return cfg


@db_app.command(name="upgrade")
def upgrade(
    revision: str = typer.Option("head", "--rev", help="Revision to upgrade to (default: head)"),
) -> None:
    """Upgrade database to a specific revision (default: head)."""
    try:
        backend.config.get_settings().ensure_app_dirs()
        cfg = get_alembic_cfg()
        alembic.command.upgrade(cfg, revision)
        console.print(f"[green]✓[/green] Database upgraded to {revision}")
    except Exception as e:
        console.print(f"[red]✗[/red] Upgrade failed: {e}")
        raise typer.Exit(1)


@db_app.command(name="downgrade")
def downgrade(
    revision: str = typer.Option(
        "-1", "--rev", help="Revision to downgrade to (default: -1 for one step back)"
    ),
) -> None:
    """Downgrade database by one revision or to a specific revision."""
    try:
        backend.config.get_settings().ensure_app_dirs()
        cfg = get_alembic_cfg()
        alembic.command.downgrade(cfg, revision)
        console.print(f"[green]✓[/green] Database downgraded to {revision}")
    except Exception as e:
        console.print(f"[red]✗[/red] Downgrade failed: {e}")
        raise typer.Exit(1)


@db_app.command(name="revision")
def revision(
    message: str = typer.Option(..., "-m", "--message", help="Migration message"),
    autogenerate: bool = typer.Option(
        False, "--autogenerate", "-a", help="Auto-generate migration from models"
    ),
) -> None:
    """Create a new migration revision."""
    try:
        backend.config.get_settings().ensure_app_dirs()
        cfg = get_alembic_cfg()
        alembic.command.revision(cfg, message=message, autogenerate=autogenerate)
        console.print(f"[green]✓[/green] Created migration: {message}")
    except Exception as e:
        console.print(f"[red]✗[/red] Revision creation failed: {e}")
        raise typer.Exit(1)


@db_app.command(name="dump")
def dump(out: Path = typer.Option(..., "--out", help="Output SQL file path")) -> None:
    """Dump database to SQL file."""
    try:
        settings = backend.config.get_settings()
        db_path = settings.database_path
        if not db_path.exists():
            console.print(f"[yellow]⚠[/yellow]  Database file not found: {db_path}")
            raise typer.Exit(1)

        out.parent.mkdir(parents=True, exist_ok=True)

        # Use sqlite3 for dump (works with aiosqlite databases)
        with sqlite3.connect(str(db_path)) as conn, out.open("w", encoding="utf-8") as f:
            for line in conn.iterdump():
                f.write(f"{line}\n")

        console.print(f"[green]✓[/green] Database dumped to {out}")
    except Exception as e:
        console.print(f"[red]✗[/red] Dump failed: {e}")
        raise typer.Exit(1)


@db_app.command(name="restore")
def restore(input_file: Path = typer.Option(..., "--in", help="Input SQL file path")) -> None:
    """Restore database from SQL file (WARNING: overwrites existing database)."""
    if not input_file.exists():
        console.print(f"[red]✗[/red] Input file not found: {input_file}")
        raise typer.Exit(1)

    settings = backend.config.get_settings()
    db_path = settings.database_path

    # Confirm overwrite
    if db_path.exists():
        console.print(f"[yellow]⚠[/yellow]  This will overwrite the existing database at {db_path}")
        if not Confirm.ask("Continue?", default=False):
            console.print("[yellow]Restore cancelled[/yellow]")
            raise typer.Exit(0)

    try:
        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        if db_path.exists():
            db_path.unlink()

        # Restore from SQL file
        with sqlite3.connect(str(db_path)) as conn, input_file.open("r", encoding="utf-8") as f:
            conn.executescript(f.read())

        console.print(f"[green]✓[/green] Database restored from {input_file}")
    except Exception as e:
        console.print(f"[red]✗[/red] Restore failed: {e}")
        raise typer.Exit(1)


@db_app.command(name="reset")
def reset(yes: bool = typer.Option(False, "--yes", help="Skip confirmation")) -> None:
    """Reset database (WARNING: deletes all data)."""
    db_path = backend.config.get_settings().database_path

    if not db_path.exists():
        console.print("[yellow]⚠[/yellow]  Database file does not exist")
        raise typer.Exit(0)

    # Confirm deletion
    if not yes:
        console.print(f"[red]⚠[/red]  This will DELETE the database at {db_path}")
        if not Confirm.ask("Are you sure?", default=False):
            console.print("[yellow]Reset cancelled[/yellow]")
            raise typer.Exit(0)

    try:
        db_path.unlink()
        console.print("[green]✓[/green] Database reset (file deleted)")
    except Exception as e:
        console.print(f"[red]✗[/red] Reset failed: {e}")
        raise typer.Exit(1)
