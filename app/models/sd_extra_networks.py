import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, root_validator
from safetensors import safe_open
from sqlmodel import JSON, Column, Field, Relationship, SQLModel

from app.models.settings import get_settings
from framework.paths import ENV_FILE


if TYPE_CHECKING:
    from .character import Character
    from .sd_base_model import SDBaseModel


settings = get_settings(env_file_path=ENV_FILE)


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
                self.sha256 = json_data.get("sha256")


class Safetensor(BaseModel):
    path: Path
    env_name: str = settings.ENV_NAME

    @property
    def name(self) -> str:
        return self.path.stem

    @property
    def id(self) -> str:
        return self.name.lower().replace(" ", "_")

    @property
    def json_file_path(self) -> Path | None:
        if self.env_name in ["local", "dev"]:
            json_file_path = Path(str(self.path).replace(".safetensors", ".json"))
            if json_file_path.exists():
                return json_file_path
        return None

    @property
    def json_file(self) -> SafetensorJSON | None:
        if self.env_name in ["local", "dev"]:
            if self.json_file_path:
                return SafetensorJSON(path=self.json_file_path)
        return None

    @property
    def sha256(self) -> str | None:
        if self.env_name != "local" and self.env_name != "dev":
            return None

        if self.json_file:
            return self.json_file.sha256

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
            existing_json_data["sha256"] = sha256

            # Save updated JSON data
            json_file_path = Path(str(self.path).replace(".safetensors", ".json"))
            with open(json_file_path, "w") as f:
                json.dump(existing_json_data, f)

            return sha256
        return None

    @property
    def size(self) -> int:
        if self.env_name != "local" and self.env_name != "dev":
            return 0
        return self.path.stat().st_size

    @property
    def metadata(self) -> dict[str, Any] | None:
        if self.path and self.path.exists():
            with safe_open(self.path, framework="pt") as f:
                metadata = f.metadata()
                if metadata:
                    return dict(metadata)
        return None


class SDExtraNetworkBase(SQLModel):
    id: str | None = Field(default=None, primary_key=True, index=True)
    sd_base_model_id: str = Field(foreign_key="sdbasemodel.id")
    character_id: str = Field(foreign_key="character.id")
    trained_on_checkpoint: str | None = Field(
        default=None, description="The checkpoint the network was trained on"
    )
    local_file_path: str | None = Field(default=None)
    remote_file_path: str | None = Field(default=None)

    network: str | None = Field(default=None, description="The name of the network (ie. 'lora')")
    network_trigger: str | None = Field(default=None, description="The trigger words for the lora")
    network_weight: float | None = Field(default=1, description="The default weight of the lora")

    sha256: str | None = Field(default=None, description="The SHA256 hash of the Safetensor file")

    only_realistic: bool = Field(default=False, description="Only use on realistic models")
    only_nonrealistic: bool = Field(default=False, description="Only use on non-realistic models")
    only_checkpoints: list[str] = Field(
        default=[],
        description="Only use on these models (ie. 'ponyRealism_V21')",
        sa_column=Column(JSON),
    )
    exclude_checkpoints: list[str] = Field(
        default=[],
        description="Do not use on these models (ie. 'ponyRealism_V21')",
        sa_column=Column(JSON),
    )

    @property
    def safetensors(self) -> Safetensor | None:
        if self.local_file_path:
            return Safetensor(path=Path(self.local_file_path))
        return None

    @property
    def safetensors_name(self) -> str | None:
        return (
            self.safetensors.name
            if self.safetensors
            else Path(self.local_file_path).stem
            if self.local_file_path
            else None
        )

    @property
    def name(self) -> str:
        return (
            f"{self.character_id} - {self.safetensors_name if self.safetensors_name else self.id}"
        )

    @property
    def network_tag(self) -> str:
        if self.network and self.safetensors and self.safetensors.name and self.network_weight:
            return f"<{self.network}:{self.safetensors.name}:{'1' if self.network_weight == 1 else self.network_weight}>"
        raise ValueError(
            "network, safetensors_name, and network_weight must be provided to generate a network tag"
        )

    @property
    def network_tag_and_trigger(self) -> str:
        if self.network and self.network_trigger:
            return f"{self.network_tag} {self.network_trigger}"
        raise ValueError(
            "network and network_trigger must be provided to generate a network tag and trigger"
        )


class SDExtraNetwork(SDExtraNetworkBase, table=True):
    sd_base_model: "SDBaseModel" = Relationship(
        back_populates="sd_extra_networks", sa_relationship_kwargs={"lazy": "selectin"}
    )
    character: "Character" = Relationship(
        back_populates="sd_extra_networks", sa_relationship_kwargs={"lazy": "selectin"}
    )

    def get_id(self):
        return f"{self.character.id}_{self.safetensors_name}_{self.sd_base_model.id}"

    def __str__(self):
        return f"{self.character_id} - {self.safetensors_name} ({self.sd_base_model_id})"


class SDExtraNetworkCreate(SDExtraNetworkBase):
    @root_validator(pre=True)
    @classmethod
    def generate_id(cls, values: dict[str, Any]) -> dict[str, Any]:
        if values.get("id") is None:
            network_trigger_value = values.get("network_trigger")
            local_file_path_value = values.get("local_file_path")
            character_id = values.get("character_id")
            sd_base_model_id = values.get("sd_base_model_id")

            safetensors_name = Path(local_file_path_value).stem if local_file_path_value else None

            if not network_trigger_value:
                raise ValueError("network_trigger must be provided to generate an ID")

            if not safetensors_name:
                raise ValueError(
                    "safetensors_name must be provided to generate an ID. Enter a local file path."
                )

            if not character_id or not sd_base_model_id:
                raise ValueError(
                    "character_id and sd_base_model_id must be provided to generate an ID"
                )

            values["id"] = f"{character_id}_{safetensors_name}_{sd_base_model_id}"
        return values


class SDExtraNetworkUpdate(SDExtraNetworkBase):
    pass


class SDExtraNetworkRead(SDExtraNetworkBase):
    pass


# Resolve forward references by ensuring the referenced models are imported
# and then calling update_forward_refs() on each model that uses them.
from .character import Character
from .sd_base_model import SDBaseModel


SDExtraNetworkBase.update_forward_refs()
SDExtraNetwork.update_forward_refs()
SDExtraNetworkCreate.update_forward_refs()
SDExtraNetworkUpdate.update_forward_refs()
SDExtraNetworkRead.update_forward_refs()
