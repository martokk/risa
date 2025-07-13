"""
This module defines the Huey tasks for background job processing.
"""

import json
import subprocess
import traceback
from datetime import datetime, timezone
from uuid import uuid4

import requests
from huey import crontab
from sqlmodel import Session

from app import logger, paths, settings
from app.tasks.execute_tasks import hook_get_script_class_from_class_name
from vcore.backend import crud, models
from vcore.backend.core.db import get_db_context
from vcore.backend.core.huey import huey_default, huey_reserved
from vcore.backend.logic.jobs import push_jobs_to_websocket
from vcore.backend.tasks.execute_scheduler import check_repeat_schedulers


def _trigger_next_queued_job(queue_name: str) -> None:
    """
    Finds the next queued job and triggers it for execution.
    This function is called after a job completes to ensure continuous processing.
    """
    logger.info("--- HUEY CONSUMER: Checking for next queued job ---")

    with get_db_context() as db:
        # Get all jobs and filter for queued status
        all_jobs = crud.job.sync.get_all_jobs_for_env_name(
            db, env_name=settings.ENV_NAME, queue_name=queue_name
        )
        queued_jobs = [j for j in all_jobs if j.status == models.JobStatus.queued]

        if not queued_jobs:
            logger.debug("No queued jobs found. Waiting for new jobs...")
            return

        # Sort by priority: highest -> high -> normal -> low -> lowest
        priority_order = {
            models.job.Priority.highest: 0,
            models.job.Priority.high: 1,
            models.job.Priority.normal: 2,
            models.job.Priority.low: 3,
            models.job.Priority.lowest: 4,
        }
        queued_jobs.sort(key=lambda j: priority_order[j.priority])

        next_job = queued_jobs[0]

        logger.info(
            f"Triggering next job from queue: {next_job.id} ({next_job.name}) "
            f"with priority {next_job.priority.value}"
        )

        # Enqueue the job for execution in Huey
        _execute_job_task(job_id=str(next_job.id), priority=priority_order[next_job.priority])


def _run_command_job(db: Session, db_job: models.Job, command: str | None = None) -> None:
    """
    Executes a command-line job using subprocess and logs output in real-time.

    Args:
        job: The job to execute.
    """
    logger.debug(f"\nJob {str(db_job.id)[:8]}: Recieved run_command_job() request.")

    log_file_name = f"job_{db_job.id}_retry_{db_job.retry_count}.txt"
    log_path = paths.JOB_LOGS_PATH / log_file_name

    # Ensure the logs directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Open the log file for writing
        with open(log_path, "w") as log_file:
            # Execute the command and stream output in real-time
            process = subprocess.Popen(
                command or db_job.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Redirect stderr to stdout
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True,
            )

            # Update the job with the PID
            db_job.pid = process.pid
            logger.info(f"Job {str(db_job.id)[:8]}: Job started with PID {db_job.pid}")

            crud.job.sync.update(db, obj_in=models.JobUpdate(pid=db_job.pid), id=db_job.id)

            # Read and write output in real-time
            if process.stdout:
                for line in process.stdout:
                    log_file.write(line)
                    log_file.flush()  # Ensure immediate writing to disk
                    logger.debug(f"Job {str(db_job.id)[:8]}: OUTPUT: {line.strip()}")

            # Wait for the process to complete
            return_code = process.wait()

            if return_code == 0:
                logger.info(f"Job {str(db_job.id)[:8]}: SUCCESSFULLY COMPLETED")
            else:
                error_msg = f"Job {str(db_job.id)[:8]}: FAILED: exit code {return_code}"
                logger.error(error_msg)
                raise subprocess.CalledProcessError(return_code, command or db_job.command)

    except subprocess.CalledProcessError as e:
        logger.error(f"Job {str(db_job.id)[:8]}: FAILED: {str(e)}")

        with open(log_path, "a") as log_file:
            log_file.write(f"Job {str(db_job.id)[:8]}: FAILED: {str(e)}\n")
        raise  # Re-raise the exception to be caught by the Huey task
    except Exception as e:
        logger.error(f"Job {str(db_job.id)[:8]}: UNEXPECTED ERROR: {str(e)}")
        raise


