from fastapi import APIRouter

from app.api.v1.endpoints import (
    app_manager,
    character,
    export,
    idle_watcher,
    sd_base_model,
    sd_checkpoint,
    sd_extra_network,
    state,
)
from framework.api.v1.endpoints import job_queue_ws, users
from framework.api.v1.endpoints.job_queue import router as job_queue_router
from framework.routes.restrict_to_env import restrict_to


api_router = APIRouter()


def include_state_router():
    api_router.include_router(state.router, tags=["State"])


def include_job_queue_router():
    api_router.include_router(job_queue_router, tags=["Job Queue"])


@restrict_to("playground")
def include_idle_watcher_router():
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


def include_job_queue_ws_router():
    api_router.include_router(job_queue_ws.router, tags=["Job Queue WS"])


include_state_router()
include_job_queue_router()
include_idle_watcher_router()
include_export_router()
include_users_router()
include_character_router()
include_sd_base_model_router()
include_sd_checkpoint_router()
include_sd_extra_network_router()
include_app_manager_router()
include_job_queue_ws_router()
