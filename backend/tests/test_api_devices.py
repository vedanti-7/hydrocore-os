"""Device API tests — parent validation, enum validation, unique constraint."""
from uuid import uuid4

import pytest


async def _create_greenhouse(client) -> str:
    site_id = (await client.post("/api/v1/sites", json={"name": "Device Test Farm"})).json()["id"]
    response = await client.post(
        "/api/v1/greenhouses", json={"site_id": site_id, "name": "Device Test GH"}
    )
    assert response.status_code == 201
    return response.json()["id"]


def _device_payload(greenhouse_id: str, **overrides) -> dict:
    # mqtt_client_id is globally unique and the dev DB is never reset between
    # runs, so every test invents a fresh one.
    payload = {
        "greenhouse_id": greenhouse_id,
        "name": "Env Monitor",
        "device_type": "env_monitor",
        "mqtt_client_id": f"env-monitor-{uuid4().hex[:12]}",
    }
    return payload | overrides


@pytest.mark.asyncio
async def test_create_device_returns_201_with_default_unknown_status(client):
    greenhouse_id = await _create_greenhouse(client)

    response = await client.post("/api/v1/devices", json=_device_payload(greenhouse_id))
    assert response.status_code == 201

    body = response.json()
    assert body["greenhouse_id"] == greenhouse_id
    assert body["device_type"] == "env_monitor"
    assert body["status"] == "unknown"
    assert body["last_seen_at"] is None

    fetched = await client.get(f"/api/v1/devices/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == body


@pytest.mark.asyncio
async def test_create_device_accepts_explicit_status(client):
    greenhouse_id = await _create_greenhouse(client)

    response = await client.post(
        "/api/v1/devices", json=_device_payload(greenhouse_id, status="online")
    )
    assert response.status_code == 201
    assert response.json()["status"] == "online"


@pytest.mark.asyncio
async def test_duplicate_mqtt_client_id_returns_409(client):
    greenhouse_id = await _create_greenhouse(client)
    payload = _device_payload(greenhouse_id)

    assert (await client.post("/api/v1/devices", json=payload)).status_code == 201

    duplicate = await client.post("/api/v1/devices", json=payload)
    assert duplicate.status_code == 409
    assert payload["mqtt_client_id"] in duplicate.json()["detail"]


@pytest.mark.asyncio
async def test_create_device_for_unknown_greenhouse_returns_404(client):
    response = await client.post("/api/v1/devices", json=_device_payload(str(uuid4())))
    assert response.status_code == 404
    assert response.json()["detail"] == "Greenhouse not found"


@pytest.mark.asyncio
async def test_invalid_device_type_returns_422(client):
    greenhouse_id = await _create_greenhouse(client)

    response = await client.post(
        "/api/v1/devices", json=_device_payload(greenhouse_id, device_type="toaster")
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_devices_scoped_to_their_own_greenhouse(client):
    greenhouse_a = await _create_greenhouse(client)
    greenhouse_b = await _create_greenhouse(client)

    created = (
        await client.post("/api/v1/devices", json=_device_payload(greenhouse_a))
    ).json()

    in_a = await client.get(f"/api/v1/greenhouses/{greenhouse_a}/devices")
    assert in_a.status_code == 200
    assert [d["id"] for d in in_a.json()] == [created["id"]]

    in_b = await client.get(f"/api/v1/greenhouses/{greenhouse_b}/devices")
    assert in_b.json() == []


@pytest.mark.asyncio
async def test_get_unknown_device_returns_404(client):
    response = await client.get(f"/api/v1/devices/{uuid4()}")
    assert response.status_code == 404
