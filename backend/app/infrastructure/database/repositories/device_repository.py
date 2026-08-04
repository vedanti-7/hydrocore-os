"""
Concrete Site/Greenhouse/Device repositories.

Implements the domain interfaces using SQLAlchemy. Business logic never
sees this file — it depends on ISiteRepository/IGreenhouseRepository/
IDeviceRepository from app.domain.interfaces.repositories.
"""
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.device import Device
from app.domain.entities.greenhouse import Greenhouse
from app.domain.entities.site import Site
from app.domain.interfaces.repositories import (
    IDeviceRepository,
    IGreenhouseRepository,
    ISiteRepository,
)
from app.infrastructure.database.mappers import device_to_domain, greenhouse_to_domain, site_to_domain
from app.infrastructure.database.models import DeviceModel, GreenhouseModel, SiteModel


class SqlAlchemySiteRepository(ISiteRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, site: Site) -> Site:
        row = SiteModel(id=site.id, name=site.name, timezone=site.timezone)
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return site_to_domain(row)

    async def get(self, site_id: UUID) -> Site | None:
        row = await self._session.get(SiteModel, site_id)
        return site_to_domain(row) if row else None

    async def list_all(self) -> list[Site]:
        result = await self._session.execute(select(SiteModel))
        return [site_to_domain(r) for r in result.scalars().all()]


class SqlAlchemyGreenhouseRepository(IGreenhouseRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, greenhouse: Greenhouse) -> Greenhouse:
        row = GreenhouseModel(
            id=greenhouse.id, site_id=greenhouse.site_id,
            name=greenhouse.name, description=greenhouse.description,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return greenhouse_to_domain(row)

    async def get(self, greenhouse_id: UUID) -> Greenhouse | None:
        row = await self._session.get(GreenhouseModel, greenhouse_id)
        return greenhouse_to_domain(row) if row else None

    async def list_by_site(self, site_id: UUID) -> list[Greenhouse]:
        result = await self._session.execute(
            select(GreenhouseModel).where(GreenhouseModel.site_id == site_id)
        )
        return [greenhouse_to_domain(r) for r in result.scalars().all()]


class SqlAlchemyDeviceRepository(IDeviceRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, device: Device) -> Device:
        row = DeviceModel(
            id=device.id, greenhouse_id=device.greenhouse_id, name=device.name,
            device_type=device.device_type.value, mqtt_client_id=device.mqtt_client_id,
            status=device.status.value, firmware_version=device.firmware_version,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return device_to_domain(row)

    async def get(self, device_id: UUID) -> Device | None:
        row = await self._session.get(DeviceModel, device_id)
        return device_to_domain(row) if row else None

    async def get_by_mqtt_client_id(self, mqtt_client_id: str) -> Device | None:
        result = await self._session.execute(
            select(DeviceModel).where(DeviceModel.mqtt_client_id == mqtt_client_id)
        )
        row = result.scalar_one_or_none()
        return device_to_domain(row) if row else None

    async def list_by_greenhouse(self, greenhouse_id: UUID) -> list[Device]:
        result = await self._session.execute(
            select(DeviceModel).where(DeviceModel.greenhouse_id == greenhouse_id)
        )
        return [device_to_domain(r) for r in result.scalars().all()]

    async def update_status(self, device_id: UUID, status: str, seen_at: datetime) -> None:
        row = await self._session.get(DeviceModel, device_id)
        if row is None:
            return
        row.status = status
        row.last_seen_at = seen_at
        await self._session.commit()
