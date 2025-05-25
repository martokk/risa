from datetime import UTC, datetime, time

from fastapi import FastAPI
from sqlmodel import Session

from app import logger
from app.core.db import get_db
from app.services.status_updater import StatusUpdateService


class TaskScheduler:
    """Scheduler for background tasks."""

    def __init__(self, app: FastAPI):
        self.app = app
        self.logger = logger
        self._last_status_update: datetime | None = None

    async def schedule_status_updates(self) -> None:
        """Schedule the status update task."""
        try:
            # Get database session
            db: Session = next(get_db())

            # Create service
            status_updater = StatusUpdateService(db=db)

            # Run the update
            await status_updater.update_grant_cycle_statuses()

            # Update last run time
            self._last_status_update = datetime.now(UTC)

            self.logger.info("Successfully completed scheduled status updates")

        except Exception as e:
            self.logger.error(f"Error running scheduled status updates: {str(e)}")
            raise
        finally:
            db.close()

    def should_run_status_update(self) -> bool:
        """Check if status update should run based on time and last run."""
        now = datetime.now(UTC)
        target_time = time(hour=7, minute=0)  # 7:00 AM UTC

        # If never run, should run
        if not self._last_status_update:
            return True

        # If not run today and it's past target time, should run
        if self._last_status_update.date() < now.date() and now.time() >= target_time:
            return True

        return False

    async def register_startup_event(self) -> None:
        """Register and run the startup event handler."""
        try:
            # Check if we need to run status updates
            if self.should_run_status_update():
                await self.schedule_status_updates()
        except Exception as e:
            self.logger.error(f"Error in startup event: {str(e)}")
            raise
