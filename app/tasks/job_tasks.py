"""
This module defines the Huey tasks for background job processing.
"""

from datetime import datetime
from uuid import uuid4

import httpx
from huey import crontab
from tinydb import TinyDB

from app import logger, models, paths, settings
from app.core.huey import huey
from app.logic import job_runner
from app.services import job_queue


# Initialize the TinyDB database for jobs
db = TinyDB(paths.JOB_DB_PATH)


def post_job_status_update(job_id: str, status: str) -> None:
    print(f"POSTing job status update for job {job_id} to {status}...")
    with httpx.Client() as client:
        response = client.put(
            f"{settings.BASE_URL}{settings.API_V1_PREFIX}/jobs/{job_id}/status",
            json={"status": status},
        )
        print(f"Response: {response.status_code}")


@huey.task()
def execute_job_task(job_id: str, priority: int = 100) -> None:
    """
    Huey task to execute a job and update its status.
    This is the entry point for background job execution.
    Version: 5
    """
    logger.info("\n\n\n")
    logger.info(f"--- HUEY WORKER: EXECUTING JOB TASK (v5) for job_id: {job_id} ---")

    # Immediately update status to 'running' as the first step.
    # job_queue.update_job_status(job_id, models.JobStatus.running)
    try:
        print("Updating job status to 'running' and broadcasting...")
        post_job_status_update(job_id, models.JobStatus.running.value)
        logger.info(f"Successfully updated job {job_id} status to 'running' and broadcasted.")
    except Exception as e:
        logger.error(f"Failed to broadcast running status: {e}")

    job = job_queue.get_job_by_id(job_id)

    logger.info(f"Job Name: {job.name if job else 'None'}")

    if not job:
        logger.error(f"Huey worker could not find job with ID: {job_id}. Aborting task.")
        return

    job_succeeded = False
    try:
        logger.info(f"Executing job {job.id} of type {job.type.value}")
        if job.type == models.JobType.command:
            try:
                job_runner.run_command_job(job)
                job_succeeded = True
            except Exception as e:
                if "died with <Signals.SIGKILL: 9>" in str(e):
                    logger.error(f"Job {job.id} was killed by SIGKILL signal")
                    # Handle SIGKILL specifically - could add custom handling here
                    post_job_status_update(str(job.id), models.JobStatus.pending.value)
                    job_succeeded = False
                else:
                    raise  # Re-raise other exceptions
        elif job.type == models.JobType.api_post:
            job_runner.run_api_post_job(job)
            job_succeeded = True
        logger.info(f"Job {job.id} execution part finished.")

    except Exception as e:
        logger.error(f"Job {job.id} failed with exception: {e}", exc_info=True)
        # job_queue.update_job_status(str(job.id), models.JobStatus.failed)
        try:
            post_job_status_update(str(job.id), models.JobStatus.failed.value)
        except Exception as e:
            logger.error(f"Failed to broadcast failed status: {e}")

    finally:
        if job_succeeded:
            logger.info(f"Job {job.id} succeeded. Updating status to 'done'.")
            # job_queue.update_job_status(str(job.id), models.JobStatus.done)
            try:
                post_job_status_update(str(job.id), models.JobStatus.done.value)
            except Exception as e:
                logger.error(f"Failed to broadcast done status: {e}")
        logger.info(f"--- HUEY WORKER: FINISHED JOB TASK (v5) for job {job.id} ---")


@huey.periodic_task(crontab(minute="0"))
def enqueue_hourly_jobs():
    """
    Periodically executed task to enqueue jobs marked as "hourly".
    """
    logger.info("Checking for hourly recurring jobs...")
    all_jobs = job_queue.get_all_jobs()
    for job in all_jobs:
        if job.recurrence == "hourly":
            logger.info(f"Spawning new job from recurring hourly job: {job.id}")
            # Spawn a new job instance, don't re-add the same one.
            new_job = job.model_copy(
                update={
                    "id": uuid4(),  # Generate a new ID
                    "status": models.JobStatus.queued,
                    "recurrence": None,  # The spawned job is not recurring
                    "created_at": datetime.now(),
                    "retry_count": 0,
                }
            )
            job_queue.add_job_to_queue(new_job)


@huey.periodic_task(crontab(minute="0", hour="0"))
def enqueue_daily_jobs():
    """
    Periodically executed task to enqueue jobs marked as "daily".
    """
    logger.info("Checking for daily recurring jobs...")
    all_jobs = job_queue.get_all_jobs()
    for job in all_jobs:
        if job.recurrence == "daily":
            logger.info(f"Spawning new job from recurring daily job: {job.id}")
            # Spawn a new job instance, don't re-add the same one.
            new_job = job.model_copy(
                update={
                    "id": uuid4(),  # Generate a new ID
                    "status": models.JobStatus.queued,
                    "recurrence": None,  # The spawned job is not recurring
                    "created_at": datetime.now(),
                    "retry_count": 0,
                }
            )
            job_queue.add_job_to_queue(new_job)


@huey.periodic_task(crontab(minute="0"))
def spawn_recurring_jobs() -> None:
    """
    Periodically executed task to enqueue jobs marked as "hourly" or "daily".
    """
    logger.info("Checking for hourly and daily recurring jobs...")
    enqueue_hourly_jobs()
    enqueue_daily_jobs()
