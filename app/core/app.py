from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from app import logger, settings, version
from app.api import deps
from app.core.db import initialize_tables_and_initial_data
from app.paths import STATIC_PATH
from app.routes.api import api_router
from app.routes.views import views_router
from app.services import notify
from app.services.status_updater import StatusUpdateService
from app.tasks.scheduler import TaskScheduler


# def run_playground_app():
#     subprocess.run(
#         [
#             "uvicorn",
#             "app.core.phidata_playground:app",
#             "--host",
#             "127.0.0.1",
#             "--port",
#             "7777",
#             "--reload",
#         ]
#     )


async def startup_event(db: Session | None = None) -> None:
    """
    Event handler that gets called when the application starts.
    Logs application start and creates database and tables if they do not exist.

    Args:
        db (Session): Database session.
    """
    logger.info("--- Start FastAPI ---")
    if settings.NOTIFY_ON_START:
        await notify.notify(text=f"{settings.PROJECT_NAME}('{settings.ENV_NAME}') started.")

    # Initialize database and tables if they do not exist
    if db is None:
        db = next(deps.get_db())
    await initialize_tables_and_initial_data(db=db)

    # Run status updater
    logger.info("Running status updater")
    status_updater = StatusUpdateService(db=db)
    await status_updater.update_grant_cycle_statuses()

    # Start the playground app in a separate thread
    # threading.Thread(target=run_playground_app).start()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    await startup_event()

    # Start task scheduler
    task_scheduler = TaskScheduler(app=app)
    await task_scheduler.register_startup_event()

    yield

    # Shutdown
    # scheduler_task.cancel()
    # with suppress(asyncio.CancelledError):
    # await scheduler_task


# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=version,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Include routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(views_router)

# Mount static and uploads directories
STATIC_PATH.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_PATH))
