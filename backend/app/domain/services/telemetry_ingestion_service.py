import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.domain.entities.enums import DeviceClass, DeviceStatus, EntityType
from app.infrastructure.database.models import (
    SiteModel,
    GreenhouseModel,
    DeviceModel,
    EntityModel,
    StateChangeModel,
)
from app.infrastructure.database.repositories.device_repository import (
    SqlAlchemyDeviceRepository,
)
from app.infrastructure.mqtt.topics import parse_telemetry_topic

logger = logging.getLogger(__name__)

# Metric keys must map onto the DeviceClass vocabulary. Anything else would
# be written as free text and then blow up in entity_to_domain() on read.
_KNOWN_DEVICE_CLASSES = {member.value for member in DeviceClass}

# JSON scalars a reading may be. Nested objects/arrays are not readings.
_SCALAR_TYPES = (int, float, bool, str)


def _parse_metrics(topic: str, payload: str) -> dict[str, Any] | None:
    """
    Validate a raw telemetry payload down to a dict of usable readings.

    Returns None when nothing should be ingested. Malformed input is a
    logged no-op, never an exception and never a placeholder entity — a
    corrupt message must not be able to define new schema by accident.
    """
    if not payload or not payload.strip():
        logger.warning("Rejecting empty telemetry payload on topic '%s'", topic)
        return None

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        logger.warning("Rejecting malformed JSON on topic '%s': %s", topic, exc)
        return None

    if not isinstance(data, dict):
        logger.warning(
            "Rejecting non-object telemetry payload on topic '%s': got %s",
            topic,
            type(data).__name__,
        )
        return None

    if not data:
        logger.warning("Rejecting empty telemetry object on topic '%s'", topic)
        return None

    metrics: dict[str, Any] = {}
    for key, value in data.items():
        if key not in _KNOWN_DEVICE_CLASSES:
            logger.warning("Skipping unknown metric '%s' on topic '%s'", key, topic)
            continue
        if not isinstance(value, _SCALAR_TYPES):
            logger.warning(
                "Skipping non-scalar value for metric '%s' on topic '%s'", key, topic
            )
            continue
        metrics[key] = value

    if not metrics:
        logger.warning("No usable metrics in telemetry payload on topic '%s'", topic)
        return None

    return metrics


class TelemetryIngestionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def process_message(self, topic: str, payload: str) -> bool:
        """
        Ingests telemetry from an already-provisioned device.

        Expected topic: hydrocore/{site}/{greenhouse}/{mqtt_client_id}/telemetry

        The device MUST exist: it is resolved by mqtt_client_id, which is
        UNIQUE, and an unknown identity is dropped. Sites, greenhouses and
        devices are never created here — provisioning is an operator action
        through the REST API. Entities are still discovered automatically,
        because a provisioned device's sensor set is a firmware detail.

        Returns True when readings were staged. Does NOT commit — the
        consumer owns the transaction boundary, so one message is one
        atomic unit that either lands whole or not at all.
        """
        logger.info(f"[TelemetryIngestionService] Processing topic: {topic} | payload: {payload}")

        parsed_topic = parse_telemetry_topic(topic)
        if parsed_topic is None:
            logger.warning("Ignoring message on non-telemetry or malformed topic: '%s'", topic)
            return False

        metrics = _parse_metrics(topic, payload)
        if metrics is None:
            return False

        mqtt_client_id = parsed_topic.mqtt_client_id
        observed_at = datetime.now(timezone.utc)

        # 1. Resolve the physical device by its authoritative identity. No
        #    name matching: names are neither unique nor stable.
        device_repo = SqlAlchemyDeviceRepository(self.session)
        device = await device_repo.get_by_mqtt_client_id(mqtt_client_id)
        if device is None:
            logger.warning(
                "Rejecting telemetry from unprovisioned device '%s' on topic '%s' — "
                "register it via POST /api/v1/devices first",
                mqtt_client_id,
                topic,
            )
            return False

        # 2. The topic's site/greenhouse are hints. Report disagreement, but
        #    the provisioned hierarchy wins — a mislabelled topic must never
        #    silently move a device between greenhouses.
        await self._warn_on_hierarchy_mismatch(parsed_topic, device.greenhouse_id)

        # 3. Liveness: the device just proved it is talking to us.
        dev = await self.session.get(DeviceModel, device.id)
        dev.last_seen_at = observed_at
        dev.status = DeviceStatus.ONLINE.value

        # 4. Iterate telemetry fields and record state changes
        for key, val in metrics.items():
            entity_unique_id = f"{mqtt_client_id}/{key}"
            res = await self.session.execute(
                select(EntityModel).where(EntityModel.unique_id == entity_unique_id)
            )
            entity = res.scalars().first()

            if not entity:
                entity = EntityModel(
                    id=uuid.uuid4(),
                    device_id=dev.id,
                    entity_type=EntityType.SENSOR.value,
                    device_class=key,
                    unique_id=entity_unique_id,
                    last_state={"value": val},
                    last_state_changed_at=observed_at,
                )
                self.session.add(entity)
                await self.session.flush()
                logger.info(f"Auto-registering new entity: {entity_unique_id}")
            elif entity.device_id != dev.id:
                # unique_id is globally UNIQUE, so an entity left behind by a
                # previous owner of this client id would otherwise be adopted
                # silently. Refuse rather than steal or crash on the insert.
                logger.warning(
                    "Skipping metric '%s': entity '%s' already belongs to device %s",
                    key,
                    entity_unique_id,
                    entity.device_id,
                )
                continue
            else:
                entity.last_state = {"value": val}
                entity.last_state_changed_at = observed_at

            # Record state change entry
            state_change = StateChangeModel(
                id=uuid.uuid4(),
                entity_id=entity.id,
                value={"value": val},
                recorded_at=observed_at,
            )
            self.session.add(state_change)
            logger.info(f"Recorded {key} = {val} for {mqtt_client_id}")

        return True

    async def _warn_on_hierarchy_mismatch(self, parsed_topic, greenhouse_id) -> None:
        """Compare the topic's routing hints against the provisioned truth."""
        result = await self.session.execute(
            select(GreenhouseModel.name, SiteModel.name)
            .join(SiteModel, GreenhouseModel.site_id == SiteModel.id)
            .where(GreenhouseModel.id == greenhouse_id)
        )
        row = result.first()
        if row is None:
            return

        actual_greenhouse, actual_site = row
        if actual_site != parsed_topic.site or actual_greenhouse != parsed_topic.greenhouse:
            logger.warning(
                "Topic hierarchy '%s/%s' does not match provisioned hierarchy "
                "'%s/%s' for device '%s'; ingesting under the provisioned "
                "hierarchy and leaving ownership unchanged",
                parsed_topic.site,
                parsed_topic.greenhouse,
                actual_site,
                actual_greenhouse,
                parsed_topic.mqtt_client_id,
            )
