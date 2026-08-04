"""
Conversion between SQLAlchemy ORM models and framework-free domain dataclasses.

This is the boundary: everything left of here (repositories, ORM models)
knows about SQLAlchemy. Everything right of here (domain, business logic)
does not.
"""
from app.domain.entities.device import Device
from app.domain.entities.entity import Entity
from app.domain.entities.enums import DeviceClass, DeviceStatus, DeviceType, EntityType
from app.domain.entities.greenhouse import Greenhouse
from app.domain.entities.site import Site
from app.infrastructure.database.models import DeviceModel, EntityModel, GreenhouseModel, SiteModel


def site_to_domain(row: SiteModel) -> Site:
    return Site(id=row.id, name=row.name, timezone=row.timezone, created_at=row.created_at)


def greenhouse_to_domain(row: GreenhouseModel) -> Greenhouse:
    return Greenhouse(
        id=row.id, site_id=row.site_id, name=row.name,
        description=row.description, created_at=row.created_at,
    )


def device_to_domain(row: DeviceModel) -> Device:
    return Device(
        id=row.id, greenhouse_id=row.greenhouse_id, name=row.name,
        device_type=DeviceType(row.device_type), mqtt_client_id=row.mqtt_client_id,
        status=DeviceStatus(row.status), firmware_version=row.firmware_version,
        last_seen_at=row.last_seen_at, created_at=row.created_at,
    )


def entity_to_domain(row: EntityModel) -> Entity:
    last_state = row.last_state.get("value") if row.last_state else None
    return Entity(
        id=row.id, device_id=row.device_id, entity_type=EntityType(row.entity_type),
        device_class=DeviceClass(row.device_class), unique_id=row.unique_id,
        unit=row.unit, last_state=last_state, last_state_changed_at=row.last_state_changed_at,
        attributes=row.attributes or {}, created_at=row.created_at,
    )
