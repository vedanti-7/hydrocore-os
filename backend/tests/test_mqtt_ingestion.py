"""
MQTT telemetry ingestion tests.

Drives handle_mqtt_message() directly — the same entry point the broker
listener calls — so the consumer's transaction boundary, the topic contract
and the ingestion service are all exercised together against real Postgres.
No broker is involved: the listener loop is transport, not logic.

    docker compose exec backend pytest tests/test_mqtt_ingestion.py -v

Devices must be provisioned before they may publish, so each test first
creates its Site -> Greenhouse -> Device through the REST API — the real
operator flow. Every test invents its own identifiers, because
devices.mqtt_client_id and entities.unique_id are UNIQUE and the dev
database is never reset between runs.
"""
import json
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.infrastructure.database.models import (
    DeviceModel,
    EntityModel,
    GreenhouseModel,
    SiteModel,
    StateChangeModel,
)
from app.infrastructure.database.session import async_session_factory
from app.infrastructure.mqtt.consumer import handle_mqtt_message


class Provisioned:
    """A registered device plus the topic it is entitled to publish on."""

    def __init__(self, site: str, greenhouse: str, mqtt_client_id: str, device_id: str):
        self.site = site
        self.greenhouse = greenhouse
        self.mqtt_client_id = mqtt_client_id
        self.device_id = device_id
        self.topic = f"hydrocore/{site}/{greenhouse}/{mqtt_client_id}/telemetry"

    def topic_for(self, site: str | None = None, greenhouse: str | None = None) -> str:
        """The same device's topic with deliberately wrong routing hints."""
        return (
            f"hydrocore/{site or self.site}/{greenhouse or self.greenhouse}/"
            f"{self.mqtt_client_id}/telemetry"
        )


async def _provision(client, device_name: str = "Water Monitor", site_id: str | None = None):
    """Register Site -> Greenhouse -> Device through the REST API."""
    suffix = uuid4().hex[:12]

    if site_id is None:
        site_response = await client.post("/api/v1/sites", json={"name": f"site-{suffix}"})
        assert site_response.status_code == 201
        site_id = site_response.json()["id"]
    site_name = (await client.get(f"/api/v1/sites/{site_id}")).json()["name"]

    greenhouse_response = await client.post(
        "/api/v1/greenhouses", json={"site_id": site_id, "name": f"gh-{suffix}"}
    )
    assert greenhouse_response.status_code == 201
    greenhouse = greenhouse_response.json()

    mqtt_client_id = f"esp32-{suffix}"
    device_response = await client.post(
        "/api/v1/devices",
        json={
            "greenhouse_id": greenhouse["id"],
            "name": device_name,
            "device_type": "water_monitor",
            "mqtt_client_id": mqtt_client_id,
        },
    )
    assert device_response.status_code == 201

    return Provisioned(
        site=site_name,
        greenhouse=greenhouse["name"],
        mqtt_client_id=mqtt_client_id,
        device_id=device_response.json()["id"],
    )


def _unprovisioned_topic() -> tuple[str, str]:
    """A well-formed topic whose device was never registered."""
    suffix = uuid4().hex[:12]
    mqtt_client_id = f"ghost-{suffix}"
    return mqtt_client_id, f"hydrocore/site-{suffix}/gh-{suffix}/{mqtt_client_id}/telemetry"


async def _get_device(device_id) -> DeviceModel | None:
    async with async_session_factory() as session:
        return await session.get(DeviceModel, device_id)


async def _get_entity(unique_id: str) -> EntityModel | None:
    async with async_session_factory() as session:
        result = await session.execute(
            select(EntityModel).where(EntityModel.unique_id == unique_id)
        )
        return result.scalars().first()


async def _count_state_changes(entity_id) -> int:
    async with async_session_factory() as session:
        result = await session.execute(
            select(func.count())
            .select_from(StateChangeModel)
            .where(StateChangeModel.entity_id == entity_id)
        )
        return result.scalar_one()


async def _count_entities_for_device(device_id) -> int:
    async with async_session_factory() as session:
        result = await session.execute(
            select(func.count()).select_from(EntityModel).where(EntityModel.device_id == device_id)
        )
        return result.scalar_one()


async def _assert_no_hierarchy_created(mqtt_client_id: str, site: str, greenhouse: str) -> None:
    """An unprovisioned device must not be able to conjure any row."""
    async with async_session_factory() as session:
        devices = await session.execute(
            select(DeviceModel).where(DeviceModel.mqtt_client_id == mqtt_client_id)
        )
        assert devices.scalars().first() is None

        sites = await session.execute(select(SiteModel).where(SiteModel.name == site))
        assert sites.scalars().first() is None

        greenhouses = await session.execute(
            select(GreenhouseModel).where(GreenhouseModel.name == greenhouse)
        )
        assert greenhouses.scalars().first() is None

        entities = await session.execute(
            select(EntityModel).where(EntityModel.unique_id.like(f"{mqtt_client_id}/%"))
        )
        assert entities.scalars().all() == []


