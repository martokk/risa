import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from safetensors import safe_open
from sqlmodel import Session

from app import crud
from app.core.db import get_db
from app.paths import HUB_MODELS_PATH
from app.views.templates import templates
from app.views.templates.context import get_template_context


FLUX_PATH = HUB_MODELS_PATH / "FLUX"
HUNYUAN_PATH = HUB_MODELS_PATH / "Hunyuan"
SDXL_PATH = HUB_MODELS_PATH / "SDXL"
WAN_2_1_VIDEO_PATH = HUB_MODELS_PATH / "WAN_2_1 Video"


class Safetensor(BaseModel):
    path: Path

    @property
    def name(self) -> str:
        return self.path.stem

    @property
    def json_file(self) -> Path | None:
        json_file_path = Path(str(self.path).replace(".safetensors", ".json"))
        if json_file_path.exists():
            return json_file_path
        return None

    @property
    def sha256(self) -> str | None:
        if self.json_file:
            with open(self.json_file) as f:
                json_data = json.load(f)
            sha256 = str(json_data.get("sha256"))
            if sha256 and sha256 != "None":
                return sha256

        # get the sha256 from the safetensors file
        import hashlib

        _sha256 = hashlib.sha256()
        with open(self.path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                _sha256.update(chunk)
        sha256 = _sha256.hexdigest()
        if sha256 and sha256 != "None":
            # Load existing JSON data if file exists
            existing_json_data = {}
            if self.json_file and self.json_file.exists():
                with open(self.json_file) as f:
                    existing_json_data = json.load(f)

            # Update only the sha256 field
            existing_json_data["sha256"] = sha256

            # Save updated JSON data
            json_file_path = Path(str(self.path).replace(".safetensors", ".json"))
            with open(json_file_path, "w") as f:
                json.dump(existing_json_data, f)

            return sha256
        return None

    @property
    def size(self) -> int:
        return self.path.stat().st_size

    @property
    def metadata(self) -> dict[str, Any] | None:
        if self.path and self.path.exists():
            with safe_open(self.path, framework="pt") as f:
                metadata = f.metadata()
                return metadata
        return None


class HubBaseModel(BaseModel):
    name: str
    path: Path
    base_models_path: Path | None
    lora_path: Path | None
    safetensors_base_models: list[Safetensor] = []
    safetensors_loras: list[Safetensor] = []

    model_config = {"arbitrary_types_allowed": True}

    def import_safetensors(self) -> None:
        if self.base_models_path:
            base_models_paths = list(self.base_models_path.rglob("*.safetensors"))
            for base_model_path in base_models_paths:
                base_model_safetensor = Safetensor(path=base_model_path)
                self.safetensors_base_models.append(base_model_safetensor)
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
        base_models_path=flux_path / "Stable-diffusion",
        lora_path=flux_path / "Lora",
    )
    hub_models.append(hub_flux)

    # Hunyuan
    hunyuan_path = HUB_MODELS_PATH / "Hunyuan"
    hub_hunyuan = HubBaseModel(
        name="Hunyuan",
        path=hunyuan_path,
        base_models_path=None,
        lora_path=hunyuan_path / "Lora",
    )
    hub_models.append(hub_hunyuan)

    # SDXL: SDXL
    sdxl_path = HUB_MODELS_PATH / "SDXL"
    hub_sdxl_sdxl = HubBaseModel(
        name="SDXL: SDXL",
        path=sdxl_path,
        base_models_path=sdxl_path / "base_models" / "sdxl",
        lora_path=sdxl_path / "loras" / "sdxl",
    )
    hub_models.append(hub_sdxl_sdxl)

    # SDXL: Pony
    sdxl_path = HUB_MODELS_PATH / "SDXL"
    hub_sdxl_pony = HubBaseModel(
        name="SDXL: Pony",
        path=sdxl_path,
        base_models_path=sdxl_path / "base_models" / "pony",
        lora_path=sdxl_path / "loras" / "pony",
    )
    hub_models.append(hub_sdxl_pony)

    # SDXL: Illustrious
    sdxl_path = HUB_MODELS_PATH / "SDXL"
    hub_sdxl_illustrious = HubBaseModel(
        name="SDXL: Illustrious",
        path=sdxl_path,
        base_models_path=sdxl_path / "base_models" / "illustrious",
        lora_path=sdxl_path / "loras" / "illustrious",
    )
    hub_models.append(hub_sdxl_illustrious)

    # WAN_2_1 Video
    wan_2_1_video_path = HUB_MODELS_PATH / "WAN_2_1 Video"
    hub_wan_2_1_video = HubBaseModel(
        name="WAN_2_1 Video",
        path=wan_2_1_video_path,
        base_models_path=None,
        lora_path=wan_2_1_video_path / "Lora",
    )
    hub_models.append(hub_wan_2_1_video)

    # Import safetensors
    for hub_model in hub_models:
        hub_model.import_safetensors()

    return hub_models


router = APIRouter()


@router.get("/safetensor-import-helper", response_class=HTMLResponse)
async def safetensor_import_helper_page(
    request: Request,
    db: Session = Depends(get_db),
    context: dict[str, Any] = Depends(get_template_context),
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

    existing_sd_extra_networks = await crud.sd_extra_network.get_all(db)
    existing_sd_extra_networks_sha256s = [
        sd_extra_network.lora_sha256
        for sd_extra_network in existing_sd_extra_networks
        if sd_extra_network.lora_sha256
    ]
    context["existing_sd_extra_networks_sha256s"] = existing_sd_extra_networks_sha256s

    return templates.TemplateResponse(
        "tools/safetensors_import_helper.html",
        context,
    )


class DeleteSafetensorRequest(BaseModel):
    file_path: str


@router.post("/delete_safetensor")
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
