"""
API endpoints for managing the job queue.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app import crud, models, settings
from vcore.backend.core.db import get_db
from vcore.backend.routes.restrict_to_env import restrict_to
from vcore.backend.templating.deps import get_current_active_user


router = APIRouter()


@router.post("/scripts/example-script/add-to-queue")
@restrict_to("dev")
async def example_script(
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    body: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
) -> JSONResponse:
    # Get from body
    env_name = body.get("env_name", settings.ENV_NAME if settings.ENV_NAME else "dev")
    queue_name = body.get("queue_name", "default")

    # Add to queue.
    db_job = await crud.job.create(
        db,
        obj_in=models.JobCreate(
            env_name=env_name,
            queue_name=queue_name,
            name="Example Script",
            type=models.JobType.script,
            command="ScriptExample",
            meta=body,
            status=models.JobStatus.queued,
        ),
    )

    return JSONResponse(
        content={
            "success": True,
            "message": f"Job added to r|{env_name.upper()}'s '{queue_name}' queue.",
            "job_id": db_job.id,
            "job": db_job.model_dump(),
        },
        status_code=200,
    )
