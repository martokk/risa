from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app import models
from app.frontend.deps import get_current_active_user
from app.frontend.templates import templates
from app.frontend.templates.context import get_template_context
from app.logic.dashboard import get_config


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

    context["apps"] = apps
    return templates.TemplateResponse(
        "dashboard/dashboard.html",
        context,
    )
