from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app import models
from app.logic import state
from app.logic.dashboard import get_config
from framework.frontend.deps import get_current_active_user
from framework.frontend.templates import templates
from framework.frontend.templates.context import get_template_context


router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    current_user: models.User = Depends(get_current_active_user),
    context: dict[str, Any] = Depends(get_template_context),
) -> HTMLResponse:
    """Dashboard page."""
    config = get_config()
    apps = config["apps"]

    # Fetch instance and network state for dashboard
    instance_state = await state.get_instance_state()
    network_state = await state.get_network_state_from_host()

    context["apps"] = apps
    context["instance_state"] = instance_state
    context["network_state"] = network_state
    return templates.TemplateResponse(
        "dashboard/dashboard.html",
        context,
    )
