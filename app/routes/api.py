from fastapi import APIRouter

from app.api.v1.endpoints import (
    app_manager,
    character,
    export,
    idle_watcher,
    job_queue,
    sd_base_model,
    sd_checkpoint,
    sd_extra_network,
    state,
    users,
)
from app.routes.restrict_to_env import restrict_to


api_router = APIRouter()

api_router.include_router(state.router, tags=["State"])
api_router.include_router(job_queue.router, tags=["Job Queue"])
api_router.include_router(idle_watcher.router, tags=["Idle Watcher"])


@restrict_to("host")
def include_export_router():
    api_router.include_router(export.router, tags=["Export"])


@restrict_to("host")
def include_users_router():
    api_router.include_router(users.router, tags=["Users"])


@restrict_to("host")
def include_character_router():
    api_router.include_router(character.router, tags=["Characters"])


@restrict_to("host")
def include_sd_base_model_router():
    api_router.include_router(sd_base_model.router, tags=["SD Base Models"])


@restrict_to("host")
def include_sd_checkpoint_router():
    api_router.include_router(sd_checkpoint.router, tags=["SD Checkpoints"])


@restrict_to("host")
def include_sd_extra_network_router():
    api_router.include_router(sd_extra_network.router, tags=["SD Extra Networks"])


@restrict_to("playground")
def include_app_manager_router():
    api_router.include_router(app_manager.router, tags=["App Manager"])
