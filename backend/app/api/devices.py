"""
Device endpoints — physical ESP32 nodes within a Greenhouse.

Devices are normally born from MQTT discovery; this router exists for manual
provisioning and for the frontend's device list.
"""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import DeviceRepositoryDep, EntityRepositoryDep, GreenhouseRepositoryDep
from app.api.schemas.device import DeviceCreate, DeviceRead
from app.api.schemas.entity import EntityRead
from app.domain.entities.device import Device

router = APIRouter(prefix="/api/v1/devices", tags=["devices"])


@router.post("", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
async def create_device(
    payload: DeviceCreate,
    repo: DeviceRepositoryDep,
    greenhouse_repo: GreenhouseRepositoryDep,
) -> DeviceRead:
    if await greenhouse_repo.get(payload.greenhouse_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Greenhouse not found")

    # mqtt_client_id is UNIQUE in the schema. Checking first turns the common
    # case into a clean 409; a concurrent duplicate still loses to the DB
    # constraint, which is the correct authority.
    if await repo.get_by_mqtt_client_id(payload.mqtt_client_id) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"Device with mqtt_client_id '{payload.mqtt_client_id}' already exists",
        )

    created = await repo.create(
        Device(
            greenhouse_id=payload.greenhouse_id,
            name=payload.name,
            device_type=payload.device_type,
            mqtt_client_id=payload.mqtt_client_id,
            status=payload.status,
            firmware_version=payload.firmware_version,
        )
    )
    return DeviceRead.model_validate(created)


@router.get("/{device_id}", response_model=DeviceRead)
async def get_device(device_id: UUID, repo: DeviceRepositoryDep) -> DeviceRead:
    device = await repo.get(device_id)
    if device is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Device not found")
    return DeviceRead.model_validate(device)


@router.get("/{device_id}/entities", response_model=list[EntityRead])
async def list_device_entities(
    device_id: UUID,
    repo: DeviceRepositoryDep,
    entity_repo: EntityRepositoryDep,
) -> list[EntityRead]:
    if await repo.get(device_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Device not found")
    entities = await entity_repo.list_by_device(device_id)
    return [EntityRead.model_validate(e) for e in entities]
