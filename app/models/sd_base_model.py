from sqlmodel import SQLModel, Field, Relationship
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .sd_checkpoint import SDCheckpoint
    from .sd_extra_networks import SDExtraNetwork


class SDBaseModelBase(SQLModel):
    id: str = Field(default=None, primary_key=True, unique=True)
    name: str = Field(default=None)


class SDBaseModel(SDBaseModelBase, table=True):
    sd_checkpoints: List["SDCheckpoint"] = Relationship(back_populates="sd_base_model")
    sd_extra_networks: List["SDExtraNetwork"] = Relationship(
        back_populates="sd_base_model"
    )


class SDBaseModelCreate(SDBaseModelBase):
    pass


class SDBaseModelUpdate(SDBaseModelBase):
    pass


class SDBaseModelRead(SDBaseModelBase):
    pass
