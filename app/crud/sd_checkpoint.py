from .base import BaseCRUD
import models


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