# --------------------------------------------------------------------------
# Provisioned devices: the happy path
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_provisioned_device_telemetry_is_ingested(client):
    device = await _provision(client)

    await handle_mqtt_message(device.topic, json.dumps({"ph": 6.1}))

    entity = await _get_entity(f"{device.mqtt_client_id}/ph")
    assert entity is not None
    assert entity.device_class == "ph"
    assert entity.entity_type == "sensor"
    assert entity.last_state == {"value": 6.1}
    assert entity.last_state_changed_at is not None
    assert await _count_state_changes(entity.id) == 1


@pytest.mark.asyncio
async def test_device_is_resolved_by_mqtt_client_id(client):
    device = await _provision(client)

    await handle_mqtt_message(device.topic, json.dumps({"ph": 6.1}))

    entity = await _get_entity(f"{device.mqtt_client_id}/ph")
    # Attached to the provisioned row itself, not a look-alike created by name.
    assert str(entity.device_id) == device.device_id


@pytest.mark.asyncio
async def test_entities_still_auto_register_for_valid_device_classes(client):
    device = await _provision(client)

    await handle_mqtt_message(
        device.topic, json.dumps({"ph": 6.1, "ec": 1.8, "water_temperature": 23.7})
    )

    assert await _count_entities_for_device(device.device_id) == 3
    for metric, value in (("ph", 6.1), ("ec", 1.8), ("water_temperature", 23.7)):
        entity = await _get_entity(f"{device.mqtt_client_id}/{metric}")
        assert entity is not None, metric
        assert entity.last_state == {"value": value}


@pytest.mark.asyncio
async def test_repeated_telemetry_updates_last_state_and_appends_history(client):
    device = await _provision(client)

    await handle_mqtt_message(device.topic, json.dumps({"ph": 6.1}))
    entity = await _get_entity(f"{device.mqtt_client_id}/ph")
    first_changed_at = entity.last_state_changed_at

    await handle_mqtt_message(device.topic, json.dumps({"ph": 6.4}))

    entity = await _get_entity(f"{device.mqtt_client_id}/ph")
    assert entity.last_state == {"value": 6.4}
    assert entity.last_state_changed_at > first_changed_at
    # History is append-only: the earlier reading survives.
    assert await _count_state_changes(entity.id) == 2


@pytest.mark.asyncio
async def test_repeated_telemetry_does_not_duplicate_entities(client):
    device = await _provision(client)

    for _ in range(3):
        await handle_mqtt_message(device.topic, json.dumps({"ph": 6.1, "ec": 1.8}))

    assert await _count_entities_for_device(device.device_id) == 2
    entity = await _get_entity(f"{device.mqtt_client_id}/ph")
    assert await _count_state_changes(entity.id) == 3


@pytest.mark.asyncio
async def test_telemetry_updates_last_seen_at_and_sets_status_online(client):
    device = await _provision(client)

    row = await _get_device(device.device_id)
    assert row.status == "unknown"
    assert row.last_seen_at is None

    await handle_mqtt_message(device.topic, json.dumps({"ph": 6.1}))

    row = await _get_device(device.device_id)
    assert row.status == "online"
    assert row.last_seen_at is not None


# --------------------------------------------------------------------------
# Identity and ownership
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_mqtt_client_id_writes_nothing(client):
    mqtt_client_id, topic = _unprovisioned_topic()
    site, greenhouse = topic.split("/")[1], topic.split("/")[2]

    await handle_mqtt_message(topic, json.dumps({"ph": 6.1}))

    await _assert_no_hierarchy_created(mqtt_client_id, site, greenhouse)


@pytest.mark.asyncio
async def test_unknown_device_cannot_auto_create_hierarchy_over_many_messages(client):
    mqtt_client_id, topic = _unprovisioned_topic()
    site, greenhouse = topic.split("/")[1], topic.split("/")[2]

    for _ in range(3):
        await handle_mqtt_message(topic, json.dumps({"ph": 6.1, "ec": 1.8}))

    await _assert_no_hierarchy_created(mqtt_client_id, site, greenhouse)


