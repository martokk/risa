from fastapi import APIRouter

from app.routes.views.character import character
from app.routes.views.dashboard import dashboard
from app.routes.views.root import root
from app.routes.views.sd_base_model import sd_base_model
from app.routes.views.sd_checkpoint import sd_checkpoint
from app.routes.views.sd_extra_network import sd_extra_network
from app.routes.views.state import state
from app.routes.views.tools import (
    dataset_tagger,
    safetensors_import_helper,
)
from app.routes.views.tools.scripts import fix_civitai_download_filenames
from vcore.backend.routes.views.jobs import job_scheduler, jobs
from vcore.backend.routes.views.login import login
from vcore.backend.routes.views.user import user


# Root routes
root_router = APIRouter()
root_router.include_router(root.router, tags=["Root"])
root_router.include_router(login.router, tags=["Logins"])
root_router.include_router(user.router, tags=["Users"])
root_router.include_router(jobs.router, tags=["Jobs"])
root_router.include_router(job_scheduler.router, tags=["Job Schedulers"])

# SD specific routes
root_router.include_router(sd_base_model.router, tags=["SD Base Models"])
root_router.include_router(sd_checkpoint.router, tags=["SD Checkpoints"])
root_router.include_router(sd_extra_network.router, tags=["SD Extra Networks"])
root_router.include_router(character.router, tags=["Characters"])

# User routes
user_router = APIRouter(prefix="/user")
user_router.include_router(user.router, tags=["Users"])

# Tools
tools_router = APIRouter()
tools_router.include_router(safetensors_import_helper.router, tags=["Tools"])
tools_router.include_router(fix_civitai_download_filenames.router, tags=["Tools"])
tools_router.include_router(dashboard.router, tags=["Dashboard"])
tools_router.include_router(dataset_tagger.router, tags=["Dataset Tagger"])

# State
state_router = APIRouter()
state_router.include_router(state.router, tags=["State"])

# Views router
views_router = APIRouter(include_in_schema=False)
views_router.include_router(root_router)
views_router.include_router(user_router)
views_router.include_router(tools_router)
views_router.include_router(state_router)
