from sqlmodel import SQLModel, Field, Relationship
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .sd_extra_networks import SDExtraNetwork


class CharacterBase(SQLModel):
    id: str = Field(
        default=None, primary_key=True, unique=True
    )  # Made id a primary key
    name: str = Field(default="Default")
    race: str | None = Field(default=None)
    skin_color: str | None = Field(default=None)

    # Head attributes
    hair_color: str | None = Field(default=None)
    hair_style: str | None = Field(default=None)
    hair_length: str | None = Field(default=None)
    face_type: str | None = Field(default=None)
    eye_color: str | None = Field(default=None)
    makeup_type: str | None = Field(default=None)

    # Body attributes
    body_type: str | None = Field(default=None)
    breasts_type: str | None = Field(default=None)
    breasts_size: str | None = Field(default=None)
    nipples_type: str | None = Field(default=None)

    # Other physical attributes
    hands_type: str | None = Field(default=None)
    hips_type: str | None = Field(default=None)
    ass_type: str | None = Field(default=None)
    pussy_type: str | None = Field(default=None)
    legs_type: str | None = Field(default=None)
    feet_type: str | None = Field(default=None)

    # Clothing attributes
    clothing_head: str | None = Field(default=None)
    clothing_upper_body: str | None = Field(default=None)
    clothing_lower_body: str | None = Field(default=None)
    clothing_feet: str | None = Field(default=None)


class Character(CharacterBase, table=True):
    sd_extra_networks: List["SDExtraNetwork"] = Relationship(
        back_populates="character", sa_relationship_kwargs={"lazy": "selectin"}
    )

    def has_extra_networks_for_base_model(self, base_model_str: str) -> bool:
        for extra_network in self.sd_extra_networks:
            if base_model_str in extra_network.sd_base_model.id:
                return True
        return False

    def get_extra_networks_for_base_model(
        self, base_model_str: str
    ) -> list["SDExtraNetwork"]:
        return [
            extra_network
            for extra_network in self.sd_extra_networks
            if base_model_str in extra_network.sd_base_model.id
        ]


class CharacterCreate(CharacterBase):
    pass


class CharacterUpdate(CharacterBase):
    pass


class CharacterRead(CharacterBase):
    pass
