"""Entity API tests — the leaf of the hierarchy, including full chain setup."""
from uuid import uuid4

import pytest


async def _create_device(client) -> str:
    site_id = (await client.post("/api/v1/sites", json={"name": "Entity Test Farm"})).json()["id"]
    greenhouse_id = (
        await client.post(
            "/api/v1/greenhouses", json={"site_id": site_id, "name": "Entity Test GH"}
        )
    ).json()["id"]
    response = await client.post(
        "/api/v1/devices",
        json={
            "greenhouse_id": greenhouse_id,
            "name": "Env Monitor",
            "device_type": "env_monitor",
            "mqtt_client_id": f"entity-test-{uuid4().hex[:12]}",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _entity_payload(device_id: str, **overrides) -> dict:
    payload = {
        "device_id": device_id,
        "entity_type": "sensor",
        "device_class": "temperature",
        "unique_id": f"env-monitor-{uuid4().hex[:12]}/temperature",
        "unit": "°C",
    }
    return payload | overrides


@pytest.mark.asyncio
async def test_create_entity_returns_201_with_null_initial_state(client):
    device_id = await _create_device(client)

    response = await client.post("/api/v1/entities", json=_entity_payload(device_id))
    assert response.status_code == 201

    body = response.json()
    assert body["device_id"] == device_id
    assert body["entity_type"] == "sensor"
    assert body["device_class"] == "temperature"
    assert body["unit"] == "°C"
    # No telemetry has arrived yet, so state must be absent rather than 0.
    assert body["last_state"] is None
    assert body["last_state_changed_at"] is None
    assert body["attributes"] == {}

    fetched = await client.get(f"/api/v1/entities/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == body


@pytest.mark.asyncio
async def test_create_entity_preserves_attributes(client):
    device_id = await _create_device(client)

    response = await client.post(
        "/api/v1/entities",
        json=_entity_payload(device_id, attributes={"min": 0, "max": 50}),
    )
    assert response.status_code == 201
    assert response.json()["attributes"] == {"min": 0, "max": 50}


@pytest.mark.asyncio
async def test_duplicate_unique_id_returns_409(client):
    device_id = await _create_device(client)
    payload = _entity_payload(device_id)

    assert (await client.post("/api/v1/entities", json=payload)).status_code == 201

    duplicate = await client.post("/api/v1/entities", json=payload)
    assert duplicate.status_code == 409
    assert payload["unique_id"] in duplicate.json()["detail"]


@pytest.mark.asyncio
async def test_create_entity_for_unknown_device_returns_404(client):
    response = await client.post("/api/v1/entities", json=_entity_payload(str(uuid4())))
    assert response.status_code == 404
    assert response.json()["detail"] == "Device not found"


@pytest.mark.asyncio
async def test_invalid_device_class_returns_422(client):
    device_id = await _create_device(client)

    response = await client.post(
        "/api/v1/entities", json=_entity_payload(device_id, device_class="vibes")
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_entities_scoped_to_their_own_device(client):
    device_a = await _create_device(client)
    device_b = await _create_device(client)

    created = (await client.post("/api/v1/entities", json=_entity_payload(device_a))).json()

    in_a = await client.get(f"/api/v1/devices/{device_a}/entities")
    assert in_a.status_code == 200
    assert [e["id"] for e in in_a.json()] == [created["id"]]

    in_b = await client.get(f"/api/v1/devices/{device_b}/entities")
    assert in_b.json() == []


@pytest.mark.asyncio
async def test_get_unknown_entity_returns_404(client):
    response = await client.get(f"/api/v1/entities/{uuid4()}")
    assert response.status_code == 404
