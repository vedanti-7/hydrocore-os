"""
Site API tests.

Runs against the real dev Postgres, same as the repository integration test:

    docker compose exec backend pytest tests/test_api_sites.py -v
"""
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_create_site_returns_201_and_persists(client):
    response = await client.post(
        "/api/v1/sites", json={"name": "Test Farm", "timezone": "Asia/Kolkata"}
    )
    assert response.status_code == 201

    body = response.json()
    assert body["name"] == "Test Farm"
    assert body["timezone"] == "Asia/Kolkata"
    assert body["id"]
    assert body["created_at"]

    # Round-trip: the created site is retrievable by the id we were handed.
    fetched = await client.get(f"/api/v1/sites/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == body


@pytest.mark.asyncio
async def test_create_site_defaults_timezone_to_utc(client):
    response = await client.post("/api/v1/sites", json={"name": "Default TZ Farm"})
    assert response.status_code == 201
    assert response.json()["timezone"] == "UTC"


@pytest.mark.asyncio
async def test_list_sites_includes_created_site(client):
    created = (await client.post("/api/v1/sites", json={"name": "Listed Farm"})).json()

    response = await client.get("/api/v1/sites")
    assert response.status_code == 200
    assert created["id"] in [site["id"] for site in response.json()]


@pytest.mark.asyncio
async def test_get_unknown_site_returns_404(client):
    response = await client.get(f"/api/v1/sites/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_malformed_site_id_returns_422(client):
    response = await client.get("/api/v1/sites/not-a-uuid")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_empty_name_is_rejected(client):
    response = await client.post("/api/v1/sites", json={"name": ""})
    assert response.status_code == 422
