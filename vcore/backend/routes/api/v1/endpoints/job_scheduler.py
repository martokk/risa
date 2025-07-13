from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from vcore.backend import crud, models
from vcore.backend.core.db import get_db
from vcore.backend.routes.api import deps


router = APIRouter(prefix="/job-schedulers", tags=["Job Schedulers"])


@router.get("/", response_model=list[models.JobSchedulerRead])
async def get_job_schedulers(
    db: Session = Depends(get_db),
    _: models.User = Depends(deps.get_current_active_user),
) -> list[models.JobScheduler]:
    return await crud.job_scheduler.get_all(db=db)


@router.post("/", response_model=models.JobSchedulerRead, status_code=status.HTTP_201_CREATED)
async def create_job_scheduler(
    *,
    db: Session = Depends(get_db),
    scheduler_in: models.JobSchedulerCreate,
    _: models.User = Depends(deps.get_current_active_user),
) -> models.JobScheduler:
    return await crud.job_scheduler.create(db=db, obj_in=scheduler_in)


@router.put("/{scheduler_id}", response_model=models.JobSchedulerRead)
async def update_job_scheduler(
    *,
    db: Session = Depends(get_db),
    scheduler_id: UUID,
    scheduler_in: models.JobSchedulerUpdate,
    _: models.User = Depends(deps.get_current_active_user),
) -> models.JobScheduler:
    scheduler = await crud.job_scheduler.get(db=db, id=scheduler_id)
    if not scheduler:
        raise HTTPException(status_code=404, detail="Job scheduler not found")
    return await crud.job_scheduler.update(db=db, db_obj=scheduler, obj_in=scheduler_in)


@router.delete("/{scheduler_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_scheduler(
    *,
    db: Session = Depends(get_db),
    scheduler_id: UUID,
    _: models.User = Depends(deps.get_current_active_user),
) -> None:
    scheduler = await crud.job_scheduler.get(db=db, id=scheduler_id)
    if not scheduler:
        raise HTTPException(status_code=404, detail="Job scheduler not found")
    await crud.job_scheduler.remove(db=db, id=scheduler_id)


@router.post("/{scheduler_id}/toggle", response_model=models.JobSchedulerRead)
async def toggle_job_scheduler(
    *,
    db: Session = Depends(get_db),
    scheduler_id: UUID,
    _: models.User = Depends(deps.get_current_active_user),
) -> models.JobScheduler:
    scheduler = await crud.job_scheduler.get(db=db, id=scheduler_id)
    if not scheduler:
        raise HTTPException(status_code=404, detail="Job scheduler not found")
    scheduler_in = models.JobSchedulerUpdate(enabled=not scheduler.enabled)
    return await crud.job_scheduler.update(db=db, db_obj=scheduler, obj_in=scheduler_in)


@router.get("/{scheduler_id}", response_model=models.JobSchedulerRead)
async def get_job_scheduler(
    *,
    db: Session = Depends(get_db),
    scheduler_id: UUID,
    _: models.User = Depends(deps.get_current_active_user),
) -> models.JobScheduler:
    scheduler = await crud.job_scheduler.get(db=db, id=scheduler_id)
    if not scheduler:
        raise HTTPException(status_code=404, detail="Job scheduler not found")
    return scheduler
