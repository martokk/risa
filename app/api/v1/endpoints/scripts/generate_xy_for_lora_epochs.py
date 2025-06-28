"""
API endpoints for managing the job queue.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app import crud, models
from framework.api.deps import get_current_active_user
from framework.core.db import get_db
from framework.routes.restrict_to_env import restrict_to


router = APIRouter()


@router.post("/scripts/generate-xy-for-lora-epochs/add-to-queue")
@restrict_to("playground")
async def generate_xy_for_lora_epochs(
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    body: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
) -> JSONResponse:
    print(body)

    # TODO: Connect 'body' to the script.
    lora_output_name = body["lora_output_name"]

    # Add to queue.
    await crud.job.create(
        db,
        obj_in=models.JobCreate(
            env_name="playground",
            name=f"Generate XY for Lora Epochs: {lora_output_name}",
            type=models.JobType.script,
            command="ScriptGenerateXYForLoraEpochs",
            meta=body,
            status=models.JobStatus.pending,
        ),
    )

    return JSONResponse(
        content={"success": True, "message": "Job added to queue."}, status_code=200
    )
