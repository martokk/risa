"""
API endpoints for managing the job queue.
"""

import json
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app import crud, models, settings
from vcore.backend.api.deps import get_current_active_user
from vcore.backend.core.db import get_db
from vcore.backend.routes.restrict_to_env import restrict_to


router = APIRouter()


@router.post("/scripts/generate-xy-for-lora-epochs/add-to-queue")
@restrict_to("playground")
async def generate_xy_for_lora_epochs(
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    body: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
) -> JSONResponse:
    lora_output_name = body["lora_output_name"]

    # convert str of list to list object
    body["styles"] = json.loads(body["styles"])

    env_name = body.get("env_name", settings.ENV_NAME if settings.ENV_NAME else "dev")
    queue_name = body.get("queue_name", "default")

    # Add to queue.
    db_job = await crud.job.create(
        db,
        obj_in=models.JobCreate(
            env_name=env_name,
            queue_name=queue_name,
            name=f"GenXY: {lora_output_name}",
            type=models.JobType.script,
            command="ScriptGenerateXYForLoraEpochs",
            meta=body,
            status=models.JobStatus.pending,
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