def _run_script_job(db_job: models.Job) -> None:
    """
    Executes a script job using the script class.
    """
    logger.debug(f"Job {str(db_job.id)[:8]}: Recieved run_script_job() request.")

    log_file_name = f"job_{db_job.id}_retry_{db_job.retry_count}.txt"
    log_path = paths.JOB_LOGS_PATH / log_file_name

    # Ensure the logs directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Open the log file for writing
    with open(log_path, "w") as log_file:
        script_class_name = db_job.command
        log_file.write(f"job_id: {str(db_job.id)}\n")
        log_file.write(f"script_class_name: {script_class_name}\n")
        log_file.write(f"meta: \n{json.dumps(db_job.meta, indent=4)}\n")
        log_file.write("----------------------------------------\n\n")

        # Get scripts from the app: app.tasks.execute_tasks.py via hook
        script_class = hook_get_script_class_from_class_name(script_class_name=script_class_name)

        try:
            db_job.meta["job_id"] = str(db_job.id)
            script_output = script_class().run(**db_job.meta)
        except Exception as e:
            log_file.write(f"Error: {e}\n Traceback: {traceback.format_exc()}\n")
            raise e

        log_file.write(
            f"Output: \n\n success: {script_output.success}\n message: {script_output.message}\n data: \n{json.dumps(script_output.data, indent=4)}\n"
        )

    logger.info(f"Script {script_class_name} \noutput: {script_output}")


def _run_api_post_job(job: models.Job) -> None:  # TODO: Not implemented yet (dummy code)
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


def _safe_push_jobs_to_websocket(context_msg: str = "") -> None:
    try:
        push_jobs_to_websocket()
        logger.info(f"[WebSocket] Successfully pushed jobs to websocket. {context_msg}")
    except Exception as e:
        logger.error(f"[WebSocket] Failed to push jobs to websocket. {context_msg} Error: {e}")


def _execute_job_task(job_id: str, priority: int = 100) -> None:
    """
    Huey task to execute a job and update its status.
    This is the entry point for background job execution.
    Version: 7 - Added proper status management and race condition protection
    """
    logger.info("\n\n\n")
    logger.info(f"--- EXECUTING JOB: {job_id} ---")

    with get_db_context() as db:
        # First, try to claim the job by updating its status to "running"
        # This prevents race conditions where multiple consumers might try to run the same job
        db_job = crud.job.sync.get(db, id=job_id)

        logger.info(f"Job {str(db_job.id)[:8]}: Name: {db_job.name}")

        if not db_job:
            logger.error(f"Huey Consumer could not find job with ID: {job_id}. Aborting task.")
            return

        # Check if job is still in queued status (race condition protection)
        if db_job.status != models.JobStatus.queued:
            logger.warning(
                f"Job {str(db_job.id)[:8]}: Job is not in queued status (current: {db_job.status}). "
                f"Another consumer may be processing it. Aborting task."
            )
            return

        # Atomically update job status to "running" to claim it
        try:
            obj_in = models.JobUpdate(status=models.JobStatus.running)
            db_job = crud.job.sync.update(db, db_obj=db_job, obj_in=obj_in)
            _safe_push_jobs_to_websocket(f"Job {db_job.id}: status set to running")
            logger.debug(
                f"Job {str(db_job.id)[:8]}: Status updated to 'running' - job claimed for execution"
            )
        except Exception as e:
            logger.error(f"Job {str(db_job.id)[:8]}: Failed to update status to 'running': {e}")
            return

        job_succeeded = False
        try:
            logger.info(f"Job {str(db_job.id)[:8]}: Starting execution...")
            if db_job.type == models.JobType.command:
                try:
                    _run_command_job(db=db, db_job=db_job)
                    job_succeeded = True
                except Exception as e:
                    if "died with <Signals.SIGKILL: 9>" in str(e):
                        logger.error(f"Job {str(db_job.id)[:8]}: KILLED by SIGKILL signal")
                        # Handle SIGKILL specifically - could add custom handling here

                        obj_in = models.JobUpdate(status=models.JobStatus.pending)
                        db_job = crud.job.sync.update(db, db_obj=db_job, obj_in=obj_in)
                        _safe_push_jobs_to_websocket(
                            f"Job {db_job.id}: status set to pending (SIGKILL)"
                        )

                        job_succeeded = False
                    else:
                        raise  # Re-raise other exceptions
            elif db_job.type == models.JobType.api_post:
                _run_api_post_job(db_job)
                job_succeeded = True
            elif db_job.type == models.JobType.script:
                _run_script_job(db_job)
                job_succeeded = True

        except requests.exceptions.Timeout as e:
            logger.error(f"Job {db_job.id}: REQUEST TIMEOUT: {e}", exc_info=True)

            # Update Status to error
            obj_in = models.JobUpdate(status=models.JobStatus.error)
            db_job = crud.job.sync.update(db, db_obj=db_job, obj_in=obj_in)
            _safe_push_jobs_to_websocket(f"Job {db_job.id}: status set to error (timeout)")

        except Exception as e:
            logger.error(f"\nJob {db_job.id}: FAILED: {e}", exc_info=True)

            # Update Status to failed
            obj_in = models.JobUpdate(status=models.JobStatus.failed)
            db_job = crud.job.sync.update(db, db_obj=db_job, obj_in=obj_in)
            _safe_push_jobs_to_websocket(f"Job {db_job.id}: status set to failed (exception)")

        finally:
            if job_succeeded:
                # Update Status to done
                obj_in = models.JobUpdate(status=models.JobStatus.done)
                db_job = crud.job.sync.update(db, db_obj=db_job, obj_in=obj_in)
                _safe_push_jobs_to_websocket(f"Job {db_job.id}: status set to done (success)")

                logger.debug(f"Job {str(db_job.id)[:8]}: Updated status to 'done'.")

            logger.info(f"--- FINISHED JOB: {str(db_job.id)[:8]} ---\n\n\n")

            # Trigger the next queued job after this one completes
            _trigger_next_queued_job(queue_name=db_job.queue_name)


