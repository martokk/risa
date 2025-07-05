"""
Pydantic models for the Job Queue feature.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON
from sqlmodel import Field, SQLModel


class JobType(str, Enum):
    """Enum for the different types of jobs that can be executed."""

    command = "command"  # Shell script or bash .sh
    api_post = "api_post"  # POST to a given endpoint
    script = "script"  # Run a script


class Priority(str, Enum):
    """Enum for job priority levels."""

    highest = "highest"
    high = "high"
    normal = "normal"
    low = "low"
    lowest = "lowest"


class JobStatus(str, Enum):
    """Enum for the status of a job."""

    pending = "pending"
    queued = "queued"
    running = "running"
    failed = "failed"
    done = "done"
    cancelled = "cancelled"
    error = "error"


class JobBase(SQLModel):
    """The core Job model for data transfer and validation."""

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    env_name: str = Field(default="dev")
    name: str = Field(default="")
    type: JobType = Field(default=JobType.command)
    command: str = Field(
        default="",
        description="The command (or script Class Name) to run for the job.",
    )
    meta: dict[str, Any] = Field(default_factory=dict, sa_type=JSON)
    pid: int | None = Field(default=None)
    priority: Priority = Field(default=Priority.normal)
    status: JobStatus = Field(default=JobStatus.pending)
    retry_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    recurrence: str | None = Field(default=None)
    archived: bool = Field(default=False)
    queue_name: str = Field(
        default="default", description="Queue this job belongs to (default or reserved)"
    )

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Override model_dump to convert UUID to string."""
        data = super().model_dump(**kwargs)
        if "id" in data and isinstance(data["id"], UUID):
            data["id"] = str(data["id"])
        if "created_at" in data and isinstance(data["created_at"], datetime):
            data["created_at"] = data["created_at"].isoformat()
        return data


class Job(JobBase, table=True):
    """The Job model for the database."""

    pass


class JobUpdate(SQLModel):
    """Pydantic model for updating a job."""

    env_name: str | None = None
    name: str | None = None
    command: str | None = None
    meta: dict[str, Any] | None = None
    pid: int | None = None
    priority: Priority | None = None
    status: JobStatus | None = None
    retry_count: int | None = None
    recurrence: str | None = None
    archived: bool | None = None
    queue_name: str | None = None


class JobCreate(JobBase):
    """Pydantic model for creating a job."""

    pass


class JobRead(JobBase):
    """Pydantic model for reading a job."""

    pass
