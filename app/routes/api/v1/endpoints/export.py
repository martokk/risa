from typing import Annotated, Any

from fastapi import APIRouter, Depends, Security
from sqlmodel import Session

from app import crud, models
from vcore.backend.core.api_key import get_api_key
from vcore.backend.core.db import get_db


# Create a router that bypasses global auth
router = APIRouter(prefix="", include_in_schema=True)


@router.get("/export", include_in_schema=True)
async def export_data(
    db: Annotated[Session, Depends(get_db)],
    api_key: Annotated[str, Security(get_api_key)],
) -> dict[str, Any]:
    """Export all data from the database.

    Args:
        db: Database session
        api_key: Validated API key

    Returns:
        Dictionary containing all exported data
    """
    # Get all data from each model
    sd_base_models = await crud.sd_base_model.get_all(db=db)
    sd_checkpoints = await crud.sd_checkpoint.get_all(db=db)
    sd_extra_networks = await crud.sd_extra_network.get_all(db=db)
    characters = await crud.character.get_all(db=db)

    character_ids_for_sd_base_models = {}
    for sd_base_model in sd_base_models:
        character_ids_for_sd_base_models[
            sd_base_model.id
        ] = await crud.sd_base_model.get_character_ids_for_base_model(db=db, id=sd_base_model.id)

    # Convert to dictionary format
    return {
        "sd_base_models": [
            models.SDBaseModelRead.model_validate(model).model_dump() for model in sd_base_models
        ],
        "sd_checkpoints": [
            models.SDCheckpointRead.model_validate(model).model_dump() for model in sd_checkpoints
        ],
        "sd_extra_networks": [
            models.SDExtraNetworkRead.model_validate(model).model_dump()
            for model in sd_extra_networks
        ],
        "characters": [
            models.CharacterRead.model_validate(model).model_dump() for model in characters
        ],
        "character_ids_for_sd_base_models": [character_ids_for_sd_base_models],
    }
