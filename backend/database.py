from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base

Base = declarative_base()
engine: Any = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    raise NotImplementedError("Database wiring is not implemented yet.")
