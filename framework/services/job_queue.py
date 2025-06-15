"""
This service manages the job queue, providing an interface to add,
view, and manage jobs in a persistent, file-based database (TinyDB).
"""

import asyncio
import os
import signal
import subprocess
from typing import Any

from tinydb import Query, TinyDB

from app import logger, paths
from framework import schemas
from framework.services.job_queue_ws_manager import job_queue_ws_manager
from framework.tasks import job_tasks


# Initialize the TinyDB database for jobs
db = TinyDB(paths.JOB_DB_PATH)

HUEY_PID_FILE = paths.DATA_PATH / "huey_consumer.pid"


async def broadcast_consumer_status(status: str) -> None:
    await job_queue_ws_manager.broadcast(
        {
            "consumer_status": status,
        }
    )


def add_job_to_queue(job: schemas.Job) -> schemas.Job:
    """
    Adds a new job to the persistent job database.

    Args:
        job: The job model instance to save.

    Returns:
        The job model instance that was saved.
    """
    logger.info(f"Adding job {job.id} to the job database.")
    db.insert(job.model_dump(mode="json"))
    return job


def get_all_jobs() -> list[schemas.Job]:
    """
    Retrieves a list of all jobs from the database.
    """
    all_jobs_data = db.all()
    return [schemas.Job(**job_data) for job_data in all_jobs_data]


def get_job_by_id(job_id: str) -> schemas.Job | None:
    """
    Retrieves a single job by its ID.
    """
    JobQuery = Query()
    job_data = db.get(JobQuery.id == job_id)
    if job_data:
        return schemas.Job(**job_data)
    return None


def update_job_status(job_id: str, status: schemas.JobStatus) -> None:
    """
    Updates the status of a single job in a robust way.

    Args:
        job_id: The ID of the job to update.
        status: The new status to set.
    """
    logger.info(f"Updating status for job {job_id} to {status.value}")
    job_doc = db.get(Query().id == job_id)

    if job_doc:
        # Load the document into a Pydantic model
        job = schemas.Job(**job_doc)
        # Update the status
        job.status = status
        # Write the entire updated object back to the DB
        db.upsert(job.model_dump(mode="json"), Query().id == job_id)

        logger.info(f"Successfully updated status for job {job_id}")

        loop = asyncio.get_event_loop()
        if loop.is_running():
            coro = job_queue_ws_manager.broadcast(
                {
                    "jobs": [j.model_dump(mode="json") for j in get_all_jobs()],
                    "consumer_status": "running" if is_consumer_running() else "stopped",
                }
            )
            asyncio.ensure_future(coro)
        else:
            loop.run_until_complete(
                job_queue_ws_manager.broadcast(
                    {
                        "jobs": [j.model_dump(mode="json") for j in get_all_jobs()],
                        "consumer_status": "running" if is_consumer_running() else "stopped",
                    }
                )
            )

        logger.info(
            f"Successfully broadcasted job status update for job {job_id} to {status.value}"
        )
    else:
        logger.warning(f"Could not find job {job_id} to update status.")


def remove_job_from_queue(job_id: str) -> bool:
    """
    Removes a job from the database.
    """
    JobQuery = Query()
    result = db.remove(JobQuery.id == job_id)
    return len(result) > 0


def trigger_next_job() -> schemas.Job | None:
    """
    Finds the next job to run based on priority, and enqueues it in Huey.

    This function is the bridge between the persistent job list and the
    Huey task queue. It is called by the idle watcher.
    """
    # This is a simplified priority queue. For a large number of jobs,
    # a more efficient querying method would be needed.
    all_jobs = get_all_jobs()

    # Filter for queued jobs
    queued_jobs = [j for j in all_jobs if j.status == schemas.JobStatus.queued]
    if not queued_jobs:
        return None

    # Sort by priority: high -> medium -> low
    priority_order = {schemas.Priority.high: 0, schemas.Priority.normal: 1, schemas.Priority.low: 2}
    queued_jobs.sort(key=lambda j: priority_order[j.priority])

    next_job = queued_jobs[0]

    logger.info(
        f"Triggering next job from queue: {next_job.id} with priority {next_job.priority.value}"
    )

    # Enqueue the job for execution in the background
    job_tasks.execute_job_task(job_data=next_job.model_dump(), priority=next_job.priority.value)

    # Update the job's status to "queued" in Huey (or "running" conceptually)
    # update_job_status(str(next_job.id), models.JobStatus.running)

    return next_job


