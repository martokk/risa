from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app import crud
from framework.core.db import get_db
from framework.frontend.templates import templates
from framework.frontend.templates.context import get_template_context


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
    character_id: str = Query(None),
    trained_on_checkpoint: str = Query(None),
    local_file_path: str = Query(None),
    remote_file_path: str = Query(None),
    network: str = Query(None),
    network_trigger: str = Query(None),
    network_weight: float = Query(None),
    sha256: str = Query(None),
    only_realistic: bool = Query(False),
    only_nonrealistic: bool = Query(False),
    only_checkpoints: list[str] = Query(None),
    exclude_checkpoints: list[str] = Query(None),
    sd_base_model_id: str = Query(None),
    redirect_url: str = Query(None),
) -> HTMLResponse:
    """Serves the page for creating a new SD Extra Network."""
    context["sd_base_models"] = await crud.sd_base_model.get_all(db=db)
    context["characters"] = await crud.character.get_all(db=db)
    context["sd_checkpoints"] = await crud.sd_checkpoint.get_all(db=db)
    context["networks"] = ["lora"]
    context["item"] = None

    context["character_id"] = character_id
    context["trained_on_checkpoint"] = trained_on_checkpoint
    context["local_file_path"] = local_file_path
    context["remote_file_path"] = remote_file_path
    context["network"] = network
    context["network_trigger"] = network_trigger
    context["network_weight"] = network_weight
    context["sha256"] = sha256
    context["only_realistic"] = only_realistic
    context["only_nonrealistic"] = only_nonrealistic
    context["only_checkpoints"] = only_checkpoints
    context["exclude_checkpoints"] = exclude_checkpoints
    context["sd_base_model_id"] = sd_base_model_id
    context["redirect_url"] = redirect_url

    return templates.TemplateResponse(
        request=request,
        name="sd_extra_network/sd_extra_network_form.html",
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

    context["item"] = sd_extra_network_obj
    context["sd_base_models"] = await crud.sd_base_model.get_all(db=db)
    context["characters"] = await crud.character.get_all(db=db)
    context["sd_checkpoints"] = await crud.sd_checkpoint.get_all(db=db)
    context["networks"] = ["lora", "locon", "other"]
    context["view_mode"] = True

    return templates.TemplateResponse(
        request=request,
        name="sd_extra_network/sd_extra_network_form.html",
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

    context["item"] = sd_extra_network_obj
    context["sd_base_models"] = await crud.sd_base_model.get_all(db=db)
    context["characters"] = await crud.character.get_all(db=db)
    context["sd_checkpoints"] = await crud.sd_checkpoint.get_all(db=db)
    context["networks"] = ["lora", "locon", "other"]  # Add more as needed

    return templates.TemplateResponse(
        request=request,
        name="sd_extra_network/sd_extra_network_form.html",
        context=context,
    )
