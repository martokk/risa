import re
from pathlib import Path

from pydantic import BaseModel

from app.models import settings
from app.models.sd_extra_networks import Safetensor
from app.paths import HUB_MODELS_PATH


class HubBaseModel(BaseModel):
    name: str
    path: Path
    checkpoints_path: Path | None
    lora_path: Path | None
    safetensors_checkpoints: list[Safetensor] = []
    safetensors_loras: list[Safetensor] = []
    sd_base_model_id: str | None = None

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._import_safetensors()

    def _import_safetensors(self) -> None:
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


class Hub(BaseModel):
    hub_base_models: list[HubBaseModel]
    hub_env_name: str


def _get_hub_base_models() -> list[HubBaseModel]:
    """Get all safetensors in the hub."""
    hub_bases_models = []

    # FLUX
    flux_path = HUB_MODELS_PATH / "FLUX"
    hub_flux = HubBaseModel(
        name="FLUX",
        path=flux_path,
        checkpoints_path=flux_path / "checkpoints",
        lora_path=flux_path / "loras",
        sd_base_model_id="flux",
    )
    hub_bases_models.append(hub_flux)

    # Hunyuan
    hunyuan_path = HUB_MODELS_PATH / "Hunyuan"
    hub_hunyuan = HubBaseModel(
        name="Hunyuan",
        path=hunyuan_path,
        checkpoints_path=None,
        lora_path=hunyuan_path / "Lora",
        sd_base_model_id="hunyuan",
    )
    hub_bases_models.append(hub_hunyuan)

    # SDXL: SDXL
    sdxl_path = HUB_MODELS_PATH / "SDXL"
    hub_sdxl_sdxl = HubBaseModel(
        name="SDXL: SDXL",
        path=sdxl_path,
        checkpoints_path=sdxl_path / "base_models" / "sdxl",
        lora_path=sdxl_path / "loras" / "sdxl",
        sd_base_model_id="sdxl",
    )
    hub_bases_models.append(hub_sdxl_sdxl)

    # SDXL: Pony
    sdxl_path = HUB_MODELS_PATH / "SDXL"
    hub_sdxl_pony = HubBaseModel(
        name="SDXL: Pony",
        path=sdxl_path,
        checkpoints_path=sdxl_path / "base_models" / "pony",
        lora_path=sdxl_path / "loras" / "pony",
        sd_base_model_id="pony",
    )
    hub_bases_models.append(hub_sdxl_pony)

    # SDXL: Illustrious
    sdxl_path = HUB_MODELS_PATH / "SDXL"
    hub_sdxl_illustrious = HubBaseModel(
        name="Illustrious",
        path=sdxl_path,
        checkpoints_path=sdxl_path / "base_models" / "illustrious",
        lora_path=sdxl_path / "loras" / "illustrious",
        sd_base_model_id="illustrious",
    )
    hub_bases_models.append(hub_sdxl_illustrious)

    # WAN_2_1 Video
    wan_2_1_video_path = HUB_MODELS_PATH / "WAN_2_1 Video"
    hub_wan_2_1_video = HubBaseModel(
        name="WAN_2_1 Video",
        path=wan_2_1_video_path,
        checkpoints_path=None,
        lora_path=wan_2_1_video_path / "Lora",
        sd_base_model_id="wan_2_1_video",
    )
    hub_bases_models.append(hub_wan_2_1_video)

    return hub_bases_models


def get_hub() -> Hub:
    """Get the hub."""
    hub_base_models = _get_hub_base_models()
    hub = Hub(hub_base_models=hub_base_models, hub_env_name=settings.ENV_NAME)
    return hub
