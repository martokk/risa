from fastapi import APIRouter

from app.views.pages import context_templates, contexts
from app.views.pages.login import login
from app.views.pages.root import (
    calendar,
    grant_cycle,
    grant_program,
    grant_proposal,
    organization,
    root,
    spreadsheet,
)
from app.views.pages.tools import calculators
from app.views.pages.user import user


# Root routes
root_router = APIRouter()
root_router.include_router(root.router, tags=["Root"])
root_router.include_router(login.router, tags=["Logins"])
root_router.include_router(organization.router, tags=["Organizations"])
root_router.include_router(grant_program.router, tags=["Grant Programs"])
root_router.include_router(grant_cycle.router, tags=["Grant Cycles"])
root_router.include_router(grant_proposal.router)
root_router.include_router(calendar.router, tags=["calendar"])
root_router.include_router(spreadsheet.router, tags=["spreadsheet"])
root_router.include_router(contexts.router, tags=["Contexts"])
root_router.include_router(context_templates.router, tags=["Context Templates"])

# Tools
root_router.include_router(calculators.router, tags=["Calculators"])

# User routes
user_router = APIRouter(prefix="/user")
user_router.include_router(user.router, tags=["Users"])


# Views router
views_router = APIRouter(include_in_schema=False)
views_router.include_router(root_router)
views_router.include_router(user_router)
