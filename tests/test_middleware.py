"""Tests for request logging middleware.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import logging
from collections.abc import Generator

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from backend.logging import request_id_var
from backend.middleware import RequestLoggingMiddleware, _is_safe_request_id

# UUID v4 format constants
UUID_LENGTH = 36  # UUID4 format: 8-4-4-4-12 hex digits = 36 chars total
UUID_DASH_COUNT = 4  # UUID4 has 4 dashes
HTTP_OK = status.HTTP_200_OK

# Configure middleware logger at module level to ensure it's set before tests run
# This ensures logs are captured even when running with coverage in parallel
_middleware_logger = logging.getLogger("backend.middleware")
_middleware_logger.setLevel(logging.DEBUG)
_middleware_logger.propagate = True
# Also ensure root logger level is set so logs propagate correctly
_root_logger = logging.getLogger()
_root_logger.setLevel(logging.DEBUG)


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


class LogCaptureHandler(logging.Handler):
    """Custom handler to capture logs for testing."""

    def __init__(self) -> None:
        """Initialize handler."""
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Capture log record."""
        self.records.append(record)

    def clear(self) -> None:
        """Clear captured records."""
        self.records.clear()


@pytest.fixture
def log_handler() -> Generator[LogCaptureHandler, None, None]:
    """Fixture to provide a custom log handler for tests."""
    handler = LogCaptureHandler()
    handler.setLevel(logging.DEBUG)

    middleware_logger = logging.getLogger("backend.middleware")
    middleware_logger.addHandler(handler)
    middleware_logger.setLevel(logging.DEBUG)
    middleware_logger.propagate = True

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    yield handler

    # Cleanup
    middleware_logger.removeHandler(handler)


@pytest.fixture
def test_app() -> FastAPI:
    """Create test FastAPI app with middleware."""
    # Ensure middleware logger is configured before middleware runs
    middleware_logger = logging.getLogger("backend.middleware")
    middleware_logger.setLevel(logging.DEBUG)  # Set to DEBUG to ensure all logs are captured
    middleware_logger.propagate = True

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


def test_middleware_logs_request(test_app: FastAPI, log_handler: LogCaptureHandler) -> None:
    """Test middleware logs http_request event with correct fields."""
    # Clear handler records and ensure handler is attached right before request
    log_handler.clear()
    middleware_logger = logging.getLogger("backend.middleware")
    if log_handler not in middleware_logger.handlers:
        middleware_logger.addHandler(log_handler)
    middleware_logger.setLevel(logging.DEBUG)
    middleware_logger.propagate = True

    # Make request - logger should be configured now
    client = TestClient(test_app)
    response = client.get("/test")

    assert response.status_code == HTTP_OK

    # Find the http_request log
    request_logs = [r for r in log_handler.records if hasattr(r, "event") and r.event == "http_request"]
    assert len(request_logs) == 1

    log = request_logs[0]
    assert log.event == "http_request"  # type: ignore[attr-defined]
    assert log.method == "GET"  # type: ignore[attr-defined]
    assert log.path == "/test"  # type: ignore[attr-defined]
    assert log.status == HTTP_OK  # type: ignore[attr-defined]
    assert hasattr(log, "duration_ms")
    assert isinstance(log.duration_ms, (int, float))  # type: ignore[arg-type]


def test_middleware_logs_error(test_app: FastAPI, log_handler: LogCaptureHandler) -> None:
    """Test middleware logs http_error event for unhandled exceptions."""
    # Clear handler records and ensure handler is attached right before request
    log_handler.clear()
    middleware_logger = logging.getLogger("backend.middleware")
    if log_handler not in middleware_logger.handlers:
        middleware_logger.addHandler(log_handler)
    middleware_logger.setLevel(logging.DEBUG)
    middleware_logger.propagate = True

    # Make request - logger should be configured now
    client = TestClient(test_app)
    try:
        client.get("/error")
    except Exception:
        pass  # Expected to raise

    # Find the http_error log
    error_logs = [r for r in log_handler.records if hasattr(r, "event") and r.event == "http_error"]
    assert len(error_logs) >= 1

    log = error_logs[0]
    assert log.event == "http_error"  # type: ignore[attr-defined]
    assert log.method == "GET"  # type: ignore[attr-defined]
    assert log.path == "/error"  # type: ignore[attr-defined]


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
