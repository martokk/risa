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
    context: Annotated[dict[str, Any], Depends(get_template_context)],
    id: str = Query(None),
    name: str = Query(None),
    local_file_path: str = Query(None),
    remote_file_path: str = Query(None),
    lora_tag: str = Query(None),
    sha256: str = Query(None),
    trigger: str = Query(None),
    only_realistic: bool = Query(False),
    only_nonrealistic: bool = Query(False),
    only_checkpoints: list[str] = Query(None),
    exclude_checkpoints: list[str] = Query(None),
    sd_base_model_id: str = Query(None),
    redirect_url: str = Query(None),
) -> HTMLResponse:
    """Serves the page for creating a new SD Extra Network.

    Args:
        request: The FastAPI request object.
        context: Template context dependency.
        lora_name: The name of the LoRA.
        local_file_path: The local path to the LoRA file.
        lora_sha256: The SHA256 hash of the LoRA file.
        redirect_url: The URL to redirect to after creation.

    Returns:
        HTMLResponse: The rendered creation page.
    """
    from urllib.parse import unquote

    context["sd_base_model_id"] = sd_base_model_id

    db_session_for_relations = next(get_db())
    sd_base_models = await crud.sd_base_model.get_all(db=db_session_for_relations)
    characters = await crud.character.get_all(db=db_session_for_relations)
    db_session_for_relations.close()

    context["sd_base_models"] = sd_base_models
    context["characters"] = characters
    context["id"] = unquote(id) if id else None
    context["name"] = unquote(name) if name else None
    context["local_file_path"] = unquote(local_file_path) if local_file_path else None
    context["remote_file_path"] = unquote(remote_file_path) if remote_file_path else None
    context["lora_tag"] = unquote(lora_tag) if lora_tag else None
    context["sha256"] = unquote(sha256) if sha256 else None
    context["trigger"] = unquote(trigger) if trigger else None
    context["only_realistic"] = only_realistic
    context["only_nonrealistic"] = only_nonrealistic
    context["only_checkpoints"] = (
        [unquote(x) for x in only_checkpoints] if only_checkpoints else None
    )
    context["exclude_checkpoints"] = (
        [unquote(x) for x in exclude_checkpoints] if exclude_checkpoints else None
    )
    context["redirect_url"] = unquote(redirect_url) if redirect_url else None

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
