from pathlib import Path
from typing import Any

from sqlmodel import Session

from app import models
from vcore.backend.crud.base import BaseCRUD


class CharacterCRUD(
    BaseCRUD[
        models.Character,
        models.CharacterCreate,
        models.CharacterUpdate,
    ]
):
    """CRUD operations for Character."""

    async def add_extra_network(
        self,
        db: Session,
        id: str,
        sd_base_model_id: str,
        trained_on_checkpoint: str | None = None,
        hub_file_path: str | None = None,
        download_url: str | None = None,
        network: str | None = None,
        network_trigger: str | None = None,
        network_weight: float | None = None,
        sha256: str | None = None,
        only_realistic: bool = False,
        only_nonrealistic: bool = False,
        only_checkpoints: list[str] | None = None,
        exclude_checkpoints: list[str] | None = None,
    ) -> models.Character:
        if only_checkpoints is None:
            only_checkpoints = []
        if exclude_checkpoints is None:
            exclude_checkpoints = []
        db_character = await self.get_or_none(db, id=id)
        if not db_character:
            raise ValueError(f"Character with id '{id}' not found")

        safetensors_name = Path(hub_file_path).stem if hub_file_path else None
        if not safetensors_name:
            raise ValueError(
                "safetensors_name must be provided to generate an ID. Enter a Hub File Path."
            )

        extra_network_id = f"{db_character.id}_{safetensors_name}_{sd_base_model_id}"

        actual_extra_network: models.SDExtraNetwork | None = db.get(
            models.SDExtraNetwork, extra_network_id
        )

        if not actual_extra_network:
            extra_network_create_schema = models.SDExtraNetworkCreate(
                sd_base_model_id=sd_base_model_id,
                character_id=db_character.id,
                trained_on_checkpoint=trained_on_checkpoint,
                hub_file_path=hub_file_path,
                download_url=download_url,
                network=network,
                network_trigger=network_trigger,
                network_weight=network_weight,
                sha256=sha256,
                only_realistic=only_realistic,
                only_nonrealistic=only_nonrealistic,
                only_checkpoints=only_checkpoints,
                exclude_checkpoints=exclude_checkpoints,
            )
            actual_extra_network = models.SDExtraNetwork.model_validate(extra_network_create_schema)
            db.add(actual_extra_network)
        else:
            pass

        if actual_extra_network not in db_character.sd_extra_networks:
            db_character.sd_extra_networks.append(actual_extra_network)

        db.commit()

        db.refresh(db_character)
        db.refresh(actual_extra_network)

        return db_character

    async def get_dataset_tagger_tags(self, db: Session, character_id: str) -> dict[str, Any]:
        db_character = await self.get_or_none(db, id=character_id)
        if not db_character:
            raise ValueError(f"Character with id '{character_id}' not found")

        return db_character.model_dump()


character = CharacterCRUD(model=models.Character)
