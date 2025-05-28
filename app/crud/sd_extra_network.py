from app import models

from .base import BaseCRUD


class SDExtraNetworkCRUD(
    BaseCRUD[
        models.SDExtraNetwork,
        models.SDExtraNetworkCreate,
        models.SDExtraNetworkUpdate,
    ]
):
    """CRUD operations for SDExtraNetwork."""

    pass


sd_extra_network = SDExtraNetworkCRUD(model=models.SDExtraNetwork)
