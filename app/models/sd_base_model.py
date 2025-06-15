from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel


if TYPE_CHECKING:
    from .sd_checkpoint import SDCheckpoint
    from .sd_extra_networks import SDExtraNetwork


class SDBaseModelBase(SQLModel):
    id: str = Field(default=None, primary_key=True, unique=True)
    name: str = Field(default=None)


class SDBaseModel(SDBaseModelBase, table=True):
    sd_checkpoints: list["SDCheckpoint"] = Relationship(back_populates="sd_base_model")
    sd_extra_networks: list["SDExtraNetwork"] = Relationship(back_populates="sd_base_model")


class SDBaseModelCreate(SDBaseModelBase):
    pass


class SDBaseModelUpdate(SDBaseModelBase):
    pass


class SDBaseModelRead(SDBaseModelBase):
    pass