@pytest.mark.asyncio
async def test_same_device_name_in_different_greenhouses_is_unambiguous(client):
    """
    The regression that motivated identity-based lookup: name matching used
    .first() over a non-unique column, so identically named devices were
    indistinguishable.
    """
    first = await _provision(client, device_name="Water Monitor")
    second = await _provision(client, device_name="Water Monitor")

    await handle_mqtt_message(first.topic, json.dumps({"ph": 6.1}))
    await handle_mqtt_message(second.topic, json.dumps({"ph": 7.9}))

    first_entity = await _get_entity(f"{first.mqtt_client_id}/ph")
    second_entity = await _get_entity(f"{second.mqtt_client_id}/ph")

    assert str(first_entity.device_id) == first.device_id
    assert str(second_entity.device_id) == second.device_id
    assert first_entity.last_state == {"value": 6.1}
    assert second_entity.last_state == {"value": 7.9}
    assert await _count_entities_for_device(first.device_id) == 1
    assert await _count_entities_for_device(second.device_id) == 1


@pytest.mark.asyncio
async def test_topic_hierarchy_mismatch_does_not_change_ownership(client):
    device = await _provision(client)
    original = await _get_device(device.device_id)
    original_greenhouse_id = original.greenhouse_id

    wrong_topic = device.topic_for(site="somewhere-else", greenhouse="not-this-one")
    await handle_mqtt_message(wrong_topic, json.dumps({"ph": 6.1}))

    # Ingested under the provisioned device, and the device did not move.
    entity = await _get_entity(f"{device.mqtt_client_id}/ph")
    assert entity is not None
    assert str(entity.device_id) == device.device_id

    row = await _get_device(device.device_id)
    assert row.greenhouse_id == original_greenhouse_id

    async with async_session_factory() as session:
        stray = await session.execute(
            select(SiteModel).where(SiteModel.name == "somewhere-else")
        )
        assert stray.scalars().first() is None


# --------------------------------------------------------------------------
# Rejection paths (unchanged behaviour, re-verified under provisioning)
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_malformed_json_is_rejected(client):
    device = await _provision(client)

    await handle_mqtt_message(device.topic, "{ph:6.1,ec:1.8}")

    assert await _count_entities_for_device(device.device_id) == 0
    assert await _get_entity(f"{device.mqtt_client_id}/raw_value") is None
    # A rejected payload must not count as liveness either.
    assert (await _get_device(device.device_id)).status == "unknown"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "topic_template",
    [
        "hydrocore/{site}/{greenhouse}/{mqtt_client_id}",
        "hydrocore/{site}/{greenhouse}/{mqtt_client_id}/status",
        "hydrocore/{site}/{mqtt_client_id}/telemetry",
        "hydrocore/{site}/{greenhouse}/{mqtt_client_id}/telemetry/extra",
        "other/{site}/{greenhouse}/{mqtt_client_id}/telemetry",
        "hydrocore//{greenhouse}/{mqtt_client_id}/telemetry",
    ],
)
async def test_malformed_topic_is_rejected(client, topic_template):
    device = await _provision(client)
    topic = topic_template.format(
        site=device.site, greenhouse=device.greenhouse, mqtt_client_id=device.mqtt_client_id
    )

    await handle_mqtt_message(topic, json.dumps({"ph": 6.1}))

    assert await _count_entities_for_device(device.device_id) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", ["[1, 2, 3]", '"just a string"', "null", "42", "{}", ""])
async def test_invalid_payload_is_rejected(client, payload):
    device = await _provision(client)

    await handle_mqtt_message(device.topic, payload)

    assert await _count_entities_for_device(device.device_id) == 0


@pytest.mark.asyncio
async def test_unknown_metric_is_skipped_but_known_metrics_ingest(client):
    device = await _provision(client)

    await handle_mqtt_message(device.topic, json.dumps({"ph": 6.1, "unicorn_count": 3}))

    assert await _count_entities_for_device(device.device_id) == 1
    assert await _get_entity(f"{device.mqtt_client_id}/ph") is not None
    assert await _get_entity(f"{device.mqtt_client_id}/unicorn_count") is None


@pytest.mark.asyncio
async def test_non_scalar_metric_value_is_skipped(client):
    device = await _provision(client)

    await handle_mqtt_message(device.topic, json.dumps({"ph": {"nested": 6.1}, "ec": 1.8}))

    assert await _count_entities_for_device(device.device_id) == 1
    assert await _get_entity(f"{device.mqtt_client_id}/ph") is None
    assert await _get_entity(f"{device.mqtt_client_id}/ec") is not None


@pytest.mark.asyncio
async def test_auto_registered_entities_are_readable_through_the_rest_api(client):
    device = await _provision(client)

    await handle_mqtt_message(device.topic, json.dumps({"ph": 6.1}))

    device_response = await client.get(f"/api/v1/devices/{device.device_id}")
    assert device_response.status_code == 200
    assert device_response.json()["status"] == "online"

    entities_response = await client.get(f"/api/v1/devices/{device.device_id}/entities")
    assert entities_response.status_code == 200
    assert [e["device_class"] for e in entities_response.json()] == ["ph"]
