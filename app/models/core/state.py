from datetime import datetime

from sqlmodel import Field, SQLModel


class InstanceStateBase(SQLModel):
    id: str = Field(default=None, primary_key=True, unique=True, alias="env_name")
    last_updated: datetime | None = None
    project_name: str
    base_domain: str


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
