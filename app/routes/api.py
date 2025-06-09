from fastapi import APIRouter

from app.api.v1.endpoints import (
    character,
    export,
    sd_base_model,
    sd_checkpoint,
    sd_extra_network,
    state,
    users,
)


api_router = APIRouter()

# Include the export router directly with empty dependencies to bypass auth
api_router.include_router(export.router, tags=["Export"])
api_router.include_router(state.router, tags=["State"])

# Include routers that require auth
api_router.include_router(users.router, tags=["Users"])
api_router.include_router(character.router, tags=["Characters"])
api_router.include_router(sd_base_model.router, tags=["SD Base Models"])
api_router.include_router(sd_checkpoint.router, tags=["SD Checkpoints"])
api_router.include_router(sd_extra_network.router, tags=["SD Extra Networks"])
