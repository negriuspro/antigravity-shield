from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from app.models.device import DeviceStatus


class DeviceOut(BaseModel):
    id: UUID
    mac: str
    ip: str
    hostname: str | None
    manufacturer: str | None
    device_type: str | None
    status: DeviceStatus
    group_name: str | None
    is_blocked: bool
    last_seen: datetime | None
    first_seen: datetime

    model_config = {"from_attributes": True}


class DeviceUpdate(BaseModel):
    hostname: str | None = None
    group_name: str | None = None
    is_blocked: bool | None = None
    device_type: str | None = None


class DeviceStats(BaseModel):
    device_id: UUID
    total_queries: int
    blocked_queries: int
    allowed_queries: int
    block_rate: float
