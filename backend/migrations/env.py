"""Alembic environment configuration for async SQLAlchemy.

Supports both sync and async database URLs. When a sync URL is provided
(e.g., sqlite://), migrations run synchronously to avoid asyncio conflicts.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import Base and all models so Alembic can detect them
from backend.config import get_settings
from backend.database import Base
from backend.models import Attachment, ChatHistory, Config, Notification, Task  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url() -> str:
    """Get database URL from settings or config override."""
    # Allow URL override from Alembic config (used by _run_migrations_sync)
    url_override = config.get_main_option("sqlalchemy.url")
    if url_override:
        return str(url_override)
    return get_settings().database_url_resolved


def is_sync_url(url: str) -> bool:
    """Check if URL is synchronous (not async)."""
    return not url.startswith(("sqlite+aiosqlite://", "postgresql+asyncpg://"))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with a connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration, prefix="sqlalchemy.", poolclass=pool.NullPool
    )

    async with connectable.begin() as connection:
        # Enable foreign keys for SQLite
        await connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_sync_migrations() -> None:
    """Run migrations synchronously (for sync URLs like sqlite://)."""
    url = get_url()

    # Create synchronous engine
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.begin() as connection:
        # Enable foreign keys for SQLite
        if url.startswith("sqlite"):
            connection.execute(text("PRAGMA foreign_keys=ON"))
        # Run migrations synchronously
        do_run_migrations(connection)

    connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Detects sync vs async URL and uses appropriate engine.
    Sync URLs (e.g., sqlite://) are used to avoid asyncio conflicts
    when migrations are called from async contexts.
    """
    url = get_url()
    if is_sync_url(url):
        # Use synchronous engine to avoid asyncio conflicts
        run_sync_migrations()
    else:
        # Use async engine - asyncio.run() will fail if loop is already running
        # This path should only be used when migrations are run directly via CLI
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
