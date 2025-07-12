from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON
from sqlmodel import Field, SQLModel


class JobSchedulerTriggerType(str, Enum):
    on_start = "on_start"
    repeat = "repeat"


class JobSchedulerBase(SQLModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    env_name: str = Field(..., description="Environment name")
    name: str = Field(default="")
    description: str = Field(default="")
    trigger_type: JobSchedulerTriggerType = Field(default=JobSchedulerTriggerType.on_start)
    repeat_every_seconds: int | None = Field(default=None)
    job_template: dict[str, Any] = Field(default_factory=dict, sa_type=JSON)
    enabled: bool = Field(default=True)
    last_run: int | None = Field(default=None, description="Unix timestamp of last run")


class JobScheduler(JobSchedulerBase, table=True):
    pass


class JobSchedulerCreate(JobSchedulerBase):
    pass


class JobSchedulerUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    trigger_type: JobSchedulerTriggerType | None = None
    repeat_every_seconds: int | None = None
    job_template: dict[str, Any] | None = None
    enabled: bool | None = None
    last_run: int | None = None
    env_name: str | None = None


class JobSchedulerRead(JobSchedulerBase):
    pass
