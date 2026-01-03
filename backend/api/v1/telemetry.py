"""Telemetry endpoint for system health and metrics.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.database import get_db

# Track app start time for uptime calculation
_app_start_time = time.time()

router = APIRouter()


async def get_migration_version(db: AsyncSession) -> str | None:
    """Get current Alembic migration version from database.

    Args:
        db: Database session.

    Returns:
        Migration version string or None if table doesn't exist or query fails.
    """
    try:
        result = await db.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
        row = result.fetchone()
        if row:
            return str(row[0])
        return None
    except Exception:
        # Table doesn't exist or query failed
        return None


async def check_db_health(db: AsyncSession) -> tuple[bool, str | None]:
    """Check database connectivity.

    Args:
        db: Database session.

    Returns:
        Tuple of (connected: bool, error: str | None).
    """
    try:
        await db.execute(text("SELECT 1"))
        return True, None
    except Exception as exc:
        return False, str(exc)


@router.get("/telemetry")
async def get_telemetry(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Get system telemetry and health metrics.

    Returns:
        JSON object with status, version, uptime, DB health, and optional metrics.
        Always returns 200 status code; status is reported in payload.
    """
    settings = get_settings()

    # Check DB health
    db_connected, db_error = await check_db_health(db)

    # Get migration version
    migration_version = await get_migration_version(db)

    # Calculate uptime
    uptime_s = int(time.time() - _app_start_time)

    # Determine overall status
    status = "ok" if db_connected else "degraded"

    # Build response
    response: dict[str, Any] = {
        "status": status,
        "version": settings.app_version,
        "uptime_s": uptime_s,
        "db": {"connected": db_connected, "migration_version": migration_version},
        "optional": {
            "event_queue_size": None,  # PR-013 not implemented
            "agent_runs_active": None,  # PR-014 not implemented
        },
    }

    # Add error message if degraded
    if not db_connected and db_error:
        response["db"]["error"] = db_error

    return response
