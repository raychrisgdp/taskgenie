"""Request logging middleware with correlation IDs.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.logging import request_id_var

logger = logging.getLogger(__name__)

# Maximum length for request ID header (per spec)
MAX_REQUEST_ID_LENGTH = 128


def _is_safe_request_id(request_id: str) -> bool:
    """Check if request ID is safe (length <= MAX_REQUEST_ID_LENGTH, ASCII).

    Args:
        request_id: Request ID string to validate.

    Returns:
        True if safe, False otherwise.
    """
    if len(request_id) > MAX_REQUEST_ID_LENGTH:
        return False
    try:
        request_id.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request logging with correlation IDs."""

    def __init__(self, app: ASGIApp) -> None:
        """Initialize middleware.

        Args:
            app: ASGI application.
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process request and log with correlation ID.

        Args:
            request: FastAPI request object.
            call_next: Next middleware/handler in chain.

        Returns:
            Response object.
        """
        # Get or generate request ID
        request_id_header = request.headers.get("X-Request-Id")
        if request_id_header and _is_safe_request_id(request_id_header):
            request_id = request_id_header
        else:
            request_id = str(uuid.uuid4())

        # Set request ID in context
        request_id_var.set(request_id)

        # Start timer
        start_time = time.time()

        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
            exception = None
        except Exception as exc:
            status_code = 500
            exception = exc
            raise
        finally:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log request
            logger.info(
                "HTTP request",
                extra={
                    "event": "http_request",
                    "method": request.method,
                    "path": request.url.path,
                    "status": status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            # Log error if exception occurred
            if exception:
                logger.error(
                    "HTTP error",
                    extra={
                        "event": "http_error",
                        "method": request.method,
                        "path": request.url.path,
                        "status": status_code,
                    },
                    exc_info=exception,
                )

        # Add request ID to response headers
        response.headers["X-Request-Id"] = request_id

        return response
