"""Device — a physical ESP32 node (or the Pi itself) within a Greenhouse."""
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.entities.enums import DeviceStatus, DeviceType


@dataclass
class Device:
    greenhouse_id: UUID
    name: str
    device_type: DeviceType
    mqtt_client_id: str
    id: UUID = field(default_factory=uuid4)
    status: DeviceStatus = DeviceStatus.UNKNOWN
    firmware_version: str | None = None
    last_seen_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
