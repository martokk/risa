"""
API endpoints for managing the job queue.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app import crud, models, settings
from vcore.backend.api.deps import get_current_active_user
from vcore.backend.core.db import get_db


router = APIRouter()


@router.post("/scripts/rsync-files/add-to-queue")
async def rsync_files(
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    body: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
) -> JSONResponse:
    # Get from body
    env_name = body.get("job_env", settings.ENV_NAME if settings.ENV_NAME else "dev")
    queue_name = body.get("queue_name", "default")
    source_env = body["source_env"]
    destination_env = body["destination_env"]
    source_location = body["source_location"]
    destination_location = body["destination_location"]

    # Add to queue.
    db_job = await crud.job.create(
        db,
        obj_in=models.JobCreate(
            env_name=env_name,
            queue_name=queue_name,
            name=f"Rsync Files:  [{source_env.upper()}] `{source_location}`   -->   [{destination_env.upper()}] `{destination_location}`",
            type=models.JobType.script,
            command="ScriptRsyncFiles",
            meta=body,
            status=models.JobStatus.queued,
        ),
    )

    return JSONResponse(
        content={
            "success": True,
            "message": f"Job added to r|{env_name.upper()}'s '{queue_name}' queue.",
            "job": db_job.model_dump(mode="json"),
        },
        status_code=200,
    )
