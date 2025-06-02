from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app import crud, logger, models
from app.api.deps import get_current_active_user
from app.core.db import get_db


router = APIRouter(prefix="/sd-checkpoints", tags=["SD Checkpoints"])


@router.get("/", response_model=list[models.SDCheckpointRead])
async def get_sd_checkpoints(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
) -> list[models.SDCheckpoint]:
    """
    Retrieve SD Checkpoints.
    """
    logger.info(f"User {current_user.id} retrieving SD Checkpoints.")
    sd_checkpoints = await crud.sd_checkpoint.get_all(db)
    return sd_checkpoints


@router.post("/", response_model=models.SDCheckpointRead, status_code=status.HTTP_201_CREATED)
async def create_sd_checkpoint(
    *,
    db: Annotated[Session, Depends(get_db)],
    sd_checkpoint_in: models.SDCheckpointCreate,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
) -> models.SDCheckpoint:
    """
    Create new SD Checkpoint.
    """
    logger.info(f"User {current_user.id} creating SD Checkpoint: {sd_checkpoint_in.id}")
    try:
        sd_checkpoint = await crud.sd_checkpoint.create(db=db, obj_in=sd_checkpoint_in)
    except Exception as e:
        logger.error(f"Error creating SD Checkpoint {sd_checkpoint_in.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating SD Checkpoint: {e}",
        )
    return sd_checkpoint


@router.get("/{sd_checkpoint_id}", response_model=models.SDCheckpointRead)
async def get_sd_checkpoint(
    *,
    db: Annotated[Session, Depends(get_db)],
    sd_checkpoint_id: str,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
) -> models.SDCheckpoint:
    """
    Get SD Checkpoint by ID.
    """
    logger.info(f"User {current_user.id} retrieving SD Checkpoint: {sd_checkpoint_id}")
    sd_checkpoint = await crud.sd_checkpoint.get(db=db, id=sd_checkpoint_id)
    if not sd_checkpoint:
        logger.warning(f"SD Checkpoint {sd_checkpoint_id} not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SD Checkpoint not found",
        )
    return sd_checkpoint


@router.put("/{sd_checkpoint_id}", response_model=models.SDCheckpointRead)
async def update_sd_checkpoint(
    *,
    db: Annotated[Session, Depends(get_db)],
    sd_checkpoint_id: str,
    sd_checkpoint_in: models.SDCheckpointUpdate,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
) -> models.SDCheckpoint:
    """
    Update an SD Checkpoint.
    """
    logger.info(f"User {current_user.id} updating SD Checkpoint: {sd_checkpoint_id}")
    sd_checkpoint = await crud.sd_checkpoint.get(db=db, id=sd_checkpoint_id)
    if not sd_checkpoint:
        logger.warning(
            f"SD Checkpoint {sd_checkpoint_id} not found for update by user {current_user.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SD Checkpoint not found",
        )
    try:
        sd_checkpoint = await crud.sd_checkpoint.update(
            db=db, db_obj=sd_checkpoint, obj_in=sd_checkpoint_in
        )
    except Exception as e:
        logger.error(f"Error updating SD Checkpoint {sd_checkpoint_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating SD Checkpoint: {e}",
        )
    return sd_checkpoint


@router.delete("/{sd_checkpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sd_checkpoint(
    *,
    db: Annotated[Session, Depends(get_db)],
    sd_checkpoint_id: str,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
) -> None:
    """
    Delete an SD Checkpoint.
    """
    logger.info(f"User {current_user.id} deleting SD Checkpoint: {sd_checkpoint_id}")
    sd_checkpoint = await crud.sd_checkpoint.get(db=db, id=sd_checkpoint_id)
    if not sd_checkpoint:
        logger.warning(
            f"SD Checkpoint {sd_checkpoint_id} not found for deletion by user {current_user.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SD Checkpoint not found",
        )
    try:
        await crud.sd_checkpoint.remove(db=db, id=sd_checkpoint_id)
    except Exception as e:
        logger.error(f"Error deleting SD Checkpoint {sd_checkpoint_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error deleting SD Checkpoint: {e}",
        )
    return
