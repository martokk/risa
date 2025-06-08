from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app import crud
from app.core.db import get_db
from app.frontend.templates import templates
from app.frontend.templates.context import get_template_context


router = APIRouter(tags=["SD Base Models"])


@router.get("/sd-base-models", response_class=HTMLResponse)
async def list_sd_base_models_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[dict[str, Any], Depends(get_template_context)],
) -> HTMLResponse:
    """Serves the page listing all SD Base Models.

    Args:
        request: The FastAPI request object.
        db: Database session dependency.
        context: Template context dependency.

    Returns:
        HTMLResponse: The rendered page.
    """
    sd_base_models = await crud.sd_base_model.get_all(db=db)
    context["sd_base_models"] = sd_base_models
    return templates.TemplateResponse(
        request=request,
        name="sd_base_model/sd_base_model_list.html",
        context=context,
    )


@router.get("/sd-base-model/create", response_class=HTMLResponse)
async def create_sd_base_model_page(
    request: Request,
    context: Annotated[dict[str, Any], Depends(get_template_context)],
) -> HTMLResponse:
    """Serves the page for creating a new SD Base Model.

    Args:
        request: The FastAPI request object.
        context: Template context dependency.

    Returns:
        HTMLResponse: The rendered creation page.
    """
    return templates.TemplateResponse(
        request=request,
        name="sd_base_model/sd_base_model_create.html",
        context=context,
    )


@router.get("/sd-base-model/{sd_base_model_id}/view", response_class=HTMLResponse)
async def view_sd_base_model_page(
    request: Request,
    sd_base_model_id: str,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[dict[str, Any], Depends(get_template_context)],
) -> HTMLResponse:
    """Serves the page for viewing a specific SD Base Model.

    Args:
        request: The FastAPI request object.
        sd_base_model_id: The ID of the SD Base Model to view.
        db: Database session dependency.
        context: Template context dependency.

    Returns:
        HTMLResponse: The rendered view page.
    """
    sd_base_model_obj = await crud.sd_base_model.get(db=db, id=sd_base_model_id)
    if not sd_base_model_obj:
        raise HTTPException(status_code=404, detail="SD Base Model not found")
    context["sd_base_model"] = sd_base_model_obj
    return templates.TemplateResponse(
        request=request,
        name="sd_base_model/sd_base_model_view.html",
        context=context,
    )


@router.get("/sd-base-model/{sd_base_model_id}/edit", response_class=HTMLResponse)
async def edit_sd_base_model_page(
    request: Request,
    sd_base_model_id: str,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[dict[str, Any], Depends(get_template_context)],
) -> HTMLResponse:
    """Serves the page for editing a specific SD Base Model.

    Args:
        request: The FastAPI request object.
        sd_base_model_id: The ID of the SD Base Model to edit.
        db: Database session dependency.
        context: Template context dependency.

    Returns:
        HTMLResponse: The rendered edit page.
    """
    sd_base_model_obj = await crud.sd_base_model.get(db=db, id=sd_base_model_id)
    if not sd_base_model_obj:
        raise HTTPException(status_code=404, detail="SD Base Model not found")
    context["sd_base_model"] = sd_base_model_obj
    return templates.TemplateResponse(
        request=request,
        name="sd_base_model/sd_base_model_edit.html",
        context=context,
    )


# Note: The actual delete operation would be an API endpoint (e.g., DELETE method).
# This route could serve a confirmation page if needed, or the delete can be handled
# client-side with a JavaScript confirmation before calling the API.
# For now, we'll assume client-side handling, so no specific delete page handler.
