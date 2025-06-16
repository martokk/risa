from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app import crud, logger, models
from app.logic import runpod, state
from app.logic.dashboard import get_config
from framework.core.db import get_db
from framework.frontend.deps import get_current_active_user
from framework.frontend.templates import templates
from framework.frontend.templates.context import get_template_context


router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    current_user: models.User = Depends(get_current_active_user),
    context: dict[str, Any] = Depends(get_template_context),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Dashboard page."""
    config = get_config()
    apps = config["apps"]

    try:
        characters = await crud.character.get_all(db=db)
    except Exception as e:
        logger.error(f"Error fetching characters: {str(e)}")
        characters = []

    try:
        checkpoints = await crud.sd_checkpoint.get_all(db=db)
    except Exception as e:
        logger.error(f"Error fetching checkpoints: {str(e)}")
        checkpoints = []

    # Fetch instance and network state for dashboard
    instance_state = await state.get_instance_state()
    network_state = await state.get_network_state_from_host()

    context["apps"] = apps
    context["instance_state"] = instance_state
    context["network_state"] = network_state
    context["characters"] = characters or []
    context["checkpoints"] = checkpoints or []
    # Add RunPod info
    try:
        context["runpod_id"] = runpod.get_runpod_id()
    except Exception:
        context["runpod_id"] = "N/A"
    try:
        context["gpu_name"] = runpod.get_runpod_gpu_name()
    except Exception:
        context["gpu_name"] = "N/A"
    return templates.TemplateResponse(
        "dashboard/dashboard.html",
        context,
    )
