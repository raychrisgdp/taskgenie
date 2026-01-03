"""Tests for request logging middleware.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import logging

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from backend.logging import request_id_var
from backend.middleware import RequestLoggingMiddleware, _is_safe_request_id

# UUID v4 format constants
UUID_LENGTH = 36  # UUID4 format: 8-4-4-4-12 hex digits = 36 chars total
UUID_DASH_COUNT = 4  # UUID4 has 4 dashes
HTTP_OK = status.HTTP_200_OK


def test_is_safe_request_id_valid() -> None:
    """Test _is_safe_request_id accepts valid request IDs."""
    assert _is_safe_request_id("abc123") is True
    assert _is_safe_request_id("a" * 128) is True
    assert _is_safe_request_id("test-request-id-123") is True


def test_is_safe_request_id_too_long() -> None:
    """Test _is_safe_request_id rejects request IDs that are too long."""
    assert _is_safe_request_id("a" * 129) is False


def test_is_safe_request_id_non_ascii() -> None:
    """Test _is_safe_request_id rejects non-ASCII request IDs."""
    assert _is_safe_request_id("café") is False
    assert _is_safe_request_id("测试") is False


@pytest.fixture
def test_app() -> FastAPI:
    """Create test FastAPI app with middleware."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/error")
    async def error_endpoint() -> None:
        raise ValueError("Test error")

    app.add_middleware(RequestLoggingMiddleware)
    return app


def test_middleware_generates_request_id(test_app: FastAPI) -> None:
    """Test middleware generates UUID4 when X-Request-Id header is missing."""
    client = TestClient(test_app)
    response = client.get("/test")

    assert response.status_code == HTTP_OK
    assert "X-Request-Id" in response.headers
    # UUID4 format: 8-4-4-4-12 hex digits
    request_id = response.headers["X-Request-Id"]
    assert len(request_id) == UUID_LENGTH
    assert request_id.count("-") == UUID_DASH_COUNT


def test_middleware_reuses_safe_request_id(test_app: FastAPI) -> None:
    """Test middleware reuses X-Request-Id header when safe."""
    client = TestClient(test_app)
    response = client.get("/test", headers={"X-Request-Id": "test-id-123"})

    assert response.status_code == HTTP_OK
    assert response.headers["X-Request-Id"] == "test-id-123"


def test_middleware_rejects_unsafe_request_id(test_app: FastAPI) -> None:
    """Test middleware generates new ID when X-Request-Id is unsafe."""
    client = TestClient(test_app)
    # Too long - TestClient allows this
    response1 = client.get("/test", headers={"X-Request-Id": "a" * 129})

    assert response1.status_code == HTTP_OK
    # Should generate new UUID, not reuse unsafe one
    assert response1.headers["X-Request-Id"] != "a" * 129
    assert len(response1.headers["X-Request-Id"]) == UUID_LENGTH

    # Non-ASCII - TestClient rejects this before middleware, so test the function directly
    # This is already covered by test_is_safe_request_id_non_ascii


def test_middleware_logs_request(caplog: pytest.LogCaptureFixture, test_app: FastAPI) -> None:
    """Test middleware logs http_request event with correct fields."""
    # Ensure the middleware logger level is set to INFO and propagates
    middleware_logger = logging.getLogger("backend.middleware")
    middleware_logger.setLevel(logging.INFO)
    middleware_logger.propagate = True

    # Also ensure root logger level is set
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    with caplog.at_level(logging.INFO):
        client = TestClient(test_app)
        response = client.get("/test")

    assert response.status_code == HTTP_OK

    # Find the http_request log
    request_logs = [r for r in caplog.records if hasattr(r, "event") and r.event == "http_request"]
    assert len(request_logs) == 1

    log = request_logs[0]
    assert log.event == "http_request"
    assert log.method == "GET"
    assert log.path == "/test"
    assert log.status == HTTP_OK
    assert hasattr(log, "duration_ms")
    assert isinstance(log.duration_ms, (int, float))


def test_middleware_logs_error(caplog: pytest.LogCaptureFixture, test_app: FastAPI) -> None:
    """Test middleware logs http_error event for unhandled exceptions."""
    # Ensure the middleware logger level is set to ERROR and propagates
    middleware_logger = logging.getLogger("backend.middleware")
    middleware_logger.setLevel(logging.ERROR)
    middleware_logger.propagate = True

    # Also ensure root logger level is set
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.ERROR)

    with caplog.at_level(logging.ERROR):
        client = TestClient(test_app)
        try:
            client.get("/error")
        except Exception:
            pass  # Expected to raise

    # Find the http_error log
    error_logs = [r for r in caplog.records if hasattr(r, "event") and r.event == "http_error"]
    assert len(error_logs) >= 1

    log = error_logs[0]
    assert log.event == "http_error"
    assert log.method == "GET"
    assert log.path == "/error"


def test_middleware_sets_request_id_in_context(test_app: FastAPI) -> None:
    """Test middleware sets request_id in context variable."""
    app = FastAPI()

    @app.get("/test-context")
    async def test_context() -> dict[str, str | None]:
        request_id = request_id_var.get()
        return {"request_id": request_id}

    app.add_middleware(RequestLoggingMiddleware)
    client = TestClient(app)

    response = client.get("/test-context", headers={"X-Request-Id": "test-context-id"})
    assert response.status_code == HTTP_OK
    assert response.json()["request_id"] == "test-context-id"
