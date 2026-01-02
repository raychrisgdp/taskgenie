"""Database initialization and session management.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from collections.abc import AsyncGenerator
from pathlib import Path

import alembic.command
import alembic.config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

import backend.config

logger = logging.getLogger(__name__)

# SQLAlchemy declarative base for models
Base = declarative_base()

# Global engine and sessionmaker
# Note: These are global for single-instance applications.
# For multi-instance scenarios, consider using dependency injection.
engine: AsyncEngine | None = None
async_session_maker: async_sessionmaker[AsyncSession] | None = None


def init_db() -> None:
    """Initialize database engine and sessionmaker.

    This should be called once at application startup.
    Automatically runs migrations if database doesn't exist or alembic_version table is missing.

    Note: When called from async context (e.g., FastAPI lifespan), use init_db_async() instead
    to avoid blocking the event loop.
    """
    global engine, async_session_maker

    if engine is not None:
        return  # Already initialized

    settings = backend.config.get_settings()
    settings.ensure_app_dirs()
    database_url = settings.database_url_resolved

    # Create async engine
    engine = create_async_engine(database_url, echo=settings.debug)

    # Create sessionmaker
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Run migrations automatically if DB doesn't exist or alembic_version table is missing
    _run_migrations_if_needed(settings, database_url)


async def init_db_async() -> None:
    """Initialize database engine and sessionmaker asynchronously.

    This is the async version of init_db() that runs migrations in a threadpool
    to avoid blocking the event loop. Use this when called from async contexts
    like FastAPI lifespan.

    Automatically runs migrations if database doesn't exist or alembic_version table is missing.
    """
    global engine, async_session_maker

    if engine is not None:
        return  # Already initialized

    settings = backend.config.get_settings()
    settings.ensure_app_dirs()
    database_url = settings.database_url_resolved

    # Create async engine
    engine = create_async_engine(database_url, echo=settings.debug)

    # Create sessionmaker
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Run migrations in threadpool to avoid blocking event loop
    await asyncio.to_thread(_run_migrations_if_needed, settings, database_url)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection.

    Yields:
        AsyncSession: Database session

    Raises:
        RuntimeError: If database not initialized
    """
    if async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with async_session_maker() as session:
        # Enable foreign keys for SQLite
        await session.execute(text("PRAGMA foreign_keys=ON"))
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def _run_migrations_if_needed(settings: backend.config.Settings, database_url: str) -> None:
    """Run migrations if database doesn't exist or alembic_version table is missing.

    Args:
        settings: Application settings
        database_url: Database URL string
    """
    # Extract database file path from URL
    if database_url.startswith("sqlite"):
        # Handle sqlite:///path or sqlite+aiosqlite:///path
        db_path_str = database_url.split("///")[-1].split("?")[0]
        if db_path_str == ":memory:":
            # In-memory database always needs migrations
            _run_migrations_sync(settings, database_url)
            return
        db_path = Path(db_path_str)
    else:
        # For non-SQLite databases, always run migrations
        _run_migrations_sync(settings, database_url)
        return

    # Check if database file exists
    if not db_path.exists():
        _run_migrations_sync(settings, database_url)
        return

    # Check if alembic_version table exists
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
        has_version_table = cursor.fetchone() is not None
        conn.close()

        if not has_version_table:
            _run_migrations_sync(settings, database_url)
    except Exception:
        # If we can't check, run migrations to be safe
        _run_migrations_sync(settings, database_url)


def _run_migrations_sync(settings: backend.config.Settings, database_url: str) -> None:
    """Run migrations synchronously using Alembic command interface.

    Uses a synchronous SQLite engine for migrations to avoid asyncio conflicts.
    This allows migrations to run reliably even when called from async contexts.

    Migration failure behavior:
        - In production (debug=False): Fails fast with RuntimeError to prevent
          running with an unknown schema.
        - In development (debug=True): Logs warning and continues, allowing
          development to proceed even if migrations fail.

    Args:
        settings: Application settings (used for fail-fast behavior)
        database_url: Database URL string (may be async URL like sqlite+aiosqlite://)
    """
    backend_dir = Path(__file__).resolve().parent
    project_root = backend_dir.parent
    migrations_dir = backend_dir / "migrations"
    alembic_ini = migrations_dir / "alembic.ini"

    if not alembic_ini.exists():
        # If alembic.ini doesn't exist, skip migrations
        return

    # Convert async URL to sync URL for migrations
    # sqlite+aiosqlite:///path -> sqlite:///path
    sync_url = database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)

    cfg = alembic.config.Config(str(alembic_ini))
    cfg.set_main_option("prepend_sys_path", str(project_root))
    cfg.set_main_option("script_location", str(migrations_dir))
    cfg.set_main_option("sqlalchemy.url", sync_url)

    def _upgrade() -> None:
        try:
            alembic.command.upgrade(cfg, "head")
        except Exception as exc:
            # Fail-fast in production, warn-and-continue in dev
            if settings.debug:
                logger.warning("Failed to run automatic migrations on startup", exc_info=True)
                # In debug mode, continue despite migration failure
            else:
                logger.error("Failed to run automatic migrations on startup", exc_info=True)
                raise RuntimeError("Database migration failed") from exc

    # Always run synchronously - no threading needed since we use sync engine
    _upgrade()


async def close_db() -> None:
    """Close database connections.

    This should be called at application shutdown.
    """
    global engine, async_session_maker

    if engine is not None:
        await engine.dispose()
        engine = None
        async_session_maker = None
