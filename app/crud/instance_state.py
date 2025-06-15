from app import models
from framework.crud.base import BaseCRUD


class InstanceStateCRUD(
    BaseCRUD[
        models.InstanceState,
        models.InstanceStateCreate,
        models.InstanceStateUpdate,
    ]
):
    """CRUD operations for InstanceState."""

    pass


instance_state = InstanceStateCRUD(model=models.InstanceState)
