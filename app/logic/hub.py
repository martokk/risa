import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from safetensors import safe_open

from app.paths import HUB_MODELS_PATH


class SafetensorJSON(BaseModel):
    path: Path
    activation_text: str | None = None
    sha256: str | None = None

    def __init__(self, path: Path):
        super().__init__(path=path)
        if self.path.exists():
            with open(self.path) as f:
                json_data = json.load(f)
                self.activation_text = json_data.get("activation_text")
                self.sha256 = json_data.get("sha256").upper()


class Safetensor(BaseModel):
    path: Path

    @property
    def name(self) -> str:
        return self.path.stem

    @property
    def id(self) -> str:
        return self.name.lower().replace(" ", "_")

    @property
    def json_file_path(self) -> Path | None:
        json_file_path = Path(str(self.path).replace(".safetensors", ".json"))
        if json_file_path.exists():
            return json_file_path
        return None

    @property
    def json_file(self) -> SafetensorJSON | None:
        if self.json_file_path:
            return SafetensorJSON(path=self.json_file_path)
        return None

    def generate_sha256(self) -> str | None:
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
            if self.json_file_path and self.json_file_path.exists():
                with open(self.json_file_path) as f:
                    existing_json_data = json.load(f)

            # Update only the sha256 field
            existing_json_data["sha256"] = sha256.upper()

            # Save updated JSON data
            json_file_path = Path(str(self.path).replace(".safetensors", ".json"))
            with open(json_file_path, "w") as f:
                json.dump(existing_json_data, f)

            return sha256.upper()
        return None

    @property
    def sha256(self) -> str | None:
        if self.json_file:
            return self.json_file.sha256.upper() if self.json_file.sha256 else None

        return None

    @property
    def size(self) -> int:
        return self.path.stat().st_size

    @property
    def metadata(self) -> dict[str, Any] | None:
        if self.path and self.path.exists():
            with safe_open(self.path, framework="pt") as f:
                metadata = f.metadata()
                if metadata:
                    return dict(metadata)
        return None


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
    hub = Hub(hub_base_models=hub_base_models)
    return hub
