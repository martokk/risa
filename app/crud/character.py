from sqlmodel import Session
from .base import BaseCRUD
import models


class CharacterCRUD(
    BaseCRUD[
        models.Character,
        models.CharacterCreate,
        models.CharacterUpdate,
    ]
):
    """CRUD operations for Character."""

    def add_extra_network(
        self,
        db: Session,
        id: str,
        sd_base_model_id: str,
        lora_tag: str | None = None,
        trigger: str | None = None,
        only_realistic: bool = False,
        only_nonrealistic: bool = False,
        only_checkpoints: list[str] = [],
        exclude_checkpoints: list[str] = [],
    ) -> models.Character:
        db_character = self.get_or_none(db, id=id)
        if not db_character:
            raise ValueError(f"Character with id '{id}' not found")

        safetensors_name = lora_tag.split(":")[1]
        extra_network_id = f"{db_character.id}_{safetensors_name}_{sd_base_model_id}"

        actual_extra_network: models.SDExtraNetwork | None = db.get(
            models.SDExtraNetwork, extra_network_id
        )

        if not actual_extra_network:
            extra_network_create_schema = models.SDExtraNetworkCreate(
                sd_base_model_id=sd_base_model_id,
                character_id=db_character.id,
                lora_tag=lora_tag,
                trigger=trigger,
                only_realistic=only_realistic,
                only_nonrealistic=only_nonrealistic,
                only_checkpoints=only_checkpoints,
                exclude_checkpoints=exclude_checkpoints,
            )
            actual_extra_network = models.SDExtraNetwork.model_validate(
                extra_network_create_schema
            )
            db.add(actual_extra_network)
        else:
            pass

        if actual_extra_network not in db_character.sd_extra_networks:
            db_character.sd_extra_networks.append(actual_extra_network)

        db.commit()

        db.refresh(db_character)
        db.refresh(actual_extra_network)

        return db_character


character = CharacterCRUD(model=models.Character)
