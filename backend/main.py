import uvicorn
from .config import settings
from .database import engine
from .models.task import Task
from .models.attachment import Attachment
from .models.notification import Notification

from .database import Base

from .models.task import Task as TaskModel
from .models.attachment import Attachment as AttachmentModel
from .models.notification import Notification as NotificationModel


@asynccontextmanager
async def lifespan(app):
    from .models.task import Task
    from .models.attachment import Attachment
    from .models.notification import Notification

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


from fastapi import FastAPI

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.app_version}


def main():
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
    )


if __name__ == "__main__":
    main()
