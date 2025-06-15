from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from framework import models
from framework.frontend.deps import get_current_active_user, get_current_user
from framework.frontend.templates.context import get_template_context


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
    return FileResponse("app/frontend/static/images/favicons/favicon.ico")
