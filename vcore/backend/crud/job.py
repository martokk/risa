import asyncio
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from sqlalchemy import BinaryExpression
from sqlmodel import Session

from app import logger, settings
from vcore.backend import models
from vcore.backend.services.job_queue_ws_manager import job_queue_ws_manager

from .base import BaseCRUD, BaseCRUDSync


T = TypeVar("T")


def broadcast_jobs_after(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to broadcast jobs after executing a CRUD operation.

    This decorator executes the original method, then broadcasts the current
    state of all jobs to connected websocket clients.

    Args:
        func: The CRUD method to decorate (create, update, etc.)

    Returns:
        The decorated function that includes broadcasting
    """

    @wraps(func)
    async def wrapper(self: "JobCRUD", db: Session, *args: Any, **kwargs: Any) -> Any:
        # Execute the original method
        result = await func(self, db, *args, **kwargs)

        # Broadcast all jobs to the websocket
        jobs = await self.get_all_jobs_for_env_name(db, settings.ENV_NAME)

        try:
            await job_queue_ws_manager.broadcast(
                {
                    "jobs": [j.model_dump(mode="json") for j in jobs],
                }
            )
        except Exception as e:
            logger.error(f"Failed to broadcast jobs: {e}")

        return result

    return cast(Callable[..., T], wrapper)


def broadcast_jobs_after_sync(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to broadcast jobs after executing a sync CRUD operation.

    This decorator executes the original method, then spawns an async task
    to broadcast the current state of all jobs to connected websocket clients.

    Args:
        func: The sync CRUD method to decorate (create, update, etc.)

    Returns:
        The decorated function that includes broadcasting
    """

    @wraps(func)
    def wrapper(self: "JobCRUDSync", db: Session, *args: Any, **kwargs: Any) -> Any:
        # Execute the original method
        result = func(self, db, *args, **kwargs)

        # Spawn async task to broadcast (fire-and-forget)
        async def broadcast_jobs() -> None:
            try:
                jobs = self.get_all_jobs_for_env_name(db, settings.ENV_NAME, include_archived=False)
                await job_queue_ws_manager.broadcast(
                    {
                        "jobs": [j.model_dump(mode="json") for j in jobs],
                    }
                )
            except Exception as e:
                # Log error but don't fail the sync operation
                logger.error(f"Failed to broadcast jobs: {e}")

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(broadcast_jobs())
        except RuntimeError:
            # No running loop, so we run it in a new one.
            # This is blocking, but ensures the broadcast happens.
            logger.warning("No running asyncio event loop, running broadcast in a new loop.")
            asyncio.run(broadcast_jobs())

        return result

    return cast(Callable[..., T], wrapper)


class JobCRUDSync(BaseCRUDSync[models.Job, models.JobCreate, models.JobUpdate]):
    def get_all_jobs_for_env_name(
        self,
        db: Session,
        env_name: str,
        queue_name: str | None = None,
        include_archived: bool = False,
    ) -> list[models.Job]:
        if queue_name is None:
            if include_archived:
                return self.get_multi(db, env_name=env_name)
            return self.get_multi(db, env_name=env_name, archived=False)
        if include_archived:
            return self.get_multi(db, env_name=env_name, queue_name=queue_name)
        return self.get_multi(db, env_name=env_name, queue_name=queue_name, archived=False)

    def get_queued_jobs_for_queue(self, db: Session, queue_name: str) -> list[models.Job]:
        return self.get_multi(db, status=models.JobStatus.queued, queue_name=queue_name)

    def get_running_jobs_for_queue(self, db: Session, queue_name: str) -> list[models.Job]:
        return self.get_multi(db, status=models.JobStatus.running, queue_name=queue_name)

    @broadcast_jobs_after_sync
    def create(self, db: Session, *, obj_in: models.JobCreate, **kwargs: Any) -> models.Job:
        return super().create(db, obj_in=obj_in, **kwargs)

    @broadcast_jobs_after_sync
    def update(
        self,
        db: Session,
        *args: BinaryExpression[Any],
        obj_in: models.JobUpdate,
        db_obj: models.Job | None = None,
        exclude_none: bool = False,
        exclude_unset: bool = True,
        **kwargs: Any,
    ) -> models.Job:
        return super().update(
            db,
            *args,
            obj_in=obj_in,
            db_obj=db_obj,
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
            **kwargs,
        )

    @broadcast_jobs_after_sync
    def remove(self, db: Session, *args: BinaryExpression[Any], **kwargs: Any) -> None:
        return super().remove(db, *args, **kwargs)


class JobCRUD(BaseCRUD[models.Job, models.JobCreate, models.JobUpdate]):
    def __init__(self, model: type[models.Job]) -> None:
        super().__init__(model=model)
        self._sync: JobCRUDSync | None = None

    @property
    def sync(self) -> JobCRUDSync:
        """Access synchronous operations."""
        if self._sync is None:
            self._sync = JobCRUDSync(model=self.model)
        return self._sync

    async def get_all_jobs_for_env_name(
        self,
        db: Session,
        env_name: str,
        queue_name: str | None = None,
        include_archived: bool = False,
    ) -> list[models.Job]:
        if queue_name is None:
            if include_archived:
                return await self.get_multi(db, env_name=env_name)
            return await self.get_multi(db, env_name=env_name, archived=False)
        if include_archived:
            return await self.get_multi(db, env_name=env_name, queue_name=queue_name)
        return await self.get_multi(db, env_name=env_name, queue_name=queue_name, archived=False)

    async def get_queued_jobs_for_queue(self, db: Session, queue_name: str) -> list[models.Job]:
        return await self.get_multi(db, status=models.JobStatus.queued, queue_name=queue_name)

    async def get_running_jobs_for_queue(self, db: Session, queue_name: str) -> list[models.Job]:
        return await self.get_multi(db, status=models.JobStatus.running, queue_name=queue_name)

    @broadcast_jobs_after
    async def create(self, db: Session, *, obj_in: models.JobCreate, **kwargs: Any) -> models.Job:
        return await super().create(db, obj_in=obj_in, **kwargs)

    @broadcast_jobs_after
    async def update(
        self,
        db: Session,
        *args: BinaryExpression[Any],
        obj_in: models.JobUpdate,
        db_obj: models.Job | None = None,
        exclude_none: bool = False,
        exclude_unset: bool = True,
        **kwargs: Any,
    ) -> models.Job:
        return await super().update(
            db,
            *args,
            obj_in=obj_in,
            db_obj=db_obj,
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
            **kwargs,
        )

    @broadcast_jobs_after
    async def remove(self, db: Session, *args: BinaryExpression[Any], **kwargs: Any) -> None:
        return await super().remove(db, *args, **kwargs)


job = JobCRUD(model=models.Job)
