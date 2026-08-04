import json
import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.infrastructure.database.models import (
    SiteModel,
    GreenhouseModel,
    DeviceModel,
    EntityModel,
    StateChangeModel,
)

logger = logging.getLogger(__name__)

class TelemetryIngestionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def process_message(self, topic: str, payload: str) -> None:
        """
        Parses MQTT telemetry messages, auto-registers missing entities,
        and records state changes into PostgreSQL.
        Expected topic structure: hydrocore/{site_id}/{zone}/{device}/{metric}
        """
        logger.info(f"[TelemetryIngestionService] Processing topic: {topic} | payload: {payload}")
        
        try:
            data = json.loads(payload) if payload else {}
        except json.JSONDecodeError:
            data = {"raw_value": payload}

        topic_parts = [p for p in topic.strip("/").split("/") if p]
        
        site_name = topic_parts[1] if len(topic_parts) > 1 else "default-site"
        greenhouse_name = topic_parts[2] if len(topic_parts) > 2 else "default-gh"
        device_name = topic_parts[3] if len(topic_parts) > 3 else "default-device"

        # 1. Auto-register Site if it doesn't exist
        res = await self.session.execute(select(SiteModel).where(SiteModel.name == site_name))
        site = res.scalars().first()
        if not site:
            site = SiteModel(id=uuid.uuid4(), name=site_name)
            self.session.add(site)
            await self.session.flush()
            logger.info(f"Auto-registering new site: {site_name}")

        # 2. Auto-register Greenhouse if it doesn't exist
        res = await self.session.execute(
            select(GreenhouseModel).where(
                GreenhouseModel.name == greenhouse_name, 
                GreenhouseModel.site_id == site.id
            )
        )
        gh = res.scalars().first()
        if not gh:
            gh = GreenhouseModel(id=uuid.uuid4(), site_id=site.id, name=greenhouse_name)
            self.session.add(gh)
            await self.session.flush()
            logger.info(f"Auto-registering new greenhouse: {greenhouse_name}")

        # 3. Auto-register Device if it doesn't exist
        res = await self.session.execute(
            select(DeviceModel).where(
                DeviceModel.name == device_name, 
                DeviceModel.greenhouse_id == gh.id
            )
        )
        dev = res.scalars().first()
        if not dev:
            dev = DeviceModel(
                id=uuid.uuid4(),
                greenhouse_id=gh.id,
                name=device_name,
                device_type="sensor",
                mqtt_client_id=f"{device_name}-{uuid.uuid4().hex[:6]}"
            )
            self.session.add(dev)
            await self.session.flush()
            logger.info(f"Auto-registering new device: {device_name}")

        # 4. Iterate telemetry fields and record state changes
        for key, val in data.items():
            entity_unique_id = f"{device_name}/{key}"
            res = await self.session.execute(
                select(EntityModel).where(EntityModel.unique_id == entity_unique_id)
            )
            entity = res.scalars().first()
            
            if not entity:
                entity = EntityModel(
                    id=uuid.uuid4(), 
                    device_id=dev.id, 
                    entity_type="sensor",
                    device_class=key,
                    unique_id=entity_unique_id, 
                    last_state={"value": val}
                )
                self.session.add(entity)
                await self.session.flush()
                logger.info(f"Auto-registering new entity: {entity_unique_id}")
            else:
                entity.last_state = {"value": val}

            # Record state change entry
            state_change = StateChangeModel(
                id=uuid.uuid4(),
                entity_id=entity.id,
                value={"value": val}
            )
            self.session.add(state_change)
            logger.info(f"Recorded {key} = {val} for {device_name}")

        await self.session.commit()