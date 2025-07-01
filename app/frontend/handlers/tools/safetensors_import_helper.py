import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlmodel import Session

from app import crud
from app.logic.hub import get_hub
from app.paths import HUB_MODELS_PATH
from framework.core.db import get_db
from framework.frontend.templates import templates
from framework.frontend.templates.context import get_template_context


router = APIRouter()


@router.get("/tools/safetensor-import-helper", response_class=HTMLResponse)
async def safetensor_import_helper_page(
    request: Request,
    db: Session = Depends(get_db),
    context: dict[str, Any] = Depends(get_template_context),
    sd_base_model_id: str | None = Query(None),
) -> HTMLResponse:
    """Safetensor Import Helper page.

    Lists all safetensors found in the hub, grouped by type and model.

    Args:
        request: FastAPI request object
        context: Template context dictionary

    Returns:
        HTML response with rendered template
    """
    hub = get_hub()
    context["hub_base_models"] = hub.hub_base_models
    if sd_base_model_id:
        context["hub_base_models"] = [
            hub_base_model
            for hub_base_model in hub.hub_base_models
            if hub_base_model.sd_base_model_id == sd_base_model_id
        ]

    existing_sd_checkpoints = await crud.sd_checkpoint.get_all(db)
    existing_sd_checkpoints_ids = [sd_checkpoint.id for sd_checkpoint in existing_sd_checkpoints]
    context["existing_sd_checkpoints_ids"] = existing_sd_checkpoints_ids

    existing_sd_extra_networks = await crud.sd_extra_network.get_all(db)
    existing_sd_extra_networks_file_paths = [
        sd_extra_network.local_file_path for sd_extra_network in existing_sd_extra_networks
    ]
    context["existing_sd_extra_networks_file_paths"] = existing_sd_extra_networks_file_paths

    context["sd_base_model_id"] = sd_base_model_id

    return templates.TemplateResponse(
        "tools/safetensors_import_helper.html",
        context,
    )


class DeleteSafetensorRequest(BaseModel):
    file_path: str


@router.post("/tools/delete_safetensor")
async def delete_safetensor(request: DeleteSafetensorRequest) -> dict[str, Any]:
    """Delete a safetensor file and its associated JSON file.

    Args:
        request: Request body containing the file path

    Returns:
        Dictionary indicating success or failure
    """
    try:
        # Ensure the file is within HUB_MODELS_PATH for security
        full_path = Path(request.file_path)
        if not str(full_path).startswith(str(HUB_MODELS_PATH)):
            return {"success": False, "error": "Invalid file path"}

        # Delete safetensor file
        if os.path.exists(request.file_path):
            os.remove(request.file_path)

        # Delete associated JSON file if it exists
        json_path = request.file_path.replace(".safetensors", ".json")
        if os.path.exists(json_path):
            os.remove(json_path)

        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
