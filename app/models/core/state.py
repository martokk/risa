from datetime import datetime

from sqlmodel import Field, SQLModel


class InstanceStateBase(SQLModel):
    id: str = Field(default=None, primary_key=True, unique=True, alias="env_name")
    last_updated: datetime | None = None
    project_name: str
    base_url: str

    # Theme
    accent: str | None = None

    # System Status
    gpu_usage: float | None = None
    gpu_memory_used: float | None = None
    cpu_usage: float | None = None
    total_disk_space: int | None = None
    used_disk_space: int | None = None
    free_disk_space: int | None = None
    disk_usage: float | None = None

    # Runpod
    runpod_gpu_name: str | None = None
    runpod_pod_id: str | None = None
    runpod_public_ip: str | None = None


class InstanceState(InstanceStateBase, table=True):
    pass


class InstanceStateCreate(InstanceStateBase):
    pass


class InstanceStateUpdate(InstanceStateBase):
    pass


class InstanceStateRead(InstanceStateBase):
    pass


class NetworkState(SQLModel):
    last_updated: datetime | None = None
    dev: InstanceState
    local: InstanceState
    host: InstanceState
    playground: InstanceState