async def update_job(job_id: str, job_in: schemas.Job | schemas.JobUpdate) -> schemas.Job | None:
    """
    Updates a job in the database.

    Args:
        job_id: The ID of the job to update.
        job_in: The job model with the updated data.

    Returns:
        The updated job model instance, or None if not found.
    """
    logger.info(f"Updating job {job_id} in the job database.")
    update_data = job_in.model_dump(mode="json", exclude_unset=True)

    # Ensure ID is not part of the update data itself
    update_data.pop("id", None)

    updated_ids = db.update(update_data, Query().id == job_id)

    if len(updated_ids) > 0:
        return get_job_by_id(job_id)
    return None


def is_consumer_running() -> bool:
    is_running = False
    if HUEY_PID_FILE.exists():
        try:
            with open(HUEY_PID_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)  # Check if process exists

            is_running = True
        except ProcessLookupError:
            logger.warning("PID file exists, but process does not.")
            os.remove(HUEY_PID_FILE)
            is_running = False
        except Exception as e:
            logger.error(f"Error checking Huey consumer process: {e}")
            is_running = False
    else:
        is_running = False

    loop = asyncio.get_event_loop()
    if loop.is_running():
        coro = job_queue_ws_manager.broadcast(
            {
                "consumer_status": "running" if is_running else "stopped",
            }
        )
        asyncio.ensure_future(coro)
    else:
        loop.run_until_complete(
            job_queue_ws_manager.broadcast(
                {
                    "consumer_status": "running" if is_running else "stopped",
                }
            )
        )

    return is_running


async def start_consumer_process() -> dict[str, Any]:
    """
    Start the Huey consumer process as a detached background process using nohup.
    Redirect output to app/data/logs/huey_consumer.log and write the PID to HUEY_PID_FILE.
    Returns a dict with success and message.
    """
    log_path = paths.DATA_PATH / "logs" / "huey_consumer.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    if is_consumer_running():
        return {"success": False, "message": "Huey consumer is already running."}
    try:
        cwd = os.getcwd()
        # Build the command string
        cmd = (
            f"nohup poetry run huey_consumer app.tasks.huey --worker-type=process"
            f"> {log_path} 2>&1 & echo $!"
        )
        # Start the process and capture the PID
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=os.environ.copy(),
        )
        pid_bytes, _ = proc.communicate()
        pid = pid_bytes.decode().strip()

        # Add a small delay to ensure process is fully started
        await asyncio.sleep(0.5)

        with open(HUEY_PID_FILE, "w") as f:
            f.write(pid)
        await broadcast_consumer_status("running")
        return {"success": True, "message": f"Huey consumer started with PID {pid}."}
    except Exception as e:
        return {"success": False, "message": f"Failed to start consumer: {e}"}


async def stop_consumer_process() -> dict[str, Any]:
    """
    Stop the Huey consumer process if running.
    Returns a dict with success and message.
    """
    if not HUEY_PID_FILE.exists():
        print("HUEY_PID_FILE does not exist")
        await broadcast_consumer_status("stopped")
        return {"success": False, "message": "Huey consumer is not running."}
    try:
        with open(HUEY_PID_FILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, signal.SIGTERM)
        os.remove(HUEY_PID_FILE)
        print("HUEY_PID_FILE removed")
        await broadcast_consumer_status("stopped")
        return {"success": True, "message": f"Huey consumer with PID {pid} stopped."}
    except Exception as e:
        return {"success": False, "message": f"Failed to stop consumer: {e}"}


def kill_job_process(job_id: str) -> dict[str, Any]:
    """Immediately kill a running job process by its PID.

    Args:
        job_id: The ID of the job to kill.

    Returns:
        Dict with 'success' and 'message'.
    """
    db.storage.read()
    job = get_job_by_id(job_id)
    if not job:
        return {"success": False, "message": f"Job {job_id} not found."}
    pid = job.pid
    if not pid:
        update_job_status(job_id, schemas.JobStatus.pending)
        return {"success": False, "message": f"No PID found for job {job_id}."}
    try:
        os.kill(int(pid), signal.SIGKILL)

        update_job_status(job_id, schemas.JobStatus.pending)

        return {"success": True, "message": f"Job {job_id} (PID {pid}) killed."}
    except ProcessLookupError:
        update_job_status(job_id, schemas.JobStatus.pending)
        return {"success": True, "message": f"Job {job_id} (PID {pid}) not found."}
    except Exception as e:
        return {"success": False, "message": f"Failed to kill job {job_id}: {e}"}
