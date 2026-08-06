"""Entity request/response schemas."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.entities.enums import DeviceClass, EntityType


class EntityCreate(BaseModel):
    device_id: UUID
    entity_type: EntityType
    device_class: DeviceClass
    unique_id: str = Field(min_length=1, max_length=160)
    unit: str | None = Field(default=None, max_length=16)
    attributes: dict = Field(default_factory=dict)


class EntityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_id: UUID
    entity_type: EntityType
    device_class: DeviceClass
    unique_id: str
    unit: str | None
    # Unwrapped by the mapper from the JSONB {"value": ...} envelope, so this
    # is the bare reading (float/bool/str) or null before the first telemetry.
    last_state: Any | None
    last_state_changed_at: datetime | None
    attributes: dict
    created_at: datetime
