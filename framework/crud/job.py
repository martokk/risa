from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from sqlalchemy import BinaryExpression
from sqlmodel import Session

from app import settings
from framework import models
from framework.core.websocket import websocket_manager

from .base import BaseCRUD


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
    async def wrapper(self: "JobCRUD", db: Session, *args: Any, **kwargs: Any) -> T:
        # Execute the original method
        result = await func(self, db, *args, **kwargs)

        # Broadcast all jobs to the websocket
        await websocket_manager.broadcast(
            {
                "jobs": [
                    j.model_dump(mode="json")
                    for j in await self.get_all_jobs_for_env_name(db, settings.ENV_NAME)
                ],
            }
        )

        return result

    return cast(Callable[..., T], wrapper)


class JobCRUD(BaseCRUD[models.Job, models.JobCreate, models.JobUpdate]):
    async def get_all_jobs_for_env_name(self, db: Session, env_name: str) -> list[models.Job]:
        return await self.get_multi(db, env_name=env_name, limit=1000)

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
