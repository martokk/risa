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

    # Add to queue.
    await crud.job.create(
        db,
        obj_in=models.JobCreate(
            env_name=settings.ENV_NAME if settings.ENV_NAME == "dev" else "playground",
            name=f"Choose Best Epoch: {lora_output_name}",
            type=models.JobType.script,
            command="ScriptChooseBestEpoch",
            meta=body,
            status=models.JobStatus.pending,
        ),
    )

    return JSONResponse(
        content={"success": True, "message": "Job added to queue."}, status_code=200
    )
