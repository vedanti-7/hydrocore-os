"""
Repository interfaces — the only contract business logic depends on.

Automation Engine, Sensor Manager, and the API layer will all take these
as constructor dependencies, never a concrete SQLAlchemy repository
directly. This is what makes domain services testable with an in-memory
fake instead of a real database.
"""
from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.device import Device
from app.domain.entities.entity import Entity
from app.domain.entities.greenhouse import Greenhouse
from app.domain.entities.site import Site
from app.domain.entities.state_change import StateChange


class ISiteRepository(ABC):
    @abstractmethod
    async def create(self, site: Site) -> Site: ...

    @abstractmethod
    async def get(self, site_id: UUID) -> Site | None: ...

    @abstractmethod
    async def list_all(self) -> list[Site]: ...


class IGreenhouseRepository(ABC):
    @abstractmethod
    async def create(self, greenhouse: Greenhouse) -> Greenhouse: ...

    @abstractmethod
    async def get(self, greenhouse_id: UUID) -> Greenhouse | None: ...

    @abstractmethod
    async def list_by_site(self, site_id: UUID) -> list[Greenhouse]: ...


class IDeviceRepository(ABC):
    @abstractmethod
    async def create(self, device: Device) -> Device: ...

    @abstractmethod
    async def get(self, device_id: UUID) -> Device | None: ...

    @abstractmethod
    async def get_by_mqtt_client_id(self, mqtt_client_id: str) -> Device | None: ...

    @abstractmethod
    async def list_by_greenhouse(self, greenhouse_id: UUID) -> list[Device]: ...

    @abstractmethod
    async def update_status(self, device_id: UUID, status: str, seen_at) -> None: ...


class IEntityRepository(ABC):
    @abstractmethod
    async def create(self, entity: Entity) -> Entity: ...

    @abstractmethod
    async def get(self, entity_id: UUID) -> Entity | None: ...

    @abstractmethod
    async def get_by_unique_id(self, unique_id: str) -> Entity | None: ...

    @abstractmethod
    async def list_by_device(self, device_id: UUID) -> list[Entity]: ...

    @abstractmethod
    async def record_state_change(self, change: StateChange) -> None:
        """Inserts a StateChange row AND updates Entity.last_state — atomic."""
        ...
