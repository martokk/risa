"""
API endpoints for managing the job queue.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app import crud, models, settings
from framework.api.deps import get_current_active_user
from framework.core.db import get_db
from framework.routes.restrict_to_env import restrict_to


router = APIRouter()


@router.post("/scripts/choose-best-epoch/add-to-queue")
@restrict_to("playground")
async def generate_xy_for_lora_epochs(
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    body: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
) -> JSONResponse:
    lora_output_name = body["select_lora_output_name"]
    best_epoch = body["select_best_epoch"]

    if not lora_output_name or not best_epoch:
        return JSONResponse(
            content={"success": False, "message": "Lora Output Name and Best Epoch are required."},
            status_code=400,
        )

    env_name = body.get("env_name", settings.ENV_NAME if settings.ENV_NAME else "dev")
    queue_name = body.get("queue_name", "default")

    # Add to queue.
    db_job = await crud.job.create(
        db,
        obj_in=models.JobCreate(
            env_name=env_name,
            queue_name=queue_name,
            name=f"Choose Best Epoch: {lora_output_name}",
            type=models.JobType.script,
            command="ScriptChooseBestEpoch",
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
