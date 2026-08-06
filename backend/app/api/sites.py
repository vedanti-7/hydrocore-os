"""
Site endpoints — top of the Site -> Greenhouse -> Device -> Entity hierarchy.

Handlers stay thin on purpose: validate, call a repository, map to a schema.
Anything more than that belongs in a domain service, not here.
"""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import GreenhouseRepositoryDep, SiteRepositoryDep
from app.api.schemas.greenhouse import GreenhouseRead
from app.api.schemas.site import SiteCreate, SiteRead
from app.domain.entities.site import Site

router = APIRouter(prefix="/api/v1/sites", tags=["sites"])


@router.post("", response_model=SiteRead, status_code=status.HTTP_201_CREATED)
async def create_site(payload: SiteCreate, repo: SiteRepositoryDep) -> SiteRead:
    created = await repo.create(Site(name=payload.name, timezone=payload.timezone))
    return SiteRead.model_validate(created)


@router.get("", response_model=list[SiteRead])
async def list_sites(repo: SiteRepositoryDep) -> list[SiteRead]:
    return [SiteRead.model_validate(s) for s in await repo.list_all()]


@router.get("/{site_id}", response_model=SiteRead)
async def get_site(site_id: UUID, repo: SiteRepositoryDep) -> SiteRead:
    site = await repo.get(site_id)
    if site is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Site not found")
    return SiteRead.model_validate(site)


@router.get("/{site_id}/greenhouses", response_model=list[GreenhouseRead])
async def list_site_greenhouses(
    site_id: UUID,
    site_repo: SiteRepositoryDep,
    greenhouse_repo: GreenhouseRepositoryDep,
) -> list[GreenhouseRead]:
    # Distinguish "no such site" (404) from "site exists but is empty" ([]).
    if await site_repo.get(site_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Site not found")
    greenhouses = await greenhouse_repo.list_by_site(site_id)
    return [GreenhouseRead.model_validate(g) for g in greenhouses]
