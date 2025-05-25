from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from sqlmodel import Session

from app import crud, models
from app.core.db import get_db
from app.logic import dashboard
from app.views.deps import get_current_active_user, get_current_user
from app.views.templates import templates
from app.views.templates.context import get_template_context


router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def root_index_router(
    request: Request,
    current_user: models.User = Depends(get_current_user),
    context: dict[str, Any] = Depends(get_template_context),
) -> Response:
    """
    Home page router

    Args:
        request(Request): The request object
        current_user(models.User): The current user

    Returns:
        Response: Home page
    """
    if current_user:
        return await root_index_authenticated(request, current_user, context)
    return await root_index_unauthenticated()


async def root_index_unauthenticated() -> Response:
    """
    Home page (Not authenticated)

    Returns:
        Response: Home page
    """
    return RedirectResponse(url="/login")


async def root_index_authenticated(
    request: Request,
    current_user: models.User = Depends(get_current_active_user),
    context: dict[str, Any] = Depends(get_template_context),
) -> Response:
    """
    Home page. (Authenticated)

    Args:
        request(Request): The request object
        current_user(models.User): The current user

    Returns:
        Response: Home page
    """
    return RedirectResponse(url="/dashboard")


@router.get("/favicon.ico", response_class=FileResponse)
async def favicon() -> FileResponse:
    """
    Serve favicon.ico file

    Returns:
        FileResponse: favicon.ico file
    """
    return FileResponse("app/views/static/images/favicons/favicon.ico")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    context: dict[str, Any] = Depends(get_template_context),
) -> Response:
    """Dashboard page showing overview of grants and activities."""
    # Get active organizations
    active_orgs = await crud.organization.get_active(db)
    active_orgs_count = len(active_orgs)

    # Get active programs
    active_programs = []
    for org in active_orgs:
        if org.id is not None:  # Add guard clause for None ID
            programs = await crud.grant_program.get_active_by_organization(
                db=db, organization_id=org.id
            )
            active_programs.extend(programs)
    active_programs_count = len(active_programs)

    # Get dashboard statistics
    stats = await dashboard.get_dashboard_statistics(db)

    # Get upcoming deadlines
    upcoming_deadlines = await dashboard.get_upcoming_deadlines(db)

    # Get recent activities
    recent_activities = await dashboard.get_recent_activity(db)

    context.update(
        {
            "request": request,
            "current_user": current_user,
            "submitted_count": stats["submitted_count"],
            "in_progress_count": stats["in_progress_count"],
            "total_requested_submitted": stats["total_requested_submitted"],
            "upcoming_awaiting_count": stats["upcoming_awaiting_count"],
            "upcoming_deadlines": upcoming_deadlines,
            "recent_activities": recent_activities,
            "now": datetime.utcnow(),
            "timedelta": timedelta,
        }
    )

    return templates.TemplateResponse("root/dashboard.html", context=context)
