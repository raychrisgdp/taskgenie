"""Tests for telemetry endpoint.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend import config, database
from backend.api.v1 import telemetry
from backend.main import app


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_telemetry_endpoint_returns_200(client: TestClient) -> None:
    """Test telemetry endpoint returns 200 status code."""
    await database.init_db_async()
    try:
        response = client.get("/api/v1/telemetry")
        assert response.status_code == 200
    finally:
        await database.close_db()


@pytest.mark.asyncio
async def test_telemetry_endpoint_includes_required_fields(
    client: TestClient,
) -> None:
    """Test telemetry endpoint includes all required fields."""
    await database.init_db_async()
    try:
        response = client.get("/api/v1/telemetry")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "uptime_s" in data
        assert "db" in data
        assert "optional" in data

        assert data["status"] in ("ok", "degraded")
        assert isinstance(data["version"], str)
        assert isinstance(data["uptime_s"], int)
        assert isinstance(data["db"], dict)
        assert isinstance(data["optional"], dict)
    finally:
        await database.close_db()


@pytest.mark.asyncio
async def test_telemetry_endpoint_db_health_connected(
    client: TestClient,
) -> None:
    """Test telemetry endpoint reports DB as connected when available."""
    await database.init_db_async()
    try:
        response = client.get("/api/v1/telemetry")
        assert response.status_code == 200

        data = response.json()
        assert data["db"]["connected"] is True
        assert "migration_version" in data["db"]
    finally:
        await database.close_db()


@pytest.mark.asyncio
async def test_telemetry_endpoint_migration_version(
    client: TestClient,
) -> None:
    """Test telemetry endpoint includes migration version."""
    await database.init_db_async()
    try:
        # Ensure migrations have run
        from backend.database import _run_migrations_if_needed

        settings = config.get_settings()
        db_url = settings.database_url_resolved
        _run_migrations_if_needed(settings, db_url)

        response = client.get("/api/v1/telemetry")
        assert response.status_code == 200

        data = response.json()
        assert data["db"]["migration_version"] is not None
        assert isinstance(data["db"]["migration_version"], str)
        assert len(data["db"]["migration_version"]) > 0
    finally:
        await database.close_db()


@pytest.mark.asyncio
async def test_telemetry_endpoint_optional_metrics_null(
    client: TestClient,
) -> None:
    """Test telemetry endpoint returns null for optional metrics."""
    await database.init_db_async()
    try:
        response = client.get("/api/v1/telemetry")
        assert response.status_code == 200

        data = response.json()
        assert data["optional"]["event_queue_size"] is None
        assert data["optional"]["agent_runs_active"] is None
    finally:
        await database.close_db()


@pytest.mark.asyncio
async def test_telemetry_endpoint_uptime_increases(
    client: TestClient,
) -> None:
    """Test telemetry endpoint uptime increases over time."""
    await database.init_db_async()
    try:
        import time

        response1 = client.get("/api/v1/telemetry")
        assert response1.status_code == 200
        uptime1 = response1.json()["uptime_s"]

        time.sleep(1)

        response2 = client.get("/api/v1/telemetry")
        assert response2.status_code == 200
        uptime2 = response2.json()["uptime_s"]

        assert uptime2 >= uptime1
    finally:
        await database.close_db()


@pytest.mark.asyncio
async def test_telemetry_endpoint_degraded_status_on_db_error(
    client: TestClient,
) -> None:
    """Test telemetry endpoint returns degraded status when DB check fails."""
    from collections.abc import AsyncGenerator

    from backend.api.v1 import telemetry

    # Mock get_db to return a session that raises on execute
    async def mock_get_db() -> AsyncGenerator[AsyncMock, None]:
        mock_session = AsyncMock()
        mock_execute = AsyncMock(side_effect=Exception("DB connection failed"))
        mock_session.execute = mock_execute
        yield mock_session

    # Override FastAPI dependency
    from backend.database import get_db

    app.dependency_overrides[get_db] = lambda: mock_get_db()
    try:
        response = client.get("/api/v1/telemetry")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "degraded"
        assert data["db"]["connected"] is False
        assert "error" in data["db"]
    finally:
        # Clean up override
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_migration_version_returns_version() -> None:
    """Test get_migration_version returns version when table exists."""
    await database.init_db_async()
    try:
        # Ensure migrations have run
        from backend.database import _run_migrations_if_needed

        settings = config.get_settings()
        db_url = settings.database_url_resolved
        _run_migrations_if_needed(settings, db_url)

        # Get a session
        async for db_session in database.get_db():
            version = await telemetry.get_migration_version(db_session)
            assert version is not None
            assert isinstance(version, str)
            break
    finally:
        await database.close_db()


@pytest.mark.asyncio
async def test_get_migration_version_returns_none_when_table_missing() -> None:
    """Test get_migration_version returns None when alembic_version table doesn't exist."""
    await database.init_db_async()
    try:
        async for db_session in database.get_db():
            # Drop alembic_version table if it exists
            await db_session.execute(text("DROP TABLE IF EXISTS alembic_version"))
            await db_session.commit()

            version = await telemetry.get_migration_version(db_session)
            assert version is None
            break
    finally:
        await database.close_db()
