from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .sd_base_model import SDBaseModel


class SDCheckpointBase(SQLModel):
    id: str = Field(default=None, primary_key=True, unique=True)
    name: str = Field(default=None)
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
