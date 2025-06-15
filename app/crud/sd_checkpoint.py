from sqlmodel import Session

from app import models
from framework.crud.base import BaseCRUD

from .sd_extra_network import sd_extra_network as crud_sd_extra_network


class SDCheckpointCRUD(
    BaseCRUD[
        models.SDCheckpoint,
        models.SDCheckpointCreate,
        models.SDCheckpointUpdate,
    ]
):
    """CRUD operations for SDCheckpoint."""

    async def get_all_extra_networks_for_checkpoint(
        self, db: Session, checkpoint_id: str
    ) -> list[models.SDExtraNetwork]:
        """Get all extra networks for a checkpoint."""
        checkpoint = await self.get(db, id=checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint with id {checkpoint_id} not found.")

        base_model_extra_networks = await crud_sd_extra_network.get_multi(
            db=db, sd_base_model_id=checkpoint.sd_base_model_id, limit=1000
        )

        # Filter out reaslistic/non-realistic extra networks
        if checkpoint.is_realistic:
            base_model_extra_networks = [
                extra_network
                for extra_network in base_model_extra_networks
                if not extra_network.only_nonrealistic
            ]
        else:
            base_model_extra_networks = [
                extra_network
                for extra_network in base_model_extra_networks
                if not extra_network.only_realistic
            ]

        return base_model_extra_networks

    async def get_all_excluded_extra_networks_for_checkpoint(
        self, db: Session, checkpoint_id: str
    ) -> list[models.SDExtraNetwork]:
        """Get all excluded extra networks for a checkpoint."""
        possible_checkpoints = await self.get_all_extra_networks_for_checkpoint(
            db=db, checkpoint_id=checkpoint_id
        )

        return [
            extra_network
            for extra_network in possible_checkpoints
            if checkpoint_id in extra_network.exclude_checkpoints
        ]


sd_checkpoint = SDCheckpointCRUD(model=models.SDCheckpoint)
