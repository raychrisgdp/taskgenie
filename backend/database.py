"""Database scaffolding (skeleton).

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import declarative_base

Base = declarative_base()
engine: AsyncEngine | None = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database session generator.

    Intentionally unimplemented in this branch. PR-001 introduces database initialization,
    migrations, and session lifecycle wiring.
    """

    raise NotImplementedError("Database wiring is not implemented yet (see PR-001).")
