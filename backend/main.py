"""TaskGenie backend entrypoint.

This branch keeps the backend as a skeleton; DB wiring/migrations land in PR-001.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import uvicorn
from fastapi import FastAPI

from .config import settings

app = FastAPI(title=settings.app_name, version=settings.app_version)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "version": settings.app_version}


def main() -> None:
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
    )


if __name__ == "__main__":
    main()
