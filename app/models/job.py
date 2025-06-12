"""
Pydantic models for the Job Queue feature.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class JobType(str, Enum):
    """Enum for the different types of jobs that can be executed."""

    command = "command"  # Shell script or bash .sh
    api_post = "api_post"  # POST to a given endpoint


class Priority(str, Enum):
    """Enum for job priority levels."""

    high = "high"
    medium = "medium"
    low = "low"


class JobStatus(str, Enum):
    """Enum for the status of a job."""

    queued = "queued"
    running = "running"
    failed = "failed"
    done = "done"
    cancelled = "cancelled"


class Job(BaseModel):
    """The core Job model for data transfer and validation."""

    id: UUID = Field(default_factory=uuid4)
    type: JobType
    command: str
    meta: dict | None = None
    priority: Priority = Priority.medium
    status: JobStatus = JobStatus.queued
    retry_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    recurrence: str | None = None  # e.g., "hourly", "daily"
