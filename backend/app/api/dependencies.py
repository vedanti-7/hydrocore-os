"""
API composition root — the single place concrete repositories are chosen.

This is the ONLY module in app/api that may import from
app.infrastructure.database.repositories. Route handlers depend on the
Annotated aliases below, whose declared types are the domain interfaces, so
swapping the persistence layer (or injecting fakes in a test) is a change
confined to this file.
"""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.repositories import (
    IDeviceRepository,
    IEntityRepository,
    IGreenhouseRepository,
    ISiteRepository,
)
from app.infrastructure.database.repositories.device_repository import (
    SqlAlchemyDeviceRepository,
    SqlAlchemyGreenhouseRepository,
    SqlAlchemySiteRepository,
)
from app.infrastructure.database.repositories.entity_repository import (
    SqlAlchemyEntityRepository,
)
from app.infrastructure.database.session import get_session

# One session per request, closed by get_session's generator teardown.
SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_site_repository(session: SessionDep) -> ISiteRepository:
    return SqlAlchemySiteRepository(session)


def get_greenhouse_repository(session: SessionDep) -> IGreenhouseRepository:
    return SqlAlchemyGreenhouseRepository(session)


def get_device_repository(session: SessionDep) -> IDeviceRepository:
    return SqlAlchemyDeviceRepository(session)


def get_entity_repository(session: SessionDep) -> IEntityRepository:
    return SqlAlchemyEntityRepository(session)


SiteRepositoryDep = Annotated[ISiteRepository, Depends(get_site_repository)]
GreenhouseRepositoryDep = Annotated[IGreenhouseRepository, Depends(get_greenhouse_repository)]
DeviceRepositoryDep = Annotated[IDeviceRepository, Depends(get_device_repository)]
EntityRepositoryDep = Annotated[IEntityRepository, Depends(get_entity_repository)]
