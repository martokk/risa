from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app import crud as app_crud, logger
from app.logic.file_management import get_trained_lora_safetensors
from app.models import settings
from vcore.backend import crud
from vcore.backend.core.db import get_db
from vcore.backend.templating import templates
from vcore.backend.templating.context import get_template_context


router = APIRouter(tags=["jobs"])


@router.get("/jobs", response_class=HTMLResponse)
async def jobs_page(
    context: dict[str, Any] = Depends(get_template_context),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """
    Renders the main job queue dashboard page.

    Args:
        context: The template context, including the request object.

    Returns:
        An HTML response rendering the jobs page.
    """
    jobs = await crud.job.get_all_jobs_for_env_name(
        db, env_name=settings.ENV_NAME, include_archived=False
    )

    # Sort jobs by status and priority for display
    status_order = {
        "running": 0,
        "queued": 1,
        "pending": 2,
        "failed": 3,
        "done": 4,
    }
    priority_order = {"highest": 0, "high": 0, "normal": 1, "low": 2, "lowest": 3}

    sorted_jobs = sorted(
        jobs, key=lambda j: (status_order.get(j.status, 99), priority_order.get(j.priority, 99))
    )

    context["jobs"] = sorted_jobs

    try:
        characters = await app_crud.character.get_all(db=db)
    except Exception as e:
        logger.error(f"Error fetching characters: {str(e)}")
        characters = []

    try:
        sd_checkpoints = await app_crud.sd_checkpoint.get_all(db=db)
    except Exception as e:
        logger.error(f"Error fetching checkpoints: {str(e)}")
        sd_checkpoints = []

    context["characters"] = characters or []
    context["sd_checkpoints"] = sd_checkpoints or []

    # Script Hooks
    context["trained_lora_safetensors"] = get_trained_lora_safetensors() or []

    return templates.TemplateResponse("jobs/jobs.html", context)