def _check_and_process_queued_jobs(queue_name: str) -> None:
    """
    Periodic task that checks for queued jobs and triggers them for processing.
    This ensures that jobs get processed even if the trigger_next_queued_job()
    mechanism fails or if jobs are added while no jobs are running.
    """
    logger.info(f"--- HUEY CONSUMER: Periodic check for queued jobs ({queue_name}) ---")

    with get_db_context() as db:
        # Check if there are any running jobs
        all_jobs = crud.job.sync.get_all_jobs_for_env_name(
            db, env_name=settings.ENV_NAME, queue_name=queue_name
        )
        running_jobs = [j for j in all_jobs if j.status == models.JobStatus.running]

        # If no jobs are running, check for queued jobs
        if not running_jobs:
            queued_jobs = [j for j in all_jobs if j.status == models.JobStatus.queued]
            if queued_jobs:
                logger.info(
                    f"Found {len(queued_jobs)} queued jobs with no running jobs. Triggering next job."
                )
                _trigger_next_queued_job(queue_name=queue_name)
            else:
                logger.debug("No running jobs and no queued jobs found.")
        else:
            logger.debug(f"Found {len(running_jobs)} running job(s). Skipping queued job check.")


def _cleanup_stuck_jobs(queue_name: str) -> None:
    """
    Periodic task that checks for jobs that have been 'running' for too long
    and may be stuck. This helps recover from situations where a job process
    died but the status wasn't updated.
    """
    logger.info("--- HUEY CONSUMER: Checking for stuck jobs ---")

    with get_db_context() as db:
        all_jobs = crud.job.sync.get_all_jobs_for_env_name(
            db, env_name=settings.ENV_NAME, queue_name=queue_name
        )
        running_jobs = [j for j in all_jobs if j.status == models.JobStatus.running]

        for job in running_jobs:
            # Check if the process is still running
            if job.pid:
                try:
                    import os

                    os.kill(job.pid, 0)  # Check if process exists
                    logger.debug(f"Job {job.id} with PID {job.pid} is still running")
                except OSError:
                    # Process is no longer running, but status wasn't updated
                    logger.warning(
                        f"Job {job.id} has PID {job.pid} but process is not running. Marking as failed."
                    )
                    obj_in = models.JobUpdate(status=models.JobStatus.failed)
                    crud.job.sync.update(db, db_obj=job, obj_in=obj_in)
            else:
                # Job has no PID but is marked as running - this shouldn't happen
                logger.warning(
                    f"Job {job.id} is marked as running but has no PID. Marking as failed."
                )
                obj_in = models.JobUpdate(status=models.JobStatus.failed)
                crud.job.sync.update(db, db_obj=job, obj_in=obj_in)


