"""Link endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, rate_limit_auth
from app.models.user import User
from app.schemas.link import LinkCreate, LinkReorder, LinkResponse, LinkUpdate
from app.services.link_service import LinkService

router = APIRouter(prefix="/profiles/me/links", tags=["links"])


@router.post("", response_model=LinkResponse, status_code=201)
async def add_link(
    data: LinkCreate,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Add a link to the user's profile."""
    service = LinkService(db)
    return await service.create_link(user, data)


@router.put("/{link_id}", response_model=LinkResponse)
async def edit_link(
    link_id: int,
    data: LinkUpdate,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Edit a link owned by the user."""
    service = LinkService(db)
    return await service.update_link(user, link_id, data)


@router.delete("/{link_id}", status_code=204)
async def delete_link(
    link_id: int,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Delete a link owned by the user."""
    service = LinkService(db)
    await service.delete_link(user, link_id)


@router.post("/reorder", status_code=200)
async def reorder_links(
    data: LinkReorder,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Reorder links."""
    service = LinkService(db)
    await service.reorder_links(user, data.link_ids)
    return {"message": "Links reordered successfully."}


@router.post("/{link_id}/boost", response_model=LinkResponse)
async def boost_link(
    link_id: int,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Boost a link for 24h."""
    service = LinkService(db)
    return await service.boost_link(user, link_id)
