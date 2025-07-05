from fastapi import APIRouter

from app.api.v1.endpoints import (
    app_manager,
    app_manager_ws,
    character,
    export,
    idle_watcher,
    sd_base_model,
    sd_checkpoint,
    sd_extra_network,
    state,
)
from app.api.v1.endpoints.scripts import (
    choose_best_epoch,
    fix_civitai_download_filenames,
    generate_xy_for_lora_epochs,
    rsync_files,
)
from framework.api.v1.endpoints import job_queue_ws, users
from framework.api.v1.endpoints.job_queue import router as job_queue_router


api_router = APIRouter()


api_router.include_router(state.router, tags=["State"])
api_router.include_router(job_queue_router, tags=["Job Queue"])
api_router.include_router(idle_watcher.router, tags=["Idle Watcher"])
api_router.include_router(export.router, tags=["Export"])
api_router.include_router(users.router, tags=["Users"])
api_router.include_router(character.router, tags=["Characters"])
api_router.include_router(sd_base_model.router, tags=["SD Base Models"])
api_router.include_router(sd_checkpoint.router, tags=["SD Checkpoints"])
api_router.include_router(sd_extra_network.router, tags=["SD Extra Networks"])
api_router.include_router(app_manager.router, tags=["App Manager"])
api_router.include_router(job_queue_ws.router, tags=["Job Queue WS"])
api_router.include_router(app_manager_ws.router, tags=["App Manager WS"])

# Scripts
api_router.include_router(generate_xy_for_lora_epochs.router, tags=["Scripts"])
api_router.include_router(choose_best_epoch.router, tags=["Scripts"])
api_router.include_router(fix_civitai_download_filenames.router, tags=["Scripts"])
api_router.include_router(rsync_files.router, tags=["Scripts"])
