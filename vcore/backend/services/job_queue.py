"""
This service manages the job queue, providing an interface to add,
view, and manage jobs in a persistent, file-based database (TinyDB).
"""

import asyncio
import os
import shutil
import signal
import subprocess
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from sqlmodel import Session

from app import logger, paths
from app.logic.config import get_config
from vcore.backend import crud, models
from vcore.backend.services.job_queue_ws_manager import job_queue_ws_manager


class HueyConsumerWorker(BaseModel):
    name: str
    db_path: Path
    log_path: Path
    pid_file: Path
    huey_module: str


CONSUMERS: list[HueyConsumerWorker] = [
    HueyConsumerWorker(
        name="default",
        db_path=paths.HUEY_DEFAULT_DB_PATH,
        log_path=paths.HUEY_DEFAULT_LOG_PATH,
        pid_file=paths.HUEY_DEFAULT_PID_FILE,
        huey_module="app.tasks.huey_default",
    ),
    HueyConsumerWorker(
        name="reserved",
        db_path=paths.HUEY_RESERVED_DB_PATH,
        log_path=paths.HUEY_RESERVED_LOG_PATH,
        pid_file=paths.HUEY_RESERVED_PID_FILE,
        huey_module="app.tasks.huey_reserved",
    ),
]


async def broadcast_consumer_status(status: str) -> None:
    try:
        await job_queue_ws_manager.broadcast(
            {
                "consumer_status": status,
            }
        )
    except Exception as e:
        logger.error(f"Failed to broadcast consumer status: {e}")


def is_consumer_running(queue_name: str) -> bool:
    consumer = next((c for c in CONSUMERS if c.name == queue_name), None)
    if not consumer:
        return False
    pid_file = Path(consumer.pid_file)

    if pid_file.exists():
        try:
            with open(pid_file) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            logger.warning(f"PID file {pid_file} exists, but process does not.")
            os.remove(pid_file)
            return False
        except Exception as e:
            logger.error(f"Error checking consumer process {consumer.name}: {e}")
            return False
    return False


async def start_huey_consumers_on_start() -> None:
    """Start Huey consumers on start."""
    config = get_config()
    if not config.jobs.start_huey_consumers_on_start:
        return
    for consumer in CONSUMERS:
        if not is_consumer_running(queue_name=consumer.name):
            await start_consumer_process(queue_name=consumer.name)


async def start_consumer_process(queue_name: str | None = None) -> dict[str, Any]:
    """Start Huey consumer process for the specified queue or all if not specified.

    Args:
        queue_name: Name of the queue to start (default, reserved), or None for all.

    Returns:
        Dict with 'results' (list of per-queue results).
    """
    results = []
    consumers = [c for c in CONSUMERS if queue_name is None or c.name == queue_name]
    if not consumers:
        raise ValueError(f"No consumers found for queue_name: {queue_name}")
    for consumer in consumers:
        log_path = Path(consumer.log_path)
        pid_file = Path(consumer.pid_file)
        huey_module = consumer.huey_module
        log_path.parent.mkdir(parents=True, exist_ok=True)
        if is_consumer_running(queue_name=consumer.name):
            results.append(
                {"success": False, "message": f"{consumer.name} consumer already running."}
            )
            continue
        try:
            cwd = os.getcwd()
            which_poetry = shutil.which("poetry")
            cmd = f"nohup {'poetry run ' if which_poetry else ''}huey_consumer {huey_module} --worker-type=process > {log_path} 2>&1 & echo $!"  # noqa: E501
            with open(log_path, "a") as f:
                f.write(f"\n Starting {consumer.name} consumer...")
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
            await asyncio.sleep(0.5)
            with open(pid_file, "w") as f:
                f.write(pid)
            results.append(
                {"success": True, "message": f"{consumer.name} consumer started with PID {pid}."}
            )
        except Exception as e:
            results.append(
                {"success": False, "message": f"Failed to start {consumer.name} consumer: {e}"}
            )
    await broadcast_consumer_status_for_all()
    return {"results": results}


async def stop_consumer_process(queue_name: str | None = None) -> dict[str, Any]:
    """Stop Huey consumer process for the specified queue or all if not specified.

    Args:
        queue_name: Name of the queue to stop (default, reserved), or None for all.

    Returns:
        Dict with 'results' (list of per-queue results).
    """
    results = []
    consumers = [c for c in CONSUMERS if queue_name is None or c.name == queue_name]
    if not consumers:
        raise ValueError(f"No consumers found for queue_name: {queue_name}")
    for consumer in consumers:
        pid_file = Path(consumer.pid_file)
        log_path = Path(consumer.log_path)
        if not pid_file.exists():
            with open(log_path, "a") as f:
                f.write(f"\n Stopping {consumer.name} consumer...")
            results.append(
                {"success": False, "message": f"{consumer.name} consumer is not running."}
            )
            continue
        try:
            with open(pid_file) as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            os.system(
                f"ps aux | grep 'huey_{consumer.name}' | grep -v grep | awk '{{print $2}}' | xargs kill -9"  # noqa: E501
            )
            os.remove(pid_file)
            with open(log_path, "a") as f:
                f.write(f"\n Stopping {consumer.name} consumer...")
            results.append(
                {"success": True, "message": f"{consumer.name} consumer with PID {pid} stopped."}
            )
        except ProcessLookupError:
            os.remove(pid_file)
            results.append(
                {
                    "success": True,
                    "message": f"{consumer.name} consumer with PID {pid} not found.",
                }
            )
        except Exception as e:
            results.append(
                {"success": False, "message": f"Failed to stop {consumer.name} consumer: {e}"}
            )
    await broadcast_consumer_status_for_all()
    return {"results": results}


def get_consumer_status_map() -> dict[str, str]:
    """Return a mapping of queue_name to status ('running' or 'stopped')."""
    status_map = {}
    for consumer in CONSUMERS:
        pid_file = Path(consumer.pid_file)
        if pid_file.exists():
            try:
                with open(pid_file) as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)
                status_map[consumer.name] = "running"
            except Exception:
                status_map[consumer.name] = "stopped"
        else:
            status_map[consumer.name] = "stopped"
    return status_map


async def broadcast_consumer_status_for_all() -> None:
    try:
        await job_queue_ws_manager.broadcast({"consumer_status": get_consumer_status_map()})
    except Exception as e:
        logger.error(f"Failed to broadcast consumer status: {e}")


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
