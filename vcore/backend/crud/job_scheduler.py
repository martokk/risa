from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session

from app import logger
from vcore.backend.crud.base import BaseCRUD, BaseCRUDSync
from vcore.backend.models import (
    JobScheduler,
    JobSchedulerCreate,
    JobSchedulerTriggerType,
    JobSchedulerUpdate,
)


class JobSchedulerCRUDSync(BaseCRUDSync[JobScheduler, JobSchedulerCreate, JobSchedulerUpdate]):
    def get_on_start_schedulers(self, db: Session, env_name: str) -> list[JobScheduler]:
        return self.get_multi(
            db, env_name=env_name, trigger_type=JobSchedulerTriggerType.on_start, enabled=True
        )

    def get_repeat_schedulers_ready_to_run(self, db: Session, env_name: str) -> list[JobScheduler]:
        schedulers = self.get_multi(
            db, env_name=env_name, trigger_type=JobSchedulerTriggerType.repeat, enabled=True
        )
        now = int(datetime.utcnow().timestamp())
        ready = []
        for s in schedulers:
            if s.repeat_every_seconds is not None and (
                s.last_run is None or now - s.last_run >= s.repeat_every_seconds
            ):
                ready.append(s)
        return ready

    def update_last_run(self, db: Session, scheduler_id: Any) -> JobScheduler:
        scheduler = self.get(db, id=scheduler_id)
        now = int(datetime.now(timezone.utc).timestamp())
        update_in = JobSchedulerUpdate(last_run=now)
        logger.info(f"Updating last run for scheduler {scheduler_id}: {now}")
        return self.update(db, db_obj=scheduler, obj_in=update_in)


class JobSchedulerCRUD(BaseCRUD[JobScheduler, JobSchedulerCreate, JobSchedulerUpdate]):
    def __init__(self, model: type[JobScheduler]) -> None:
        super().__init__(model=model, model_crud_sync=JobSchedulerCRUDSync(model=model))

    async def get_on_start_schedulers(self, db: Session, env_name: str) -> list[JobScheduler]:
        return await self.get_multi(
            db, env_name=env_name, trigger_type=JobSchedulerTriggerType.on_start, enabled=True
        )

    async def get_repeat_schedulers_ready_to_run(
        self, db: Session, env_name: str
    ) -> list[JobScheduler]:
        schedulers = await self.get_multi(
            db, env_name=env_name, trigger_type=JobSchedulerTriggerType.repeat, enabled=True
        )
        now = int(datetime.utcnow().timestamp())
        ready = []
        for s in schedulers:
            if s.repeat_every_seconds is not None and (
                s.last_run is None or now - s.last_run >= s.repeat_every_seconds
            ):
                ready.append(s)
        return ready

    async def update_last_run(self, db: Session, scheduler_id: Any) -> JobScheduler:
        scheduler = await self.get(db, id=scheduler_id)
        now = int(datetime.now(timezone.utc).timestamp())
        update_in = JobSchedulerUpdate(last_run=now)
        return await self.update(db, db_obj=scheduler, obj_in=update_in)


job_scheduler = JobSchedulerCRUD(model=JobScheduler)
