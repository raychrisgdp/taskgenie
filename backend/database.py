"""Database initialization and session management.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

import backend.config

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


async def close_db() -> None:
    """Close database connections.

    This should be called at application shutdown.
    """
    global engine, async_session_maker

    if engine is not None:
        await engine.dispose()
        engine = None
        async_session_maker = None
