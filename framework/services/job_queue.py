"""
This service manages the job queue, providing an interface to add,
view, and manage jobs in a persistent, file-based database (TinyDB).
"""

import asyncio
import os
import signal
import subprocess
from typing import Any

from sqlmodel import Session

from app import logger, paths
from framework import crud, models
from framework.services.job_queue_ws_manager import job_queue_ws_manager
from framework.tasks import execute_tasks


HUEY_PID_FILE = paths.DATA_PATH / "huey_consumer.pid"


async def broadcast_consumer_status(status: str) -> None:
    await job_queue_ws_manager.broadcast(
        {
            "consumer_status": status,
        }
    )


async def trigger_next_job(db: Session) -> models.Job | None:
    """
    Finds the next job to run based on priority, and enqueues it in Huey.

    This function is the bridge between the persistent job list and the
    Huey task queue. It is called by the idle watcher.
    """
    # This is a simplified priority queue. For a large number of jobs,
    # a more efficient querying method would be needed.
    all_jobs = await crud.job.get_all(db)

    # Filter for queued jobs
    queued_jobs = [j for j in all_jobs if j.status == models.JobStatus.queued]
    if not queued_jobs:
        return None

    # Sort by priority: high -> medium -> low
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
        f"Triggering next job from queue: {next_job.id} with priority {next_job.priority.value}"
    )

    # Enqueue the job for execution in the background, passing only the ID
    execute_tasks.execute_job_task(
        job_id=str(next_job.id), priority=priority_order[next_job.priority]
    )

    return next_job


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

    job_queue_ws_manager.broadcast(
        {
            "consumer_status": "running" if is_running else "stopped",
        }
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

        # Append "\n Starting consumer..." to the log file
        with open(log_path, "a") as f:
            f.write("\n Starting consumer...")

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
    log_path = paths.DATA_PATH / "logs" / "huey_consumer.log"

    if not HUEY_PID_FILE.exists():
        print("HUEY_PID_FILE does not exist")

        # Append "\n Stopping consumer..." to the log file
        with open(log_path, "a") as f:
            f.write("\n Stopping consumer...")

        await broadcast_consumer_status("stopped")
        return {"success": False, "message": "Huey consumer is not running."}
    try:
        with open(HUEY_PID_FILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, signal.SIGTERM)
        os.remove(HUEY_PID_FILE)
        print("HUEY_PID_FILE removed")

        # Append "\n Stopping consumer..." to the log file
        with open(log_path, "a") as f:
            f.write("\n Stopping consumer...")

        await broadcast_consumer_status("stopped")
        return {"success": True, "message": f"Huey consumer with PID {pid} stopped."}
    except Exception as e:
        return {"success": False, "message": f"Failed to stop consumer: {e}"}


async def kill_job_process(job_id: str, db: Session) -> dict[str, Any]:
    """Immediately kill a running job process by its PID.

    Args:
        job_id: The ID of the job to kill.

    Returns:
        Dict with 'success' and 'message'.
    """
    job = await crud.job.get_or_none(db, id=job_id)
    if not job:
        return {"success": False, "message": f"Job {job_id} not found."}
    pid = job.pid
    if not pid:
        await crud.job.update(
            db, id=job_id, obj_in=models.JobUpdate(status=models.JobStatus.pending)
        )
        return {"success": False, "message": f"No PID found for job {job_id}."}
    try:
        os.kill(int(pid), signal.SIGKILL)

        await crud.job.update(
            db, id=job_id, obj_in=models.JobUpdate(status=models.JobStatus.pending)
        )

        return {"success": True, "message": f"Job {job_id} (PID {pid}) killed."}
    except ProcessLookupError:
        await crud.job.update(
            db, id=job_id, obj_in=models.JobUpdate(status=models.JobStatus.pending)
        )
        return {"success": True, "message": f"Job {job_id} (PID {pid}) not found."}
    except Exception as e:
        return {"success": False, "message": f"Failed to kill job {job_id}: {e}"}
