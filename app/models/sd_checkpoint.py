from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import root_validator
from sqlmodel import Field, Relationship, SQLModel


if TYPE_CHECKING:
    from .sd_base_model import SDBaseModel


class SDCheckpointBase(SQLModel):
    id: str = Field(default=None, primary_key=True, unique=True)
    name: str = Field(default=None)
    local_file_path: str | None = Field(default=None)
    remote_file_path: str | None = Field(default=None)
    is_realistic: bool = Field(default=False)
    sd_base_model_id: str = Field(default=None, foreign_key="sdbasemodel.id")


class SDCheckpoint(SDCheckpointBase, table=True):
    sd_base_model: "SDBaseModel" = Relationship(back_populates="sd_checkpoints")


class SDCheckpointCreate(SDCheckpointBase):
    @root_validator(pre=True)
    @classmethod
    def generate_id(cls, values: dict[str, Any]) -> dict[str, Any]:
        if values.get("id") is None:
            name = values.get("name")
            local_file_path_value = values.get("local_file_path")

            safetensors_name = Path(local_file_path_value).stem if local_file_path_value else None

            if not name and not safetensors_name:
                raise ValueError(
                    "name or safetensors_name(local_file_path) must be provided to generate an ID"
                )

            id_raw = safetensors_name if safetensors_name else name
            id = id_raw.replace(" ", "_").replace("/", "").replace("\\", "").replace(":", "_")

            values["id"] = id
        return values


class SDCheckpointUpdate(SDCheckpointBase):
    pass


class SDCheckpointRead(SDCheckpointBase):
    pass
