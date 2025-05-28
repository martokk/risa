from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app import crud, logger, models
from app.api.deps import get_current_active_user
from app.core.db import get_db


router = APIRouter(prefix="/sd-extra-networks", tags=["SD Extra Networks"])


@router.get("/", response_model=list[models.SDExtraNetworkRead])
async def get_sd_extra_networks(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
) -> list[models.SDExtraNetwork]:
    """
    Retrieve SD Extra Networks.
    """
    logger.info(f"User {current_user.id} retrieving SD Extra Networks.")
    sd_extra_networks = await crud.sd_extra_network.get_all(db)
    return sd_extra_networks


@router.post("/", response_model=models.SDExtraNetworkRead, status_code=status.HTTP_201_CREATED)
async def create_sd_extra_network(
    *,
    db: Annotated[Session, Depends(get_db)],
    sd_extra_network_in: models.SDExtraNetworkCreate,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
) -> models.SDExtraNetwork:
    """
    Create new SD Extra Network.
    """
    logger.info(f"User {current_user.id} creating SD Extra Network: {sd_extra_network_in.id}")
    try:
        sd_extra_network = await crud.sd_extra_network.create(db=db, obj_in=sd_extra_network_in)
    except ValueError as ve:
        logger.error(f"Validation error creating SD Extra Network by user {current_user.id}: {ve}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,  # Pydantic validation error
            detail=str(ve),
        )
    except Exception as e:
        logger.error(
            f"Error creating SD Extra Network {sd_extra_network_in.id if sd_extra_network_in else 'unknown'}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating SD Extra Network: {e}",
        )
    return sd_extra_network


@router.get("/{sd_extra_network_id}", response_model=models.SDExtraNetworkRead)
async def get_sd_extra_network(
    *,
    db: Annotated[Session, Depends(get_db)],
    sd_extra_network_id: str,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
) -> models.SDExtraNetwork:
    """
    Get SD Extra Network by ID.
    """
    logger.info(f"User {current_user.id} retrieving SD Extra Network: {sd_extra_network_id}")
    sd_extra_network = await crud.sd_extra_network.get(db=db, id=sd_extra_network_id)
    if not sd_extra_network:
        logger.warning(
            f"SD Extra Network {sd_extra_network_id} not found for user {current_user.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SD Extra Network not found",
        )
    return sd_extra_network


@router.put("/{sd_extra_network_id}", response_model=models.SDExtraNetworkRead)
async def update_sd_extra_network(
    *,
    db: Annotated[Session, Depends(get_db)],
    sd_extra_network_id: str,
    sd_extra_network_in: models.SDExtraNetworkUpdate,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
) -> models.SDExtraNetwork:
    """
    Update an SD Extra Network.
    """
    logger.info(f"User {current_user.id} updating SD Extra Network: {sd_extra_network_id}")
    sd_extra_network = await crud.sd_extra_network.get(db=db, id=sd_extra_network_id)
    if not sd_extra_network:
        logger.warning(
            f"SD Extra Network {sd_extra_network_id} not found for update by user {current_user.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SD Extra Network not found",
        )
    try:
        sd_extra_network = await crud.sd_extra_network.update(
            db=db, db_obj=sd_extra_network, obj_in=sd_extra_network_in
        )
    except ValueError as ve:
        logger.error(
            f"Validation error updating SD Extra Network {sd_extra_network_id} by user {current_user.id}: {ve}"
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except Exception as e:
        logger.error(f"Error updating SD Extra Network {sd_extra_network_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating SD Extra Network: {e}",
        )
    return sd_extra_network


@router.delete("/{sd_extra_network_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sd_extra_network(
    *,
    db: Annotated[Session, Depends(get_db)],
    sd_extra_network_id: str,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
) -> None:
    """
    Delete an SD Extra Network.
    """
    logger.info(f"User {current_user.id} deleting SD Extra Network: {sd_extra_network_id}")
    sd_extra_network = await crud.sd_extra_network.get(db=db, id=sd_extra_network_id)
    if not sd_extra_network:
        logger.warning(
            f"SD Extra Network {sd_extra_network_id} not found for deletion by user {current_user.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SD Extra Network not found",
        )
    try:
        await crud.sd_extra_network.remove(db=db, id=sd_extra_network_id)
    except Exception as e:
        logger.error(f"Error deleting SD Extra Network {sd_extra_network_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error deleting SD Extra Network: {e}",
        )
    return
