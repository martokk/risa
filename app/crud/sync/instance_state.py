from app import models
from framework.crud.sync import base


class InstanceStateCRUD(
    base.BaseCRUDSync[
        models.InstanceState,
        models.InstanceStateCreate,
        models.InstanceStateUpdate,
    ]
):
    """CRUD operations for InstanceState."""

    pass


instance_state = InstanceStateCRUD(model=models.InstanceState)