def _enqueue_hourly_jobs(queue_name: str) -> None:
    """
    Periodically executed task to enqueue jobs marked as "hourly".
    """
    logger.info("Checking for hourly recurring jobs...")
    with get_db_context() as db:
        all_jobs = crud.job.sync.get_all_jobs_for_env_name(
            db, env_name=settings.ENV_NAME, queue_name=queue_name
        )
        for job in all_jobs:
            if job.recurrence == "hourly":
                logger.info(f"Spawning new job from recurring hourly job: {job.id}")
                # Spawn a new job instance, don't re-add the same one.
                new_job_data = job.model_copy(
                    update={
                        "id": uuid4(),  # Generate a new ID
                        "status": models.JobStatus.queued,
                        "recurrence": None,  # The spawned job is not recurring
                        "created_at": datetime.now(tz=timezone.utc),
                        "retry_count": 0,
                    }
                )
                new_job_create = models.JobCreate.model_validate(new_job_data)
                crud.job.sync.create(db, obj_in=new_job_create)


def _enqueue_daily_jobs(queue_name: str) -> None:
    """
    Periodically executed task to enqueue jobs marked as "daily".
    """
    logger.info("Checking for daily recurring jobs...")
    with get_db_context() as db:
        all_jobs = crud.job.sync.get_all_jobs_for_env_name(
            db, env_name=settings.ENV_NAME, queue_name=queue_name
        )
        for job in all_jobs:
            if job.recurrence == "daily":
                logger.info(f"Spawning new job from recurring daily job: {job.id}")
                # Spawn a new job instance, don't re-add the same one.
                new_job_data = job.model_copy(
                    update={
                        "id": uuid4(),  # Generate a new ID
                        "status": models.JobStatus.queued,
                        "recurrence": None,  # The spawned job is not recurring
                        "created_at": datetime.now(tz=timezone.utc),
                        "retry_count": 0,
                    }
                )
                new_job_create = models.JobCreate.model_validate(new_job_data)
                crud.job.sync.create(db, obj_in=new_job_create)


def _spawn_recurring_jobs(queue_name: str) -> None:
    """
    Periodically executed task to enqueue jobs marked as "hourly" or "daily".
    """
    logger.info("Checking for hourly and daily recurring jobs...")
    _enqueue_hourly_jobs(queue_name=queue_name)
    _enqueue_daily_jobs(queue_name=queue_name)


@huey_default.task()
def execute_job_task_default(job_id: str, priority: int = 100) -> None:
    _execute_job_task(job_id=job_id, priority=priority)


@huey_reserved.task()
def execute_job_task_reserved(job_id: str, priority: int = 100) -> None:
    _execute_job_task(job_id=job_id, priority=priority)


@huey_default.periodic_task(crontab(minute="*/1"))  # Check every 1 minute
def check_and_process_queued_jobs_default() -> None:
    _check_and_process_queued_jobs(queue_name="default")


@huey_default.periodic_task(crontab(minute="*/1"))  # Check every 1 minute
def check_and_process_job_schedulers() -> None:
    check_repeat_schedulers()


@huey_reserved.periodic_task(crontab(minute="*/1"))  # Check every 1 minute
def check_and_process_queued_jobs_reserved() -> None:
    _check_and_process_queued_jobs(queue_name="reserved")


@huey_default.periodic_task(crontab(minute="*/5"))  # Check every 5 minutes
def cleanup_stuck_jobs_default() -> None:
    _cleanup_stuck_jobs(queue_name="default")


@huey_reserved.periodic_task(crontab(minute="*/5"))
def cleanup_stuck_jobs_reserved() -> None:
    _cleanup_stuck_jobs(queue_name="reserved")


@huey_default.periodic_task(crontab(minute="0"), queue_name="default")  # TODO: NOT IMPLEMENTED YET
def enqueue_hourly_jobs_default() -> None:
    _enqueue_hourly_jobs(queue_name="default")


@huey_reserved.periodic_task(
    crontab(minute="0"), queue_name="reserved"
)  # TODO: NOT IMPLEMENTED YET
def enqueue_hourly_jobs_reserved() -> None:
    _enqueue_hourly_jobs(queue_name="reserved")


@huey_default.periodic_task(
    crontab(minute="0", hour="0"), queue_name="default"
)  # TODO: NOT IMPLEMENTED YET
def enqueue_daily_jobs_default() -> None:
    _enqueue_daily_jobs(queue_name="default")


@huey_reserved.periodic_task(crontab(minute="0", hour="0"), queue_name="reserved")
def enqueue_daily_jobs_reserved() -> None:
    _enqueue_daily_jobs(queue_name="reserved")


@huey_default.periodic_task(crontab(minute="0"))
def spawn_recurring_jobs_default() -> None:
    _spawn_recurring_jobs(queue_name="default")


@huey_reserved.periodic_task(crontab(minute="0"))
def spawn_recurring_jobs_reserved() -> None:
    _spawn_recurring_jobs(queue_name="reserved")
