from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.frontend.templates import templates
from app.frontend.templates.context import get_template_context
from app.services import job_queue


router = APIRouter(tags=["jobs"])


@router.get("/jobs", response_class=HTMLResponse)
async def jobs_page(
    context: dict[str, Any] = Depends(get_template_context),
) -> HTMLResponse:
    """
    Renders the main job queue dashboard page.

    Args:
        context: The template context, including the request object.

    Returns:
        An HTML response rendering the jobs page.
    """
    jobs = job_queue.get_all_jobs()
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
    return templates.TemplateResponse("root/jobs.html", context)
