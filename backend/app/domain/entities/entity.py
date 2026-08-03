"""
Entity — one measurable/controllable point on a Device.

The generalized abstraction (HA-inspired) that lets us support any sensor
or actuator type without a schema migration per device class. A PAR sensor
and a pH sensor are both Entity rows, differing only in device_class/unit.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from app.domain.entities.enums import DeviceClass, EntityType


@dataclass
class Entity:
    device_id: UUID
    entity_type: EntityType
    device_class: DeviceClass
    unique_id: str  # stable identifier, derived from MQTT topic
    id: UUID = field(default_factory=uuid4)
    unit: str | None = None
    last_state: Any | None = None
    last_state_changed_at: datetime | None = None
    attributes: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
