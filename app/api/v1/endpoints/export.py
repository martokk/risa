from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from sqlmodel import Session

from app import crud, logger, models, settings
from app.core.db import get_db


# Create a router that bypasses global auth
router = APIRouter(prefix="", include_in_schema=True)

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)


async def get_api_key(api_key_header: Annotated[str | None, Security(api_key_header)]) -> str:
    """Validate API key from header.

    Args:
        api_key_header: API key from request header

    Returns:
        Validated API key

    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not settings.EXPORT_API_KEY:
        logger.error("EXPORT_API_KEY is not set in environment variables")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Export API key not configured",
        )

    logger.debug(f"Received API key: {api_key_header}")
    if api_key_header == settings.EXPORT_API_KEY:
        return api_key_header

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key",
    )


@router.get("", include_in_schema=True)
async def export_data(
    db: Annotated[Session, Depends(get_db)],
    api_key: Annotated[str, Security(get_api_key)],
) -> dict[str, list[dict[str, Any]]]:
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
    }
