"""
This service manages the job queue, providing an interface to add,
view, and manage jobs in the Huey task queue.
"""

from app import logger, models
from app.tasks import job_tasks


def add_job_to_queue(job: models.Job) -> models.Job:
    """
    Adds a new job to the Huey task queue.

    This function takes a Job model, serializes it, and enqueues it
    as a background task.

    Args:
        job: The job model instance to enqueue.

    Returns:
        The job model instance that was enqueued.
    """
    logger.info(f"Adding job {job.id} to the queue with priority {job.priority.value}")

    # Enqueue the job execution task with the specified priority by passing it
    # as a keyword argument directly to the task's invocation.
    job_tasks.execute_job_task(job_data=job.model_dump(), priority=job.priority.value)

    return job


def get_all_jobs() -> list[models.Job]:
    """
    Retrieves a list of all jobs from the Huey queue.

    NOTE: This is a simplified implementation. A real-world application
    would need a more robust way to query job status, likely involving
    a separate database to track job states, as Huey's API for
    querying scheduled tasks is limited.

    For now, this will return a placeholder.
    """
    logger.warning("get_all_jobs is a placeholder and does not fetch real jobs from Huey.")
    return []


def get_job_by_id(job_id: str) -> models.Job | None:
    """
    Retrieves a single job by its ID.

    NOTE: Placeholder implementation, similar to get_all_jobs.
    """
    logger.warning(f"get_job_by_id for {job_id} is a placeholder.")
    return None


def cancel_job(job_id: str) -> bool:
    """
    Cancels a job in the queue.

    NOTE: Placeholder implementation. True cancellation requires interacting
    with Huey's storage and is non-trivial.
    """
    logger.warning(f"cancel_job for {job_id} is a placeholder.")
    return True
