from app import models

from .base import BaseCRUD


class SDCheckpointCRUD(
    BaseCRUD[
        models.SDCheckpoint,
        models.SDCheckpointCreate,
        models.SDCheckpointUpdate,
    ]
):
    """CRUD operations for SDCheckpoint."""

    pass


sd_checkpoint = SDCheckpointCRUD(model=models.SDCheckpoint)
