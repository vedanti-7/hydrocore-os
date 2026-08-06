"""Greenhouse endpoints — growing areas within a Site."""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import DeviceRepositoryDep, GreenhouseRepositoryDep, SiteRepositoryDep
from app.api.schemas.device import DeviceRead
from app.api.schemas.greenhouse import GreenhouseCreate, GreenhouseRead
from app.domain.entities.greenhouse import Greenhouse

router = APIRouter(prefix="/api/v1/greenhouses", tags=["greenhouses"])


@router.post("", response_model=GreenhouseRead, status_code=status.HTTP_201_CREATED)
async def create_greenhouse(
    payload: GreenhouseCreate,
    repo: GreenhouseRepositoryDep,
    site_repo: SiteRepositoryDep,
) -> GreenhouseRead:
    # The FK would reject this anyway, but as a 500 — check first for a 404.
    if await site_repo.get(payload.site_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Site not found")

    created = await repo.create(
        Greenhouse(
            site_id=payload.site_id,
            name=payload.name,
            description=payload.description,
        )
    )
    return GreenhouseRead.model_validate(created)


@router.get("/{greenhouse_id}", response_model=GreenhouseRead)
async def get_greenhouse(greenhouse_id: UUID, repo: GreenhouseRepositoryDep) -> GreenhouseRead:
    greenhouse = await repo.get(greenhouse_id)
    if greenhouse is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Greenhouse not found")
    return GreenhouseRead.model_validate(greenhouse)


@router.get("/{greenhouse_id}/devices", response_model=list[DeviceRead])
async def list_greenhouse_devices(
    greenhouse_id: UUID,
    repo: GreenhouseRepositoryDep,
    device_repo: DeviceRepositoryDep,
) -> list[DeviceRead]:
    if await repo.get(greenhouse_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Greenhouse not found")
    devices = await device_repo.list_by_greenhouse(greenhouse_id)
    return [DeviceRead.model_validate(d) for d in devices]
