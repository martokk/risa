"""
This module defines the Huey tasks for background job processing.
"""

from typing import Any

from app import logger, models
from app.core.huey import huey
from app.logic import job_runner


@huey.task(retries=1, retry_delay=10)
def execute_job_task(job_data: dict[str, Any]) -> None:
    """
    A Huey task to execute a job.

    This task deserializes the job data, updates its status,
    and then calls the main execution logic. It includes retry logic.

    Args:
        job_data: A dictionary representation of the job model.
    """
    try:
        # Deserialize the job data back into a Pydantic model
        job = models.Job(**job_data)

        # Log and update status to "running"
        logger.info(f"Starting execution for job {job.id}, retry {job.retry_count}")
        job.status = models.JobStatus.running

        # This is where you would typically update the job status in a persistent
        # storage if you need to track it outside of Huey's task lifecycle.
        # For now, we just log it.

        job_runner.execute_job(job)

        # If execution completes without error, mark as done
        job.status = models.JobStatus.done
        logger.info(f"Job {job.id} finished successfully.")

    except Exception as e:
        # On the final retry, the task will raise an unhandled exception
        # and be marked as "failed" by Huey.
        job.status = models.JobStatus.failed
        logger.error(f"Job {job.id} failed after retries. Error: {e}")
        # Increment retry count for the next attempt
        job.retry_count += 1
        # Re-raise the exception to trigger Huey's retry mechanism
        raise
