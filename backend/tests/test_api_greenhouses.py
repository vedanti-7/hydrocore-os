"""Greenhouse API tests — including the Site -> Greenhouse parent link."""
from uuid import uuid4

import pytest


async def _create_site(client) -> str:
    response = await client.post("/api/v1/sites", json={"name": "GH Test Farm"})
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_greenhouse_returns_201_and_links_to_site(client):
    site_id = await _create_site(client)

    response = await client.post(
        "/api/v1/greenhouses",
        json={"site_id": site_id, "name": "Greenhouse A", "description": "North block"},
    )
    assert response.status_code == 201

    body = response.json()
    assert body["site_id"] == site_id
    assert body["name"] == "Greenhouse A"
    assert body["description"] == "North block"

    fetched = await client.get(f"/api/v1/greenhouses/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == body


@pytest.mark.asyncio
async def test_create_greenhouse_for_unknown_site_returns_404(client):
    response = await client.post(
        "/api/v1/greenhouses", json={"site_id": str(uuid4()), "name": "Orphan"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Site not found"


@pytest.mark.asyncio
async def test_list_greenhouses_scoped_to_their_own_site(client):
    site_a = await _create_site(client)
    site_b = await _create_site(client)

    created = (
        await client.post("/api/v1/greenhouses", json={"site_id": site_a, "name": "In A"})
    ).json()

    in_a = await client.get(f"/api/v1/sites/{site_a}/greenhouses")
    assert in_a.status_code == 200
    assert [g["id"] for g in in_a.json()] == [created["id"]]

    # A sibling site must not see it — proves the query filters by site_id.
    in_b = await client.get(f"/api/v1/sites/{site_b}/greenhouses")
    assert in_b.status_code == 200
    assert in_b.json() == []


@pytest.mark.asyncio
async def test_list_greenhouses_for_unknown_site_returns_404(client):
    response = await client.get(f"/api/v1/sites/{uuid4()}/greenhouses")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_unknown_greenhouse_returns_404(client):
    response = await client.get(f"/api/v1/greenhouses/{uuid4()}")
    assert response.status_code == 404
