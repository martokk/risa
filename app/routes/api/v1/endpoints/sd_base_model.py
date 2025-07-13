from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app import crud, logger, models
from vcore.backend.core.db import get_db
from vcore.backend.templating.deps import get_current_active_user


router = APIRouter(prefix="/sd-base-models", tags=["SD Base Models"])


@router.get("/", response_model=list[models.SDBaseModel])
async def get_sd_base_models(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
) -> list[models.SDBaseModel]:
    """
    Retrieve SD Base Models.
    """
    logger.info(f"User {current_user.id} retrieving SD Base Models.")
    sd_base_models = await crud.sd_base_model.get_all(db=db, skip=skip, limit=limit)
    return sd_base_models


@router.post("/", response_model=models.SDBaseModelRead, status_code=status.HTTP_201_CREATED)
async def create_sd_base_model(
    *,
    db: Annotated[Session, Depends(get_db)],
    sd_base_model_in: models.SDBaseModelCreate,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
) -> models.SDBaseModel:
    """
    Create new SD Base Model.
    """
    logger.info(f"User {current_user.id} creating SD Base Model: {sd_base_model_in.id}")
    try:
        sd_base_model = await crud.sd_base_model.create(db=db, obj_in=sd_base_model_in)
    except Exception as e:
        logger.error(f"Error creating SD Base Model {sd_base_model_in.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating SD Base Model: {e}",
        )
    return sd_base_model


@router.get("/{sd_base_model_id}", response_model=models.SDBaseModelRead)
async def get_sd_base_model(
    *,
    db: Annotated[Session, Depends(get_db)],
    sd_base_model_id: str,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
) -> models.SDBaseModel:
    """
    Get SD Base Model by ID.
    """
    logger.info(f"User {current_user.id} retrieving SD Base Model: {sd_base_model_id}")
    sd_base_model = await crud.sd_base_model.get(db=db, id=sd_base_model_id)
    if not sd_base_model:
        logger.warning(f"SD Base Model {sd_base_model_id} not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SD Base Model not found",
        )
    return sd_base_model


@router.put("/{sd_base_model_id}", response_model=models.SDBaseModelRead)
async def update_sd_base_model(
    *,
    db: Annotated[Session, Depends(get_db)],
    sd_base_model_id: str,
    sd_base_model_in: models.SDBaseModelUpdate,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
) -> models.SDBaseModel:
    """
    Update an SD Base Model.
    """
    logger.info(f"User {current_user.id} updating SD Base Model: {sd_base_model_id}")
    sd_base_model = await crud.sd_base_model.get(db=db, id=sd_base_model_id)
    if not sd_base_model:
        logger.warning(
            f"SD Base Model {sd_base_model_id} not found for update by user {current_user.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SD Base Model not found",
        )
    try:
        sd_base_model = await crud.sd_base_model.update(
            db=db, db_obj=sd_base_model, obj_in=sd_base_model_in
        )
    except Exception as e:
        logger.error(f"Error updating SD Base Model {sd_base_model_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating SD Base Model: {e}",
        )
    return sd_base_model


@router.delete("/{sd_base_model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sd_base_model(
    *,
    db: Annotated[Session, Depends(get_db)],
    sd_base_model_id: str,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
) -> None:
    """
    Delete an SD Base Model.
    """
    logger.info(f"User {current_user.id} deleting SD Base Model: {sd_base_model_id}")
    sd_base_model = await crud.sd_base_model.get(db=db, id=sd_base_model_id)
    if not sd_base_model:
        logger.warning(
            f"SD Base Model {sd_base_model_id} not found for deletion by user {current_user.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SD Base Model not found",
        )
    try:
        await crud.sd_base_model.remove(db=db, id=sd_base_model_id)
    except Exception as e:
        logger.error(f"Error deleting SD Base Model {sd_base_model_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error deleting SD Base Model: {e}",
        )
    return


# TODO: Add endpoints for add_checkpoint and add_extra_network
# These will require specific input models and careful handling of parameters.
