"""
Entity endpoints — individual sensor/actuator points on a Device.

Read-heavy by design: the dashboard polls these for current state. Writing
state is the MQTT ingestion path's job, not an HTTP concern, so there is no
state-write endpoint here.
"""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import DeviceRepositoryDep, EntityRepositoryDep
from app.api.schemas.entity import EntityCreate, EntityRead
from app.domain.entities.entity import Entity

router = APIRouter(prefix="/api/v1/entities", tags=["entities"])


@router.post("", response_model=EntityRead, status_code=status.HTTP_201_CREATED)
async def create_entity(
    payload: EntityCreate,
    repo: EntityRepositoryDep,
    device_repo: DeviceRepositoryDep,
) -> EntityRead:
    if await device_repo.get(payload.device_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Device not found")

    # unique_id is UNIQUE in the schema — same pre-check rationale as devices.
    if await repo.get_by_unique_id(payload.unique_id) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"Entity with unique_id '{payload.unique_id}' already exists",
        )

    created = await repo.create(
        Entity(
            device_id=payload.device_id,
            entity_type=payload.entity_type,
            device_class=payload.device_class,
            unique_id=payload.unique_id,
            unit=payload.unit,
            attributes=payload.attributes,
        )
    )
    return EntityRead.model_validate(created)


@router.get("/{entity_id}", response_model=EntityRead)
async def get_entity(entity_id: UUID, repo: EntityRepositoryDep) -> EntityRead:
    entity = await repo.get(entity_id)
    if entity is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Entity not found")
    return EntityRead.model_validate(entity)
