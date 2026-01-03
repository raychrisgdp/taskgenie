"""Structured logging configuration with JSON formatter and redaction.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import json
import logging
import re
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from typing import Any

from backend.config import Settings, get_settings

# Context variable for request ID (set by middleware)
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# Sensitive keys to redact (case-insensitive)
SENSITIVE_KEYS = {"authorization", "token", "api_key", "password", "secret", "cookie", "set-cookie", "email"}

# Email regex pattern
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")


class JSONFormatter(logging.Formatter):
    """JSON log formatter with structured fields."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format.

        Returns:
            JSON string representation of the log record.
        """
        log_data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request_id (always include, null if not in request context)
        request_id = request_id_var.get()
        log_data["request_id"] = request_id

        # Add event type if present
        if hasattr(record, "event"):
            log_data["event"] = record.event

        # Add HTTP request fields if present
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "status"):
            log_data["status"] = record.status
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields (excluding already processed ones)
        excluded_keys = {"event", "method", "path", "status", "duration_ms"}
        for key, value in record.__dict__.items():
            if key not in excluded_keys and key not in {
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
            }:
                log_data[key] = value

        return json.dumps(log_data, default=str)


class RedactionFilter(logging.Filter):
    """Filter to redact sensitive information from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive data from log record.

        Args:
            record: Log record to filter.

        Returns:
            Always returns True (filter doesn't exclude records).
        """
        # Redact message
        if record.getMessage():
            record.msg = self._redact_string(str(record.msg))
            record.args = ()

        # Redact extra fields
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if isinstance(value, str):
                    # Redact if key is sensitive
                    if key.lower() in SENSITIVE_KEYS:
                        record.__dict__[key] = "[redacted]"
                    else:
                        # Redact emails from string values
                        record.__dict__[key] = self._redact_string(value)
                elif isinstance(value, dict):
                    record.__dict__[key] = self._redact_dict(value)
                elif isinstance(value, list):
                    record.__dict__[key] = [self._redact_value(item) for item in value]

        return True

    def _redact_string(self, value: str) -> str:
        """Redact emails from string.

        Args:
            value: String value to redact.

        Returns:
            String with emails replaced by [redacted-email].
        """
        return EMAIL_PATTERN.sub("[redacted-email]", value)

    def _redact_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive keys and values from dictionary.

        Args:
            data: Dictionary to redact.

        Returns:
            Dictionary with sensitive data redacted.
        """
        redacted: dict[str, Any] = {}
        for key, value in data.items():
            if key.lower() in SENSITIVE_KEYS:
                redacted[key] = "[redacted]"
            else:
                redacted[key] = self._redact_value(value)
        return redacted

    def _redact_value(self, value: Any) -> Any:
        """Redact sensitive data from any value type.

        Args:
            value: Value to redact.

        Returns:
            Redacted value.
        """
        if isinstance(value, str):
            return self._redact_string(value)
        if isinstance(value, dict):
            return self._redact_dict(value)
        if isinstance(value, list):
            return [self._redact_value(item) for item in value]
        return value


def setup_logging(settings: Settings | None = None) -> None:
    """Configure structured logging with JSON formatter and redaction.

    Args:
        settings: Application settings. If None, uses get_settings().
    """
    if settings is None:
        settings = get_settings()

    # Get log level
    log_level = settings.get_log_level()

    # Create formatter and filter
    formatter = JSONFormatter()
    redaction_filter = RedactionFilter()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(redaction_filter)
    root_logger.addHandler(console_handler)

    # File handler (always enabled; uses default path if LOG_FILE_PATH not set)
    log_file_path = settings.get_log_file_path()
    if log_file_path:
        # Ensure log directory exists
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Use RotatingFileHandler to avoid unbounded growth
        file_handler = RotatingFileHandler(
            str(log_file_path),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(redaction_filter)
        root_logger.addHandler(file_handler)
