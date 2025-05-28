from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app import crud, logger, models
from app.api.deps import get_current_active_user
from app.core.db import get_db


router = APIRouter(prefix="/characters", tags=["Characters"])


@router.get("/", response_model=list[models.CharacterRead])
async def get_characters(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
) -> list[models.Character]:
    """
    Retrieve characters.
    """
    logger.info(f"User {current_user.id} retrieving characters.")
    characters = await crud.character.get_all(db=db, skip=skip, limit=limit)
    return characters


@router.post("/", response_model=models.CharacterRead, status_code=status.HTTP_201_CREATED)
async def create_character(
    *,
    db: Annotated[Session, Depends(get_db)],
    character_in: models.CharacterCreate,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
) -> models.Character:
    """
    Create new character.
    """
    logger.info(f"User {current_user.id} creating character: {character_in.id}")
    try:
        character = await crud.character.create(db=db, obj_in=character_in)
    except Exception as e:
        logger.error(f"Error creating character {character_in.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating character: {e}",
        )
    return character


@router.get("/{character_id}", response_model=models.CharacterRead)
async def get_character(
    *,
    db: Annotated[Session, Depends(get_db)],
    character_id: str,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
) -> models.Character:
    """
    Get character by ID.
    """
    logger.info(f"User {current_user.id} retrieving character: {character_id}")
    character = await crud.character.get(db=db, id=character_id)
    if not character:
        logger.warning(f"Character {character_id} not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )
    return character


@router.put("/{character_id}", response_model=models.CharacterRead)
async def update_character(
    *,
    db: Annotated[Session, Depends(get_db)],
    character_id: str,
    character_in: models.CharacterUpdate,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
) -> models.Character:
    """
    Update a character.
    """
    logger.info(f"User {current_user.id} updating character: {character_id}")
    character = await crud.character.get(db=db, id=character_id)
    if not character:
        logger.warning(f"Character {character_id} not found for update by user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )
    try:
        character = await crud.character.update(db=db, db_obj=character, obj_in=character_in)
    except Exception as e:
        logger.error(f"Error updating character {character_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating character: {e}",
        )
    return character


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(
    *,
    db: Annotated[Session, Depends(get_db)],
    character_id: str,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
) -> None:
    """
    Delete a character.
    """
    logger.info(f"User {current_user.id} deleting character: {character_id}")
    character = await crud.character.get(db=db, id=character_id)
    if not character:
        logger.warning(f"Character {character_id} not found for deletion by user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )
    try:
        await crud.character.remove(db=db, id=character_id)
    except Exception as e:
        logger.error(f"Error deleting character {character_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error deleting character: {e}",
        )
    return


# Placeholder for add_extra_network endpoint
# @router.post("/{character_id}/sd_extra_networks", response_model=models.CharacterRead)
# async def add_sd_extra_network_to_character(
# ...,
# ) -> models.Character:
# details to be filled in based on how SDExtraNetworkCreate and the CRUD method align.
#     pass
