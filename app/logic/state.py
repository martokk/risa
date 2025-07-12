from datetime import datetime, timezone

from sqlmodel import Session

from app import crud, models, settings
from app.logic.runpod import (
    get_runpod_gpu_name,
    get_runpod_pod_id,
    get_runpod_public_ip,
    get_runpod_tcp_port_22,
)
from app.models.core.state import InstanceState, NetworkState
from vcore.backend.core.db import get_db_context
from vcore.backend.utils.system_status import get_cpu_stats, get_disk_stats, get_gpu_stats


async def _get_instance_state() -> InstanceState:
    id = settings.ENV_NAME
    last_updated = datetime.now(tz=timezone.utc)
    project_name = settings.PROJECT_NAME
    base_url = settings.BASE_URL
    base_domain = settings.BASE_DOMAIN

    # Theme
    accent = settings.ACCENT

    # System Status
    gpu_stats = get_gpu_stats()
    gpu_usage = gpu_stats["gpu_usage"]
    gpu_memory_used = gpu_stats["gpu_memory_used"]

    cpu_stats = get_cpu_stats()
    cpu_usage = cpu_stats["cpu_usage"]

    disk_stats = get_disk_stats()
    total_disk_space = disk_stats["total_disk_space"]
    used_disk_space = disk_stats["used_disk_space"]
    free_disk_space = disk_stats["free_disk_space"]
    disk_usage = disk_stats["disk_usage"]

    # Runpod
    runpod_gpu_name = get_runpod_gpu_name()
    runpod_pod_id = get_runpod_pod_id()
    runpod_public_ip = get_runpod_public_ip()
    runpod_tcp_port_22 = get_runpod_tcp_port_22()

    public_ip = None
    if id == "playground":
        public_ip = runpod_public_ip
    if id == "host":
        public_ip = base_domain.split(":")[0]

    return InstanceState(
        id=id,
        last_updated=last_updated,
        project_name=project_name,
        base_url=base_url,
        public_ip=public_ip,
        accent=accent,
        gpu_usage=gpu_usage,
        gpu_memory_used=gpu_memory_used,
        cpu_usage=cpu_usage,
        total_disk_space=total_disk_space,
        used_disk_space=used_disk_space,
        free_disk_space=free_disk_space,
        disk_usage=disk_usage,
        runpod_gpu_name=runpod_gpu_name,
        runpod_pod_id=runpod_pod_id,
        runpod_public_ip=runpod_public_ip,
        runpod_tcp_port_22=runpod_tcp_port_22,
    )


# async def post_instance_state_to_host(instance_state: InstanceState) -> None:
#     """
#     DEPRECATED: Use save_instance_state_to_db instead

#     Post this instance state to the Risa(Host) API Endpoint"""
#     try:
#         async with httpx.AsyncClient() as client:
#             await client.post(
#                 f"{RISA_HOST_BASE_URL}/api/v1/state/recieve-state",
#                 headers={"X-API-Key": settings.EXPORT_API_KEY},
#                 json=models.InstanceStateRead.model_validate(instance_state).model_dump(
#                     mode="json"
#                 ),
#             )
#     except Exception as e:
#         logger.error(f"Failed to post the instance state to the host api: {e}")


async def save_instance_state_to_db(db: Session, instance_state: InstanceState) -> None:
    instance_state = models.InstanceState.model_validate(instance_state)
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


async def get_instance_state() -> InstanceState:
    return await update_instance_state()


async def update_instance_state() -> InstanceState:
    instance_state = await _get_instance_state()

    with get_db_context() as db:
        await save_instance_state_to_db(db, instance_state)
    return instance_state


def get_network_state(db: Session) -> NetworkState:
    dev = crud.instance_state.sync.get(db, id="dev")
    local = crud.instance_state.sync.get(db, id="local")
    playground = crud.instance_state.sync.get(db, id="playground")
    host = crud.instance_state.sync.get(db, id="host")
    return NetworkState(
        last_updated=datetime.now(tz=timezone.utc),
        dev=dev,
        local=local,
        playground=playground,
        host=host,
    )


# async def get_network_state_from_host() -> NetworkState | None:
#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.get(
#                 f"{RISA_HOST_BASE_URL}/api/v1/state/network",
#                 headers={"X-API-Key": settings.EXPORT_API_KEY},
#             )
#         return NetworkState.model_validate(response.json())
#     except Exception as e:
#         logger.error(f"Failed to get the network state from the host api: {e}")
#         return None


def is_env_name_running(env_name: str) -> bool:
    with get_db_context() as db:
        instance_state = crud.sync.instance_state.get(db, id=env_name)
        if instance_state:
            return instance_state.is_running
        return False
