"""Tests for structured logging configuration.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest
from fastapi import status

from backend import config
from backend.logging import JSONFormatter, RedactionFilter, request_id_var, setup_logging

HTTP_OK = status.HTTP_200_OK
EXPECTED_DURATION_MS = 123.45
MIN_HANDLERS_WITH_FILE = 2


def test_json_formatter_basic_fields() -> None:
    """Test JSONFormatter includes all required basic fields."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test.logger", level=logging.INFO, pathname="test.py", lineno=1, msg="Test message", args=(), exc_info=None
    )
    record.created = 1609459200.0  # 2021-01-01 00:00:00 UTC

    output = formatter.format(record)
    data = json.loads(output)

    assert data["timestamp"] == "2021-01-01T00:00:00+00:00"
    assert data["level"] == "INFO"
    assert data["logger"] == "test.logger"
    assert data["message"] == "Test message"
    assert data["request_id"] is None  # Always present, null when not in request context


def test_json_formatter_with_request_id() -> None:
    """Test JSONFormatter includes request_id when set in context."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test.logger", level=logging.INFO, pathname="test.py", lineno=1, msg="Test message", args=(), exc_info=None
    )
    record.created = 1609459200.0

    # Set request ID in context
    token = request_id_var.set("test-request-id-123")
    try:
        output = formatter.format(record)
        data = json.loads(output)
        assert data["request_id"] == "test-request-id-123"
    finally:
        request_id_var.reset(token)


def test_json_formatter_with_event() -> None:
    """Test JSONFormatter includes event field when present."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test.logger", level=logging.INFO, pathname="test.py", lineno=1, msg="HTTP request", args=(), exc_info=None
    )
    record.created = 1609459200.0
    record.event = "http_request"  # type: ignore[attr-defined]
    record.method = "GET"  # type: ignore[attr-defined]
    record.path = "/api/v1/tasks"  # type: ignore[attr-defined]
    record.status = 200  # type: ignore[attr-defined]
    record.duration_ms = 123.45  # type: ignore[attr-defined]

    output = formatter.format(record)
    data = json.loads(output)

    assert data["event"] == "http_request"
    assert data["method"] == "GET"
    assert data["path"] == "/api/v1/tasks"
    assert data["status"] == HTTP_OK
    assert data["duration_ms"] == EXPECTED_DURATION_MS


def test_redaction_filter_sensitive_keys() -> None:
    """Test RedactionFilter redacts sensitive keys."""
    filter_obj = RedactionFilter()
    record = logging.LogRecord(
        name="test.logger", level=logging.INFO, pathname="test.py", lineno=1, msg="Test message", args=(), exc_info=None
    )
    record.authorization = "Bearer secret-token"  # type: ignore[attr-defined]
    record.password = "mypassword123"  # type: ignore[attr-defined]
    record.email = "user@example.com"  # type: ignore[attr-defined]

    filter_obj.filter(record)

    assert record.authorization == "[redacted]"  # type: ignore[attr-defined]
    assert record.password == "[redacted]"  # type: ignore[attr-defined]
    assert record.email == "[redacted]"  # type: ignore[attr-defined]


def test_redaction_filter_email_in_strings() -> None:
    """Test RedactionFilter redacts email addresses in string values."""
    filter_obj = RedactionFilter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="User email is user@example.com",
        args=(),
        exc_info=None,
    )

    filter_obj.filter(record)

    assert "[redacted-email]" in record.msg
    assert "user@example.com" not in record.msg


def test_redaction_filter_nested_dict() -> None:
    """Test RedactionFilter handles nested dictionaries."""
    filter_obj = RedactionFilter()
    record = logging.LogRecord(
        name="test.logger", level=logging.INFO, pathname="test.py", lineno=1, msg="Test message", args=(), exc_info=None
    )
    record.data = {"user": {"email": "user@example.com", "token": "secret123"}}  # type: ignore[attr-defined]

    filter_obj.filter(record)

    assert record.data["user"]["email"] == "[redacted]"  # type: ignore[attr-defined]
    assert record.data["user"]["token"] == "[redacted]"  # type: ignore[attr-defined]


def test_setup_logging_configures_handlers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test setup_logging configures handlers correctly."""
    monkeypatch.setenv("TASKGENIE_DATA_DIR", str(tmp_path))
    config.get_settings.cache_clear()

    setup_logging()

    root_logger = logging.getLogger()
    handlers = root_logger.handlers

    # Should have at least console handler
    assert len(handlers) >= 1
    assert any(isinstance(h, logging.StreamHandler) for h in handlers)


def test_setup_logging_creates_file_handler(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test setup_logging creates file handler when log_file_path is set."""
    log_file = tmp_path / "test.jsonl"
    monkeypatch.setenv("TASKGENIE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("LOG_FILE_PATH", str(log_file))
    config.get_settings.cache_clear()

    setup_logging()

    root_logger = logging.getLogger()
    handlers = root_logger.handlers

    # Should have both console and file handler
    assert len(handlers) >= MIN_HANDLERS_WITH_FILE
    assert any(isinstance(h, logging.handlers.RotatingFileHandler) for h in handlers)
    assert log_file.parent.exists()


def test_setup_logging_respects_log_level(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test setup_logging respects configured log level."""
    monkeypatch.setenv("TASKGENIE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    config.get_settings.cache_clear()

    setup_logging()

    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG
