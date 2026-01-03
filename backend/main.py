"""TaskGenie backend entrypoint.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.api.v1 import tasks as tasks_router, telemetry
from backend.config import get_settings
from backend.database import close_db, init_db_async
from backend.logging import setup_logging
from backend.middleware import RequestLoggingMiddleware
from backend.schemas.task import ErrorResponse
from backend.services.task_service import TaskNotFoundError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifespan events."""
    # Startup
    settings = get_settings()
    settings.ensure_app_dirs()
    setup_logging(settings)  # Setup structured logging
    await init_db_async()  # Use async version to avoid blocking event loop
    yield
    # Shutdown
    await close_db()


settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Register API routers
app.include_router(tasks_router.router, prefix="/api/v1")

# Register telemetry router if enabled
if settings.telemetry_enabled:
    app.include_router(telemetry.router, prefix="/api/v1", tags=["telemetry"])


@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(request: Request, exc: TaskNotFoundError) -> JSONResponse:
    """Handle TaskNotFoundError exceptions.

    Args:
        request: FastAPI request object.
        exc: TaskNotFoundError exception.

    Returns:
        JSONResponse: 404 response with error details.
    """
    error_response = ErrorResponse(error="Task not found", code=exc.code)
    return JSONResponse(status_code=404, content=error_response.model_dump())


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "version": get_settings().app_version}


def main() -> None:
    """Main entry point for the backend server."""
    settings = get_settings()
    # Logging is now configured via setup_logging() in lifespan
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
