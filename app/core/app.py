import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from app import logger, settings
from app.logic.state import update_instance_state
from app.paths import STATIC_PATH
from app.routes.api import api_router
from app.routes.views import views_router
from app.services.idle_watcher import start_idle_watcher, stop_idle_watcher
from framework.core.db import get_db, initialize_tables_and_initial_data
from framework.services import notify


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


async def periodic_instance_state_update() -> None:
    """Periodically update the instance state."""
    while True:
        try:
            logger.info("Updating instance state...")
            await update_instance_state()
            logger.info("Instance state updated.")
        except Exception as e:
            logger.error(f"Error updating instance state: {e}")
        await asyncio.sleep(5 * 60)  # 5 minutes


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
        db = next(get_db())
    await initialize_tables_and_initial_data(db=db)

    # Start the playground app in a separate thread
    # threading.Thread(target=run_playground_app).start()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    await startup_event()
    start_idle_watcher()

    # Start the periodic task
    update_task = asyncio.create_task(periodic_instance_state_update())

    yield

    # Shutdown
    stop_idle_watcher()
    update_task.cancel()
    with suppress(asyncio.CancelledError):
        await update_task


# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
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
