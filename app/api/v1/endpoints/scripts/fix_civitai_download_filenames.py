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


@router.post("/scripts/fix-civitai-download-filenames/add-to-queue")
@restrict_to("playground")
async def fix_civitai_download_filenames(
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    body: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
) -> JSONResponse:
    hub_path = body["hub_path"]

    if not hub_path:
        return JSONResponse(
            content={"success": False, "message": "Hub Path is required."},
            status_code=400,
        )

    # Add to queue.
    await crud.job.create(
        db,
        obj_in=models.JobCreate(
            env_name=settings.ENV_NAME if settings.ENV_NAME == "dev" else "playground",
            queue_name="default",
            name=f"Fix Civitai Download Filenames: {hub_path}",
            type=models.JobType.script,
            command="ScriptFixCivitaiDownloadFilenames",
            meta=body,
            status=models.JobStatus.queued,
        ),
    )

    return JSONResponse(
        content={"success": True, "message": "Job added to queue."}, status_code=200
    )
