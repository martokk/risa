from typing import TYPE_CHECKING

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
    pass


class SDCheckpointUpdate(SDCheckpointBase):
    pass


class SDCheckpointRead(SDCheckpointBase):
    pass
