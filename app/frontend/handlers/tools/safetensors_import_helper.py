import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlmodel import Session

from app import crud
from app.core.db import get_db
from app.frontend.templates import templates
from app.frontend.templates.context import get_template_context
from app.models.sd_extra_networks import Safetensor
from app.paths import HUB_MODELS_PATH


FLUX_PATH = HUB_MODELS_PATH / "FLUX"
HUNYUAN_PATH = HUB_MODELS_PATH / "Hunyuan"
SDXL_PATH = HUB_MODELS_PATH / "SDXL"
WAN_2_1_VIDEO_PATH = HUB_MODELS_PATH / "WAN_2_1 Video"


class HubBaseModel(BaseModel):
    name: str
    path: Path
    checkpoints_path: Path | None
    lora_path: Path | None
    safetensors_checkpoints: list[Safetensor] = []
    safetensors_loras: list[Safetensor] = []
    sd_base_model_id: str | None = None

    model_config = {"arbitrary_types_allowed": True}

    def import_safetensors(self) -> None:
        if self.checkpoints_path:
            checkpoints_paths = list(self.checkpoints_path.rglob("*.safetensors"))
            for checkpoint_path in checkpoints_paths:
                checkpoint_safetensor = Safetensor(path=checkpoint_path)
                self.safetensors_checkpoints.append(checkpoint_safetensor)
        if self.lora_path:
            lora_paths = list(self.lora_path.rglob("**/characters/**/*.safetensors"))
            for lora_path in lora_paths:
                lora_safetensor = Safetensor(path=lora_path)
                self.safetensors_loras.append(lora_safetensor)


def get_all_hub_models() -> list[HubBaseModel]:
    """Get all safetensors in the hub."""
    hub_models = []

    # FLUX
    flux_path = HUB_MODELS_PATH / "FLUX"
    hub_flux = HubBaseModel(
        name="FLUX",
        path=flux_path,
        checkpoints_path=flux_path / "checkpoints",
        lora_path=flux_path / "loras",
        sd_base_model_id="flux",
    )
    hub_models.append(hub_flux)

    # Hunyuan
    hunyuan_path = HUB_MODELS_PATH / "Hunyuan"
    hub_hunyuan = HubBaseModel(
        name="Hunyuan",
        path=hunyuan_path,
        checkpoints_path=None,
        lora_path=hunyuan_path / "Lora",
        sd_base_model_id="hunyuan",
    )
    hub_models.append(hub_hunyuan)

    # SDXL: SDXL
    sdxl_path = HUB_MODELS_PATH / "SDXL"
    hub_sdxl_sdxl = HubBaseModel(
        name="SDXL: SDXL",
        path=sdxl_path,
        checkpoints_path=sdxl_path / "base_models" / "sdxl",
        lora_path=sdxl_path / "loras" / "sdxl",
        sd_base_model_id="sdxl",
    )
    hub_models.append(hub_sdxl_sdxl)

    # SDXL: Pony
    sdxl_path = HUB_MODELS_PATH / "SDXL"
    hub_sdxl_pony = HubBaseModel(
        name="SDXL: Pony",
        path=sdxl_path,
        checkpoints_path=sdxl_path / "base_models" / "pony",
        lora_path=sdxl_path / "loras" / "pony",
        sd_base_model_id="pony",
    )
    hub_models.append(hub_sdxl_pony)

    # SDXL: Illustrious
    sdxl_path = HUB_MODELS_PATH / "SDXL"
    hub_sdxl_illustrious = HubBaseModel(
        name="Illustrious",
        path=sdxl_path,
        checkpoints_path=sdxl_path / "base_models" / "illustrious",
        lora_path=sdxl_path / "loras" / "illustrious",
        sd_base_model_id="illustrious",
    )
    hub_models.append(hub_sdxl_illustrious)

    # WAN_2_1 Video
    wan_2_1_video_path = HUB_MODELS_PATH / "WAN_2_1 Video"
    hub_wan_2_1_video = HubBaseModel(
        name="WAN_2_1 Video",
        path=wan_2_1_video_path,
        checkpoints_path=None,
        lora_path=wan_2_1_video_path / "Lora",
        sd_base_model_id="wan_2_1_video",
    )
    hub_models.append(hub_wan_2_1_video)

    # Import safetensors
    for hub_model in hub_models:
        hub_model.import_safetensors()

    return hub_models


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
    hub_models = get_all_hub_models()
    context["hub_models"] = hub_models
    if sd_base_model_id:
        context["hub_models"] = [
            hub_model for hub_model in hub_models if hub_model.sd_base_model_id == sd_base_model_id
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
