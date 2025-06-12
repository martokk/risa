"""
API endpoints for managing the job queue.
"""

from uuid import UUID

from fastapi import APIRouter, Body, HTTPException

from app import models
from app.services import job_queue


router = APIRouter()


@router.post("/jobs", response_model=models.Job, status_code=201)
def create_job(job_in: models.Job = Body(...)) -> models.Job:
    """
    Create a new job and add it to the queue.
    """
    return job_queue.add_job_to_queue(job_in)


@router.get("/jobs", response_model=list[models.Job])
def list_jobs() -> list[models.Job]:
    """
    Retrieve a list of all jobs. (Placeholder)
    """
    return job_queue.get_all_jobs()


@router.get("/jobs/{job_id}", response_model=models.Job)
def get_job(job_id: UUID) -> models.Job:
    """
    Retrieve a single job by its ID. (Placeholder)
    """
    job = job_queue.get_job_by_id(str(job_id))
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.delete("/jobs/{job_id}", status_code=204)
def delete_job(job_id: UUID) -> None:
    """
    Delete a job. (Placeholder)
    """
    if not job_queue.cancel_job(str(job_id)):
        raise HTTPException(status_code=404, detail="Job not found or could not be cancelled")
    return


# The following endpoints are placeholders as per the service layer.
# A full implementation would require more complex logic.


@router.post("/jobs/reorder", status_code=501)
def reorder_jobs() -> None:
    """Reorder jobs. (Not Implemented)"""
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.post("/jobs/{job_id}/retry", status_code=501)
def retry_job(job_id: UUID) -> None:
    """Retry a failed job. (Not Implemented)"""
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.get("/jobs/status", status_code=501)
def get_status() -> None:
    """Get queue status. (Not Implemented)"""
    raise HTTPException(status_code=501, detail="Not Implemented")
