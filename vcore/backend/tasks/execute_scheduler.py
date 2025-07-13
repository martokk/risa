from sqlmodel import Session

from app import logger, settings
from vcore.backend import crud, models
from vcore.backend.core.db import get_db_context


def _create_job_from_scheduler(db: Session, scheduler: models.JobScheduler) -> None:
    """Create a job from a scheduler's job_template."""
    try:
        job_data = models.JobCreate.model_validate(scheduler.job_template)
        job_data.name = f"Scheduled Job ({scheduler.trigger_type.value}): {scheduler.name}"
        crud.job.sync.create(db, obj_in=job_data)
        logger.info(f"Created job from scheduler: {scheduler.id} ({scheduler.name})")
    except Exception as e:
        logger.error(f"Failed to create job from scheduler {scheduler.id}: {e}")


def check_repeat_schedulers() -> None:
    """Check and run repeat job schedulers that are due."""
    with get_db_context() as db:
        ready_to_run = crud.job_scheduler.sync.get_repeat_schedulers_ready_to_run(  # type: ignore
            db, env_name=settings.ENV_NAME
        )
        for scheduler in ready_to_run:
            logger.info(f"Running repeat scheduler: {scheduler.id} ({scheduler.name})")
            _create_job_from_scheduler(db, scheduler)
            crud.job_scheduler.sync.update_last_run(db, scheduler_id=scheduler.id)  # type: ignore


def run_on_start_schedulers() -> None:
    """Run all on_start job schedulers."""
    with get_db_context() as db:
        on_start_schedulers = crud.job_scheduler.sync.get_on_start_schedulers(  # type: ignore
            db, env_name=settings.ENV_NAME
        )
        for scheduler in on_start_schedulers:
            _create_job_from_scheduler(db, scheduler)
            crud.job_scheduler.sync.update_last_run(db, scheduler_id=scheduler.id)  # type: ignore
