"""Device request/response schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.entities.enums import DeviceStatus, DeviceType


class DeviceCreate(BaseModel):
    greenhouse_id: UUID
    name: str = Field(min_length=1, max_length=120)
    device_type: DeviceType
    mqtt_client_id: str = Field(min_length=1, max_length=120)
    status: DeviceStatus = DeviceStatus.UNKNOWN
    firmware_version: str | None = Field(default=None, max_length=32)


class DeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    greenhouse_id: UUID
    name: str
    device_type: DeviceType
    mqtt_client_id: str
    status: DeviceStatus
    firmware_version: str | None
    last_seen_at: datetime | None
    created_at: datetime
