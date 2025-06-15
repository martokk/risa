from typing import TYPE_CHECKING

from pydantic import validator
from sqlmodel import Field, Relationship, SQLModel


if TYPE_CHECKING:
    from .sd_extra_networks import SDExtraNetwork


class CharacterBase(SQLModel):
    id: str = Field(default=None, primary_key=True, unique=True)  # Made id a primary key
    person_name: str | None = Field(default=None)
    character_name1: str | None = Field(default=None)
    character_name2: str | None = Field(default=None)
    character_name3: str | None = Field(default=None)
    is_known: bool = Field(default=False)
    age_group: str | None = Field(default=None)
    race: str | None = Field(default=None)
    skin_color: str | None = Field(default=None)

    @validator("id")
    def trim_id(cls, v: str | None) -> str | None:
        """Ensure ID has no leading/trailing whitespace."""
        if v is not None:
            return v.strip()
        return v

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

    @property
    def is_incomplete(self) -> bool:
        return all(
            getattr(self, attr) is None
            for attr in [
                "age_group",
                "race",
                "skin_color",
                "hair_color",
                "hair_style",
                "hair_length",
                "face_type",
                "eye_color",
                "makeup_type",
                "body_type",
                "breasts_type",
                "breasts_size",
                "nipples_type",
                "hands_type",
                "hips_type",
                "ass_type",
                "pussy_type",
                "legs_type",
                "feet_type",
                "clothing_head",
                "clothing_upper_body",
                "clothing_lower_body",
                "clothing_feet",
            ]
        )

    @property
    def name(self) -> str:
        if not self.person_name and not self.character_name1:
            raise ValueError(
                f"Person name or character name is required for Character(id={self.id})."
            )
        if not self.person_name and self.character_name1:
            return self.character_name1

        name = self.person_name

        character_names = []
        if self.character_name1:
            character_names.append(self.character_name1)
        if self.character_name2:
            character_names.append(self.character_name2)
        if self.character_name3:
            character_names.append(self.character_name3)
        if character_names:
            name += f" ({', '.join(character_names)})"
        return name


class Character(CharacterBase, table=True):
    sd_extra_networks: list["SDExtraNetwork"] = Relationship(
        back_populates="character", sa_relationship_kwargs={"lazy": "selectin"}
    )

    def has_extra_networks_for_base_model(self, base_model_str: str) -> bool:
        for extra_network in self.sd_extra_networks:
            if base_model_str in extra_network.sd_base_model.id:
                return True
        return False

    def get_extra_networks_for_base_model(self, base_model_str: str) -> list["SDExtraNetwork"]:
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
