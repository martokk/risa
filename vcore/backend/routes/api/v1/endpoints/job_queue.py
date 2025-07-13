"""
API endpoints for managing the job queue.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlmodel import Session

from app import paths, settings
from vcore.backend import crud, models
from vcore.backend.core.db import get_db
from vcore.backend.services.job_queue import (
    kill_job_process,
    start_consumer_process,
    stop_consumer_process,
)
from vcore.backend.services.job_queue_ws_manager import job_queue_ws_manager


router = APIRouter(prefix="/jobs", tags=["Job Queue"])


@router.post("/", response_model=models.Job, status_code=201)
async def create_job(db: Session = Depends(get_db), job_in: models.Job = Body(...)) -> models.Job:
    """
    Create a new job and add it to the queue.
    """
    try:
        return await crud.job.create(db, obj_in=job_in)
    except Exception as e:
        from app import logger

        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create job.")


@router.get("/", response_model=list[models.Job])
async def list_jobs(db: Session = Depends(get_db)) -> list[models.Job]:
    """
    Retrieve a list of all jobs.
    """
    return await crud.job.get_all(db)


@router.get("/{job_id}", response_model=models.Job)
async def get_job(job_id: UUID, db: Session = Depends(get_db)) -> models.Job:
    """
    Retrieve a single job by its ID.
    """
    return await crud.job.get(db, id=job_id)


@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: str, db: Session = Depends(get_db)) -> None:
    """
    Delete a job.
    """
    try:
        return await crud.job.remove(db, id=job_id)
    except Exception as e:
        from app import logger

        logger.error(f"Failed to delete job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete job {job_id}.")


@router.post("/push-jobs-to-websocket")
async def push_jobs_to_websocket_endpoint(db: Session = Depends(get_db)) -> None:
    """
    Push all jobs to the websocket.
    """
    from app import logger

    try:
        jobs = await crud.job.get_all_jobs_for_env_name(db, env_name=settings.ENV_NAME)
        try:
            await job_queue_ws_manager.broadcast(
                {
                    "jobs": [j.model_dump(mode="json") for j in jobs],
                }
            )
        except Exception as e:
            logger.error(f"Failed to broadcast jobs to websocket: {e}")
    except Exception as e:
        logger.error(f"Failed to push jobs to websocket: {e}")
        raise HTTPException(status_code=500, detail="Failed to push jobs to websocket.")


@router.put("/{job_id}", response_model=models.Job)
async def update_job(
    job_id: str, job_in: models.JobUpdate = Body(...), db: Session = Depends(get_db)
) -> models.Job:
    """
    Update a job's properties.
    """
    try:
        return await crud.job.update(db, id=job_id, obj_in=job_in)
    except Exception as e:
        from app import logger

        logger.error(f"Failed to update job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update job {job_id}.")


@router.put("/{job_id}/status")
async def update_job_status(
    job_id: str, body: dict[str, Any] = Body(...), db: Session = Depends(get_db)
) -> JSONResponse:
    """
    Update the status of a job and broadcast the update to websocket clients.
    Expects a JSON body: {"status": "running"}
    """
    from app import logger

    status_value = body.get("status")
    if not status_value:
        raise HTTPException(status_code=400, detail="Missing 'status' in request body.")
    try:
        status = models.JobStatus(status_value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status_value}")
    try:
        # Update the job status in the database
        await crud.job.update(db, id=job_id, obj_in=models.JobUpdate(status=status))
        # The websocket broadcast is handled by the CRUD decorator, but we can log here
        logger.info(f"Job {job_id} status updated to {status.value} and broadcast attempted.")
    except Exception as e:
        logger.error(f"Failed to update job status or broadcast for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update job status for {job_id}.")
    return JSONResponse(
        content={"success": True, "message": f"Job {job_id} status updated to {status.value}"}
    )


@router.post("/{job_id}/kill")
async def kill_job(job_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Immediately kill a running job by its PID.

    Args:
        job_id: The ID of the job to kill.

    Returns:
        Dict with 'success' and 'message'.

    Raises:
        HTTPException: If the job could not be killed.
    """
    result = await kill_job_process(job_id, db)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/{job_id}/log", response_class=PlainTextResponse)
def get_job_log(job_id: str) -> PlainTextResponse:
    """
    Retrieves the log file for a specific job.
    For now, it retrieves the log of the first run (retry_count=0).
    """
    # NOTE: This currently only fetches the log for the first run (retry 0).
    # A more robust solution would handle multiple retries.
    log_file_name = f"job_{job_id}_retry_0.txt"
    log_file_path = paths.JOB_LOGS_PATH / log_file_name

    if not log_file_path.exists():
        raise HTTPException(status_code=404, detail="Log file not found.")

    return PlainTextResponse(content=log_file_path.read_text())


@router.post("/start-consumer")
async def start_huey_consumer(body: dict[str, Any] = Body(default={})) -> JSONResponse:
    """Start Huey consumer for the specified queue (or all if not specified)."""
    queue_name = body.get("queue_name")
    result = await start_consumer_process(queue_name=queue_name)
    status = 200 if all(r.get("success") for r in result.get("results", [])) else 400
    return JSONResponse(content=result, status_code=status)


@router.post("/stop-consumer")
async def stop_huey_consumer(body: dict[str, Any] = Body(default={})) -> JSONResponse:
    """Stop Huey consumer for the specified queue (or all if not specified)."""
    queue_name = body.get("queue_name")
    result = await stop_consumer_process(queue_name=queue_name)
    status = 200 if all(r.get("success") for r in result.get("results", [])) else 400
    return JSONResponse(content=result, status_code=status)


# The following endpoints are placeholders as per the service layer.
# A full implementation would require more complex logic.


@router.post("/reorder", status_code=501)
def reorder_jobs() -> None:
    """Reorder jobs. (Not Implemented)"""
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.get("/status", status_code=501)
async def get_status() -> None:
    """Get queue status. (Not Implemented)"""
    raise HTTPException(status_code=501, detail="Not Implemented")
