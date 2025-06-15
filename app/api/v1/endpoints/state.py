from typing import Annotated, Any

from fastapi import APIRouter, Depends, Security
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app import crud, models
from app.logic import state
from framework.core.api_key import get_api_key
from framework.core.db import get_db
from framework.routes.restrict_to_env import restrict_to


# Create a router that bypasses global auth
router = APIRouter(prefix="", include_in_schema=True)


@router.get("/state/instance", include_in_schema=True)
async def get_instance_state(
    db: Annotated[Session, Depends(get_db)],
    api_key: Annotated[str, Security(get_api_key)],
) -> dict[str, Any]:
    """Get the instance state.

    Args:
        db: Database session
        api_key: Validated API key

    Returns:
        Dictionary containing the instance state
    """
    instance_state = await state.get_instance_state()

    return instance_state.model_dump(mode="json")


@router.get("/state/network", include_in_schema=True)
@restrict_to("host")
async def get_network_state(
    db: Annotated[Session, Depends(get_db)],
    api_key: Annotated[str, Security(get_api_key)],
) -> Any:
    """Get the network state.

    Args:
        db: Database session
        api_key: Validated API key

    Returns:
        Dictionary containing the network state
    """
    network_state = await state.get_network_state_from_db()

    return network_state.model_dump(mode="json")


@router.post("/state/recieve-state", include_in_schema=True, response_class=JSONResponse)
@restrict_to("host")
async def recieve_state(
    state: models.InstanceStateRead,
    db: Annotated[Session, Depends(get_db)],
    api_key: Annotated[str, Security(get_api_key)],
) -> dict[str, Any]:
    """Recieve the instance state. Save it to the database.

    Args:
        state: Instance state
        db: Database session
        api_key: Validated API key

    Returns:
        Dictionary containing the instance state
    """
    instance_state = models.InstanceState.model_validate(state)
    db_instance_state = await crud.instance_state.get(db, id=instance_state.id)
    if db_instance_state:
        await crud.instance_state.update(
            db,
            db_obj=db_instance_state,
            obj_in=models.InstanceStateUpdate.model_validate(instance_state),
        )
    else:
        await crud.instance_state.create(
            db, obj_in=models.InstanceStateCreate.model_validate(instance_state)
        )

    return {"message": "Instance state saved"}
