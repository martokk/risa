from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app import crud
from app.core.db import get_db
from app.views.templates import templates
from app.views.templates.context import get_template_context


router = APIRouter(tags=["SD Extra Networks"])


@router.get("/sd-extra-networks", response_class=HTMLResponse)
async def list_sd_extra_networks_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[dict[str, Any], Depends(get_template_context)],
) -> HTMLResponse:
    """Serves the page listing all SD Extra Networks."""
    sd_extra_networks = await crud.sd_extra_network.get_all(db)
    context["sd_extra_networks"] = sd_extra_networks

    return templates.TemplateResponse(
        request=request,
        name="sd_extra_network/sd_extra_network_list.html",
        context=context,
    )


@router.get("/sd-extra-network/create", response_class=HTMLResponse)
async def create_sd_extra_network_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[dict[str, Any], Depends(get_template_context)],
    character_id: Annotated[str | None, Query()] = None,
) -> HTMLResponse:
    """Serves the page for creating a new SD Extra Network."""
    sd_base_models = await crud.sd_base_model.get_all(db)
    characters = await crud.character.get_all(db)
    context["sd_base_models"] = sd_base_models
    context["characters"] = characters
    context["selected_character_id"] = character_id
    return templates.TemplateResponse(
        request=request,
        name="sd_extra_network/sd_extra_network_create.html",
        context=context,
    )


@router.get("/sd-extra-network/{sd_extra_network_id}/view", response_class=HTMLResponse)
async def view_sd_extra_network_page(
    request: Request,
    sd_extra_network_id: str,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[dict[str, Any], Depends(get_template_context)],
) -> HTMLResponse:
    """Serves the page for viewing a specific SD Extra Network."""
    sd_extra_network_obj = await crud.sd_extra_network.get(db=db, id=sd_extra_network_id)
    if not sd_extra_network_obj:
        raise HTTPException(status_code=404, detail="SD Extra Network not found")

    context["sd_extra_network"] = sd_extra_network_obj
    return templates.TemplateResponse(
        request=request,
        name="sd_extra_network/sd_extra_network_view.html",
        context=context,
    )


@router.get("/sd-extra-network/{sd_extra_network_id}/edit", response_class=HTMLResponse)
async def edit_sd_extra_network_page(
    request: Request,
    sd_extra_network_id: str,
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[dict[str, Any], Depends(get_template_context)],
) -> HTMLResponse:
    """Serves the page for editing a specific SD Extra Network."""
    sd_extra_network_obj = await crud.sd_extra_network.get(db=db, id=sd_extra_network_id)
    if not sd_extra_network_obj:
        raise HTTPException(status_code=404, detail="SD Extra Network not found")

    sd_base_models = await crud.sd_base_model.get_all(db=db)
    characters = await crud.character.get_all(db=db)

    context["sd_extra_network"] = sd_extra_network_obj
    context["sd_base_models"] = sd_base_models
    context["characters"] = characters
    return templates.TemplateResponse(
        request=request,
        name="sd_extra_network/sd_extra_network_edit.html",
        context=context,
    )
