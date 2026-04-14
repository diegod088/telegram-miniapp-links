"""Link endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tglinktree.api.deps import get_db, rate_limit_auth
from tglinktree.core.exceptions import ForbiddenError, NotFoundError
from tglinktree.models.link import ProfileLink
from tglinktree.models.profile import Profile
from tglinktree.models.user import User
from tglinktree.schemas.link import LinkCreate, LinkReorder, LinkResponse, LinkUpdate
from tglinktree.services.profile_service import check_link_limit, get_profile_by_user
from tglinktree.services import discovery_service, social_service

router = APIRouter(prefix="/profiles/me/links", tags=["links"])


@router.post("", response_model=LinkResponse, status_code=201)
async def add_link(
    data: LinkCreate,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Add a link to the user's profile."""
    profile = await get_profile_by_user(db, user)
    await check_link_limit(db, profile)

    # 1. Scrub URL
    canonical_url = await social_service.scrub_url(data.url)
    
    # 2. Scrape title if missing
    title = data.title
    if not title:
        scraped_title = await social_service.scrape_page_title(canonical_url)
        title = scraped_title or canonical_url # Fallback to URL as title

    # 3. Determine next position
    result = await db.execute(
        select(ProfileLink)
        .where(ProfileLink.profile_id == profile.id)
        .order_by(ProfileLink.position.desc())
        .limit(1)
    )
    last_link = result.scalar_one_or_none()
    next_position = (last_link.position + 1) if last_link else 0

    link = ProfileLink(
        profile_id=profile.id,
        title=title,
        url=data.url,
        canonical_url=canonical_url,
        category=data.category,
        description=data.description,
        icon=data.icon,
        link_type=data.link_type,
        style=data.style or {},
        position=next_position,
    )
    db.add(link)
    await db.flush()
    # Update search index in background
    await discovery_service.update_search_vector(db, profile.id)
    return link


@router.patch("/{link_id}", response_model=LinkResponse)
async def edit_link(
    link_id: int,
    data: LinkUpdate,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Edit a link owned by the user."""
    link = await _get_own_link(db, user, link_id)

    await db.flush()
    # Update search index
    await discovery_service.update_search_vector(db, link.profile_id)
    return link


@router.delete("/{link_id}", status_code=204)
async def delete_link(
    link_id: int,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Delete a link owned by the user."""
    link = await _get_own_link(db, user, link_id)
    profile_id = link.profile_id
    await db.delete(link)
    await db.commit() # Commit needed before refresh to see deleted state if using Joins
    await discovery_service.update_search_vector(db, profile_id)


@router.post("/reorder", status_code=200)
async def reorder_links(
    data: LinkReorder,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Reorder links by providing the full ordered list of link IDs."""
    profile = await get_profile_by_user(db, user)

    # Get all links for this profile
    result = await db.execute(
        select(ProfileLink).where(ProfileLink.profile_id == profile.id)
    )
    links = {link.id: link for link in result.scalars().all()}

    # Validate all IDs belong to this profile
    for i, link_id in enumerate(data.link_ids):
        if link_id not in links:
            raise NotFoundError(f"Link {link_id} not found in your profile.")
        links[link_id].position = i

    await db.flush()
    return {"message": "Links reordered successfully."}


async def _get_own_link(
    db: AsyncSession,
    user: User,
    link_id: int,
) -> ProfileLink:
    """Get a link that belongs to the user, or raise 404/403."""
    result = await db.execute(
        select(ProfileLink)
        .join(Profile)
        .where(ProfileLink.id == link_id, Profile.user_id == user.id)
    )
    link = result.scalar_one_or_none()
    if link is None:
        raise NotFoundError("Link not found or you don't own it.")
    return link
