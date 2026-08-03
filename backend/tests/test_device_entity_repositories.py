"""
Integration test: proves the Site -> Greenhouse -> Device -> Entity ->
StateChange chain round-trips correctly through the real repositories.

Run against the actual dev Postgres (docker compose) — this is not mocked,
because the whole point of this module is verifying the schema + mappers
work together, not just that Python compiles.

    docker compose exec backend pytest tests/test_device_entity_repositories.py -v
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.device import Device
from app.domain.entities.entity import Entity
from app.domain.entities.enums import DeviceClass, DeviceStatus, DeviceType, EntityType
from app.domain.entities.greenhouse import Greenhouse
from app.domain.entities.site import Site
from app.domain.entities.state_change import StateChange
from app.infrastructure.database.repositories.device_repository import (
    SqlAlchemyDeviceRepository,
    SqlAlchemyGreenhouseRepository,
    SqlAlchemySiteRepository,
)
from app.infrastructure.database.repositories.entity_repository import SqlAlchemyEntityRepository
from app.infrastructure.database.session import async_session_factory


@pytest.mark.asyncio
async def test_full_hierarchy_round_trip():
    async with async_session_factory() as session:  # type: AsyncSession
        site_repo = SqlAlchemySiteRepository(session)
        gh_repo = SqlAlchemyGreenhouseRepository(session)
        device_repo = SqlAlchemyDeviceRepository(session)
        entity_repo = SqlAlchemyEntityRepository(session)

        site = await site_repo.create(Site(name="Test Farm"))
        assert site.id is not None

        greenhouse = await gh_repo.create(Greenhouse(site_id=site.id, name="Greenhouse A"))
        assert greenhouse.site_id == site.id

        device = await device_repo.create(
            Device(
                greenhouse_id=greenhouse.id, name="Env Monitor 1",
                device_type=DeviceType.ENV_MONITOR, mqtt_client_id="env-monitor-01",
                status=DeviceStatus.ONLINE,
            )
        )
        assert device.greenhouse_id == greenhouse.id

        entity = await entity_repo.create(
            Entity(
                device_id=device.id, entity_type=EntityType.SENSOR,
                device_class=DeviceClass.TEMPERATURE,
                unique_id="env-monitor-01/temperature", unit="°C",
            )
        )
        assert entity.device_id == device.id
        assert entity.last_state is None

        await entity_repo.record_state_change(StateChange(entity_id=entity.id, value=24.6))

        refreshed = await entity_repo.get(entity.id)
        assert refreshed.last_state == 24.6
        assert refreshed.last_state_changed_at is not None
