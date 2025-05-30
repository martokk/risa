from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import root_validator
from safetensors import safe_open
from sqlmodel import JSON, Column, Field, Relationship, SQLModel


if TYPE_CHECKING:
    from .character import Character
    from .sd_base_model import SDBaseModel
    from .sd_checkpoint import SDCheckpoint


class SDExtraNetworkBase(SQLModel):
    id: str | None = Field(default=None, primary_key=True, index=True)
    sd_base_model_id: str = Field(foreign_key="sdbasemodel.id")
    character_id: str = Field(foreign_key="character.id")
    lora_path: str | None = Field(default=None, description="The path to the LORA file")
    lora_tag: str | None = Field(default=None, description="The LORA tag (ie. '<lora:XXXX:1>')")
    lora_sha256: str | None = Field(default=None, description="The SHA256 hash of the LORA file")
    trigger: str | None = Field(default=None, description="The trigger words for the lora")
    only_realistic: bool = Field(default=False, description="Only use on realistic models")
    only_nonrealistic: bool = Field(default=False, description="Only use on non-realistic models")
    only_checkpoints: list["SDCheckpoint"] = Field(
        default=[],
        description="Only use on these models (ie. 'ponyRealism_V21')",
        sa_column=Column(JSON),
    )
    exclude_checkpoints: list["SDCheckpoint"] = Field(
        default=[],
        description="Do not use on these models (ie. 'ponyRealism_V21')",
        sa_column=Column(JSON),
    )

    @property
    def safetensors_name(self) -> str | None:
        if self.lora_tag:
            return self.lora_tag.split(":")[1]
        return None


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
            lora_tag_value = values.get("lora_tag")
            trigger_value = values.get("trigger")

            if not lora_tag_value and not trigger_value:
                raise ValueError("lora_tag or trigger must be provided to generate an ID")

            safetensors_name = None
            if isinstance(lora_tag_value, str) and lora_tag_value.strip():
                try:
                    safetensors_name = lora_tag_value.split(":")[1]
                except IndexError:
                    raise ValueError(
                        f"Invalid lora_tag format: {lora_tag_value}. Expected format like '<lora:NAME:1>'."
                    )

            character_id = values.get("character_id")
            sd_base_model_id = values.get("sd_base_model_id")

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
from .sd_checkpoint import SDCheckpoint


SDExtraNetworkBase.update_forward_refs()
SDExtraNetwork.update_forward_refs()
SDExtraNetworkCreate.update_forward_refs()
SDExtraNetworkUpdate.update_forward_refs()
SDExtraNetworkRead.update_forward_refs()
