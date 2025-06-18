"""
This module defines the Huey tasks for background job processing.
"""

import subprocess
from datetime import datetime, timezone
from uuid import uuid4

import requests
from huey import crontab
from sqlmodel import Session

from app import logger, paths
from framework import crud, models
from framework.core.db import get_db_context
from framework.core.huey import huey
from framework.services import job_queue


def run_command_job(db: Session, db_job: models.Job) -> None:
    """
    Executes a command-line job using subprocess and logs output in real-time.

    Args:
        job: The job to execute.
    """
    log_file_name = f"job_{db_job.id}_retry_{db_job.retry_count}.txt"
    log_path = paths.JOB_LOGS_PATH / log_file_name

    # Ensure the logs directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Open the log file for writing
        with open(log_path, "w") as log_file:
            # Execute the command and stream output in real-time
            process = subprocess.Popen(
                db_job.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Redirect stderr to stdout
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True,
            )

            # Update the job with the PID
            db_job.pid = process.pid
            logger.info(f"Job `{db_job.id}` started with PID `{db_job.pid}`")

            crud.job.update(db, obj_in=models.JobUpdate(pid=db_job.pid), db_obj=db_job)

            # Read and write output in real-time
            if process.stdout:
                for line in process.stdout:
                    log_file.write(line)
                    log_file.flush()  # Ensure immediate writing to disk
                    logger.debug(f"Job {db_job.id} output: {line.strip()}")

            # Wait for the process to complete
            return_code = process.wait()

            if return_code == 0:
                logger.info(f"Job `{db_job.id}` executed successfully.")
            else:
                error_msg = f"Job `{db_job.id}` failed with exit code `{return_code}`"
                logger.error(error_msg)
                raise subprocess.CalledProcessError(return_code, db_job.command)

    except subprocess.CalledProcessError as e:
        logger.error(f"Job `{db_job.id}` failed: {str(e)}")

        with open(log_path, "a") as log_file:
            log_file.write(f"Job `{db_job.id}` failed: {str(e)}\n")
        raise  # Re-raise the exception to be caught by the Huey task
    except Exception as e:
        logger.error(f"Unexpected error in job `{db_job.id}`: {str(e)}")
        raise


def run_api_post_job(job: models.Job) -> None:  # TODO: Not implemented yet (dummy code)
    """
    Executes an API POST job using requests.

    Args:
        job: The job to execute.
    """
    try:
        response = requests.post(job.command, json=job.meta)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        output = response.text
        logger.info(f"API POST job {job.id} executed successfully.")
    except requests.exceptions.RequestException as e:
        output = f"Error executing API POST job: {str(e)}"
        logger.error(f"API POST job {job.id} failed: {output}")
        raise  # Re-raise
    except Exception as e:
        output = f"An unexpected error occurred: {str(e)}"
        logger.error(f"Unexpected error in API POST job {job.id}: {output}")
        raise


@huey.task()
def execute_job_task(job_id: str, priority: int = 100) -> None:
    """
    Huey task to execute a job and update its status.
    This is the entry point for background job execution.
    Version: 5
    """
    logger.info("\n\n\n")
    logger.info(f"--- HUEY CONSUMER: EXECUTING JOB TASK (v5) for job_id: {job_id} ---")

    with get_db_context() as db:
        db_job = crud.job.get(db, id=job_id)

    logger.info(f"Job Name: {db_job.name if db_job else 'None'}")

    if not db_job:
        logger.error(f"Huey Consumer could not find job with ID: {job_id}. Aborting task.")
        return

    job_succeeded = False
    try:
        logger.info(f"Executing job {db_job.id} of type {db_job.type.value}")
        if db_job.type == models.JobType.command:
            try:
                run_command_job(db=db, db_job=db_job)
                job_succeeded = True
            except Exception as e:
                if "died with <Signals.SIGKILL: 9>" in str(e):
                    logger.error(f"Job {db_job.id} was killed by SIGKILL signal")
                    # Handle SIGKILL specifically - could add custom handling here

                    # Update Status
                    with get_db_context() as db:
                        obj_in = models.JobUpdate(status=models.JobStatus.pending)
                        db_job = crud.job.update(db, db_obj=db_job, obj_in=obj_in)

                    job_succeeded = False
                else:
                    raise  # Re-raise other exceptions
        elif db_job.type == models.JobType.api_post:
            run_api_post_job(db_job)
            job_succeeded = True
        logger.info(f"Job {db_job.id} execution part finished.")

    except Exception as e:
        logger.error(f"Job {db_job.id} failed with exception: {e}", exc_info=True)

        # Update Status
        with get_db_context() as db:
            obj_in = models.JobUpdate(status=models.JobStatus.failed)
            db_job = crud.job.update(db, db_obj=db_job, obj_in=obj_in)

    finally:
        if job_succeeded:
            logger.info(f"Job {db_job.id} succeeded. Updating status to 'done'.")

            # Update Status
            with get_db_context() as db:
                obj_in = models.JobUpdate(status=models.JobStatus.done)
                db_job = crud.job.update(db, db_obj=db_job, obj_in=obj_in)

        logger.info(f"--- HUEY CONSUMER: FINISHED JOB TASK (v5) for job {db_job.id} ---")


@huey.periodic_task(crontab(minute="0"))  # TODO: NOT IMPLEMENTED YET
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
                    "created_at": datetime.now(tz=timezone.utc),
                    "retry_count": 0,
                }
            )
            job_queue.add_job_to_queue(new_job)


@huey.periodic_task(crontab(minute="0", hour="0"))  # TODO: NOT IMPLEMENTED YET
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
                    "created_at": datetime.now(tz=timezone.utc),
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
