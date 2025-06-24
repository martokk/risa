from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app.models import settings
from framework import crud
from framework.core.db import get_db
from framework.frontend.templates import templates
from framework.frontend.templates.context import get_template_context


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
    jobs = await crud.job.get_all_jobs_for_env_name(db, env_name=settings.ENV_NAME)
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
    return templates.TemplateResponse("jobs/jobs.html", context)
