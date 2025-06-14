"""
Pydantic models for the Job Queue feature.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class JobType(str, Enum):
    """Enum for the different types of jobs that can be executed."""

    command = "command"  # Shell script or bash .sh
    api_post = "api_post"  # POST to a given endpoint


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


class Job(BaseModel):
    """The core Job model for data transfer and validation."""

    id: UUID = Field(default_factory=uuid4)
    name: str = ""
    type: JobType
    command: str
    meta: dict[str, Any] | None = None
    pid: int | None = None
    priority: Priority = Priority.normal
    status: JobStatus = JobStatus.pending
    retry_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    recurrence: str | None = None  # e.g., "hourly", "daily"


class JobUpdate(BaseModel):
    """Pydantic model for updating a job."""

    name: str | None = None
    command: str | None = None
    meta: dict[str, Any] | None = None
    pid: int | None = None
    priority: Priority | None = None
    status: JobStatus | None = None
    retry_count: int | None = None
    recurrence: str | None = None
