from datetime import datetime, timezone

import httpx

from app import crud, logger, models, settings
from app.models.core.state import InstanceState, NetworkState
from framework.core.db import get_db
from framework.routes.restrict_to_env import restrict_to


async def _get_instance_state() -> InstanceState:
    id = settings.ENV_NAME
    last_updated = datetime.now(tz=timezone.utc)
    project_name = settings.PROJECT_NAME
    base_domain = settings.BASE_DOMAIN

    return InstanceState(
        id=id,
        last_updated=last_updated,
        project_name=project_name,
        base_domain=base_domain,
    )


async def post_instance_state_to_host(instance_state: InstanceState) -> None:
    """Post this instance state to the Risa(Host) API Endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.RISA_HOST_BASE_URL}/api/v1/state/recieve-state",
                headers={"X-API-Key": settings.EXPORT_API_KEY},
                json=models.InstanceStateRead.model_validate(instance_state).model_dump(
                    mode="json"
                ),
            )
    except Exception as e:
        logger.error(f"Failed to post the instance state to the host api: {e}")


async def get_instance_state() -> InstanceState:
    return await update_instance_state()


async def update_instance_state() -> InstanceState:
    instance_state = await _get_instance_state()
    await post_instance_state_to_host(instance_state)
    return instance_state


@restrict_to("host")
async def get_network_state_from_db() -> NetworkState:
    db = next(get_db())

    dev = await crud.instance_state.get(db, id="dev")
    local = await crud.instance_state.get(db, id="local")
    playground = await crud.instance_state.get(db, id="playground")
    host = await crud.instance_state.get(db, id="host")

    return NetworkState(
        last_updated=datetime.now(tz=timezone.utc),
        dev=dev,
        local=local,
        playground=playground,
        host=host,
    )


async def get_network_state_from_host() -> NetworkState | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.RISA_HOST_BASE_URL}/api/v1/state/network",
                headers={"X-API-Key": settings.EXPORT_API_KEY},
            )
        return NetworkState.model_validate(response.json())
    except Exception as e:
        logger.error(f"Failed to get the network state from the host api: {e}")
        return None
