"""
Concrete Entity/StateChange repository.

record_state_change() is the one method every other future module (MQTT
Manager, Automation Engine) will call constantly — it inserts the history
row AND updates the entity's cached current state, atomically.
"""
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.entity import Entity
from app.domain.entities.state_change import StateChange
from app.domain.interfaces.repositories import IEntityRepository
from app.infrastructure.database.mappers import entity_to_domain
from app.infrastructure.database.models import EntityModel, StateChangeModel


class SqlAlchemyEntityRepository(IEntityRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, entity: Entity) -> Entity:
        row = EntityModel(
            id=entity.id, device_id=entity.device_id, entity_type=entity.entity_type.value,
            device_class=entity.device_class.value, unique_id=entity.unique_id,
            unit=entity.unit, attributes=entity.attributes,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return entity_to_domain(row)

    async def get(self, entity_id: UUID) -> Entity | None:
        row = await self._session.get(EntityModel, entity_id)
        return entity_to_domain(row) if row else None

    async def get_by_unique_id(self, unique_id: str) -> Entity | None:
        result = await self._session.execute(
            select(EntityModel).where(EntityModel.unique_id == unique_id)
        )
        row = result.scalar_one_or_none()
        return entity_to_domain(row) if row else None

    async def list_by_device(self, device_id: UUID) -> list[Entity]:
        result = await self._session.execute(
            select(EntityModel).where(EntityModel.device_id == device_id)
        )
        return [entity_to_domain(r) for r in result.scalars().all()]

    async def record_state_change(self, change: StateChange) -> None:
        history_row = StateChangeModel(
            id=change.id, entity_id=change.entity_id,
            value={"value": change.value}, recorded_at=change.recorded_at,
        )
        self._session.add(history_row)

        entity_row = await self._session.get(EntityModel, change.entity_id)
        if entity_row is not None:
            entity_row.last_state = {"value": change.value}
            entity_row.last_state_changed_at = change.recorded_at

        await self._session.commit()
