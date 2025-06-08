from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app import crud
from app.core.db import get_db
from app.frontend.templates import templates
from app.frontend.templates.context import get_template_context


router = APIRouter(tags=["SD Checkpoints"])


@router.get("/sd-checkpoints", response_class=HTMLResponse)
async def list_sd_checkpoints_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[dict[str, Any], Depends(get_template_context)],
) -> HTMLResponse:
    """Serves the page listing all SD Checkpoints.

    Args:
        request: The FastAPI request object.
        db: Database session dependency.
        context: Template context dependency.

    Returns:
        HTMLResponse: The rendered page.
    """
    sd_checkpoints = await crud.sd_checkpoint.get_all(db=db)
    context["sd_checkpoints"] = sd_checkpoints
    return templates.TemplateResponse(
        request=request,
        name="sd_checkpoint/sd_checkpoint_list.html",
        context=context,
    )


@router.get("/sd-checkpoint/create", response_class=HTMLResponse)
async def create_sd_checkpoint_page(
    request: Request,
    context: Annotated[dict[str, Any], Depends(get_template_context)],
    id: str = Query(None),
    name: str = Query(None),
    local_file_path: str = Query(None),
    remote_file_path: str = Query(None),
    is_realistic: bool = Query(False),
    sd_base_model_id: str = Query(None),
    redirect_url: str = Query(None),
) -> HTMLResponse:
    """Serves the page for creating a new SD Checkpoint.

    Args:
        request: The FastAPI request object.
        context: Template context dependency.

    Returns:
        HTMLResponse: The rendered creation page.
    """
    # We need to pass sd_base_models to the template for the dropdown
    db_session_for_base_models = next(get_db())  # Create a new session for this operation
    sd_base_models = await crud.sd_base_model.get_all(db=db_session_for_base_models)
    context["sd_base_models"] = sd_base_models
    db_session_for_base_models.close()

    context["name"] = name
    context["id"] = id
    context["local_file_path"] = local_file_path
    context["remote_file_path"] = remote_file_path
    context["is_realistic"] = is_realistic
    context["sd_base_model_id"] = sd_base_model_id
    context["redirect_url"] = redirect_url
    return templates.TemplateResponse(
        request=request,
        name="sd_checkpoint/sd_checkpoint_create.html",
        context=context,
    )


@router.get("/sd-checkpoint/{sd_checkpoint_id}/view", response_class=HTMLResponse)
async def view_sd_checkpoint_page(
    request: Request,
    sd_checkpoint_id: str,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[dict[str, Any], Depends(get_template_context)],
) -> HTMLResponse:
    """Serves the page for viewing a specific SD Checkpoint.

    Args:
        request: The FastAPI request object.
        sd_checkpoint_id: The ID of the SD Checkpoint to view.
        db: Database session dependency.
        context: Template context dependency.

    Returns:
        HTMLResponse: The rendered view page.
    """
    sd_checkpoint_obj = await crud.sd_checkpoint.get(db=db, id=sd_checkpoint_id)
    if not sd_checkpoint_obj:
        raise HTTPException(status_code=404, detail="SD Checkpoint not found")
    context["sd_checkpoint"] = sd_checkpoint_obj

    # Get all extra networks for the checkpoint
    extra_networks = await crud.sd_checkpoint.get_all_extra_networks_for_checkpoint(
        db=db, checkpoint_id=sd_checkpoint_id
    )
    context["extra_networks"] = extra_networks

    # Get all excluded extra networks for the checkpoint
    excluded_extra_networks = (
        await crud.sd_checkpoint.get_all_excluded_extra_networks_for_checkpoint(
            db=db, checkpoint_id=sd_checkpoint_id
        )
    )
    context["excluded_extra_networks"] = excluded_extra_networks

    return templates.TemplateResponse(
        request=request,
        name="sd_checkpoint/sd_checkpoint_view.html",
        context=context,
    )


@router.get("/sd-checkpoint/{sd_checkpoint_id}/edit", response_class=HTMLResponse)
async def edit_sd_checkpoint_page(
    request: Request,
    sd_checkpoint_id: str,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[dict[str, Any], Depends(get_template_context)],
) -> HTMLResponse:
    """Serves the page for editing a specific SD Checkpoint.

    Args:
        request: The FastAPI request object.
        sd_checkpoint_id: The ID of the SD Checkpoint to edit.
        db: Database session dependency.
        context: Template context dependency.

    Returns:
        HTMLResponse: The rendered edit page.
    """
    sd_checkpoint_obj = await crud.sd_checkpoint.get(db=db, id=sd_checkpoint_id)
    if not sd_checkpoint_obj:
        raise HTTPException(status_code=404, detail="SD Checkpoint not found")
    context["sd_checkpoint"] = sd_checkpoint_obj

    # We need to pass sd_base_models to the template for the dropdown
    db_session_for_base_models = next(get_db())  # Create a new session for this operation
    sd_base_models = await crud.sd_base_model.get_all(db=db_session_for_base_models)
    context["sd_base_models"] = sd_base_models
    db_session_for_base_models.close()

    return templates.TemplateResponse(
        request=request,
        name="sd_checkpoint/sd_checkpoint_edit.html",
        context=context,
    )
