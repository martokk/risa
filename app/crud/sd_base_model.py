from sqlmodel import Session

from app import models

from .base import BaseCRUD


class SDBaseModelCRUD(
    BaseCRUD[
        models.SDBaseModel,
        models.SDBaseModelCreate,
        models.SDBaseModelUpdate,
    ]
):
    """CRUD operations for SDBaseModel."""

    async def add_checkpoint(
        self,
        db: Session,
        id: str,
        checkpoint_id: str,
        checkpoint_name: str,
        is_realistic: bool,
    ) -> models.SDBaseModel:
        db_base_model = await self.get_or_none(db, id=id)
        if not db_base_model:
            raise ValueError(f"SDBaseModel with id '{id}' not found")

        actual_checkpoint: models.SDCheckpoint | None = db.get(models.SDCheckpoint, checkpoint_id)

        if not actual_checkpoint:
            checkpoint_create_schema = models.SDCheckpointCreate(
                id=checkpoint_id,
                name=checkpoint_name,
                is_realistic=is_realistic,
            )
            actual_checkpoint = models.SDCheckpoint.model_validate(checkpoint_create_schema)
            db.add(actual_checkpoint)
        else:
            pass

        if actual_checkpoint not in db_base_model.sd_checkpoints:
            db_base_model.sd_checkpoints.append(actual_checkpoint)

        db.commit()

        db.refresh(db_base_model)
        db.refresh(actual_checkpoint)

        return db_base_model

    async def add_extra_network(
        self,
        db: Session,
        id: str,
        character_id: str,
        lora_tag: str | None = None,
        trigger: str | None = None,
        only_realistic: bool = False,
        only_nonrealistic: bool = False,
        only_checkpoints: list[models.SDCheckpoint] = [],
        exclude_checkpoints: list[models.SDCheckpoint] = [],
    ) -> models.SDBaseModel:
        db_base_model = await self.get_or_none(db, id=id)
        if not db_base_model:
            raise ValueError(f"SDBaseModel with id '{id}' not found")

        if not lora_tag:
            # Or handle this case as an error, depending on requirements
            raise ValueError("lora_tag cannot be None when adding an extra network")

        safetensors_name = lora_tag.split(":")[1]
        extra_network_id = f"{character_id}_{safetensors_name}_{db_base_model.id}"

        actual_extra_network: models.SDExtraNetwork | None = db.get(
            models.SDExtraNetwork, extra_network_id
        )

        if not actual_extra_network:
            extra_network_create_schema = models.SDExtraNetworkCreate(
                character_id=character_id,
                lora_tag=lora_tag,
                trigger=trigger,
                only_realistic=only_realistic,
                only_nonrealistic=only_nonrealistic,
                only_checkpoints=only_checkpoints,
                exclude_checkpoints=exclude_checkpoints,
                sd_base_model_id=db_base_model.id,
            )
            actual_extra_network = models.SDExtraNetwork.model_validate(extra_network_create_schema)
            db.add(actual_extra_network)
        else:
            pass

        if actual_extra_network not in db_base_model.sd_extra_networks:
            db_base_model.sd_extra_networks.append(actual_extra_network)

        db.commit()

        db.refresh(db_base_model)
        db.refresh(actual_extra_network)

        return db_base_model


sd_base_model = SDBaseModelCRUD(model=models.SDBaseModel)
