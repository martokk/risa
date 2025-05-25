from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from typing import TYPE_CHECKING, Any
from pydantic import root_validator

if TYPE_CHECKING:
    from .sd_base_model import SDBaseModel
    from .character import Character
    from .sd_checkpoint import SDCheckpoint


class SDExtraNetworkBase(SQLModel):
    id: str | None = Field(default=None, primary_key=True, index=True)
    sd_base_model_id: str = Field(foreign_key="sdbasemodel.id")
    character_id: str = Field(foreign_key="character.id")
    lora_tag: str | None = Field(
        default=None, description="The LORA tag (ie. '<lora:XXXX:1>')"
    )
    trigger: str | None = Field(
        default=None, description="The trigger words for the lora"
    )
    only_realistic: bool = Field(
        default=False, description="Only use on realistic models"
    )
    only_nonrealistic: bool = Field(
        default=False, description="Only use on non-realistic models"
    )
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


class SDExtraNetwork(SDExtraNetworkBase, table=True):
    sd_base_model: "SDBaseModel" = Relationship(back_populates="sd_extra_networks")
    character: "Character" = Relationship(back_populates="sd_extra_networks")


class SDExtraNetworkCreate(SDExtraNetworkBase):
    @root_validator(pre=True)
    @classmethod
    def generate_id(cls, values: dict[str, Any]) -> dict[str, Any]:
        if values is None:
            return values
        if values.get("id") is None:
            if not values.get("lora_tag") and not values.get("trigger"):
                raise ValueError("lora_tag or trigger must be provided")
            safetensors_name = (
                values.get("lora_tag").split(":")[1] if values.get("lora_tag") else None
            )
            values["id"] = (
                f"{values.get('character_id')}_{safetensors_name}_{values.get('sd_base_model_id')}"
            )
        return values


class SDExtraNetworkUpdate(SDExtraNetworkBase):
    pass


class SDExtraNetworkRead(SDExtraNetworkBase):
    pass


# Resolve forward references by ensuring the referenced models are imported
# and then calling update_forward_refs() on each model that uses them.
from .sd_base_model import SDBaseModel
from .character import Character
from .sd_checkpoint import SDCheckpoint

SDExtraNetworkBase.update_forward_refs()
SDExtraNetwork.update_forward_refs()
SDExtraNetworkCreate.update_forward_refs()
SDExtraNetworkUpdate.update_forward_refs()
SDExtraNetworkRead.update_forward_refs()
