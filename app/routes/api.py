from fastapi import APIRouter

from app.api.v1.endpoints import (
    context_sections,
    context_sections_texts,
    context_templates,
    contexts,
    grant_cycles,
    grant_programs,
    grant_proposal,
    organizations,
    tasks,
    users,
)


api_router = APIRouter()

api_router.include_router(users.router, tags=["Users"])
api_router.include_router(organizations.router, tags=["Organizations"])
api_router.include_router(contexts.router, tags=["Contexts"])
api_router.include_router(context_sections.router, tags=["Context Sections"])
api_router.include_router(context_sections_texts.router, tags=["Context Sections Texts"])
api_router.include_router(context_templates.router, tags=["Context Templates"])
api_router.include_router(grant_programs.router, tags=["Grant Programs"])
api_router.include_router(grant_cycles.router, tags=["Grant Cycles"])
api_router.include_router(grant_proposal.router, tags=["Grant Proposals"])
api_router.include_router(tasks.router, tags=["Tasks"])
