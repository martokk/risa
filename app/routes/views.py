from fastapi import APIRouter

from app.views.pages import context_templates, contexts
from app.views.pages.character import character
from app.views.pages.login import login
from app.views.pages.root import root
from app.views.pages.sd_base_model import sd_base_model
from app.views.pages.sd_checkpoint import sd_checkpoint
from app.views.pages.sd_extra_network import sd_extra_network
from app.views.pages.user import user


# Root routes
root_router = APIRouter()
root_router.include_router(root.router, tags=["Root"])
root_router.include_router(login.router, tags=["Logins"])

root_router.include_router(contexts.router, tags=["Contexts"])
root_router.include_router(context_templates.router, tags=["Context Templates"])

# SD specific routes
root_router.include_router(sd_base_model.router, tags=["SD Base Models"])
root_router.include_router(sd_checkpoint.router, tags=["SD Checkpoints"])
root_router.include_router(sd_extra_network.router, tags=["SD Extra Networks"])
root_router.include_router(character.router, tags=["Characters"])

# User routes
user_router = APIRouter(prefix="/user")
user_router.include_router(user.router, tags=["Users"])


# Views router
views_router = APIRouter(include_in_schema=False)
views_router.include_router(root_router)
views_router.include_router(user_router)
