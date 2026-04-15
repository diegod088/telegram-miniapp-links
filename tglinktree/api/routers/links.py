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
from tglinktree.middleware.plan_limits import check_link_limit
from tglinktree.services.profile_service import get_profile_by_user, check_daily_limit
from tglinktree.services import discovery_service, social_service
import re
from datetime import datetime, timedelta

router = APIRouter(prefix="/profiles/me/links", tags=["links"])


@router.post("", response_model=LinkResponse, status_code=201)
async def add_link(
    data: LinkCreate,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
    _limit: None = Depends(check_link_limit),
):
    """Add a link to the user's profile."""
    # 0. Check daily limit
    await check_daily_limit(db, user)

    profile = await get_profile_by_user(db, user)

    # 1. Scrub URL
    canonical_url = await social_service.scrub_url(data.url)
    
    # 2. Scrape title if missing
    title = data.title
    if not title:
        scraped_title = await social_service.scrape_page_title(canonical_url)
        title = scraped_title or canonical_url # Fallback to URL as title

    # Sanitization (Adult Content Protection)
    forbidden_keywords = r"(porno|xxx|follar|sex|nudes)"
    title = re.sub(forbidden_keywords, "[Contenido]", title, flags=re.IGNORECASE)
    # Emojis protection
    title = re.sub(r"[🔞🍆💦]", "[Contenido]", title)

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
    
    # Update user statistics
    user.daily_link_count += 1
    user.last_link_created_at = datetime.utcnow()
    
    await db.flush()
    # Update search index in background
    await discovery_service.update_search_vector(db, profile.id)
    return link


@router.put("/{link_id}", response_model=LinkResponse)
async def edit_link(
    link_id: int,
    data: LinkUpdate,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Edit a link owned by the user."""
    link = await _get_own_link(db, user, link_id)

    if data.title is not None:
        # Sanitize title
        sanitized = re.sub(r"(porno|xxx|follar|sex|nudes)", "[Contenido]", data.title, flags=re.IGNORECASE)
        sanitized = re.sub(r"[🔞🍆💦]", "[Contenido]", sanitized)
        link.title = sanitized
    if data.url is not None:
        link.url = data.url
        link.canonical_url = await social_service.scrub_url(data.url)
    if data.description is not None:
        link.description = data.description
    if data.icon is not None:
        link.icon = data.icon
    if data.is_active is not None:
        link.is_active = data.is_active
    if data.link_type is not None:
        link.link_type = data.link_type
    if data.style is not None:
        link.style = data.style

    # is_premium only editable by VIP users
    if hasattr(data, "is_premium") and getattr(data, "is_premium", None) is not None:
        profile = await get_profile_by_user(db, user)
        if profile.plan in ("pro", "business"):
            link.is_premium = data.is_premium

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


@router.post("/{link_id}/boost", response_model=LinkResponse)
async def boost_link(
    link_id: int,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Boost a link for 24h (Pro/Business Plan required)."""
    profile = await get_profile_by_user(db, user)
    
    if profile.plan not in ["pro", "business"]:
        from tglinktree.core.exceptions import ForbiddenError
        raise ForbiddenError("Upgrade help reach more people with Boost.")

    link = await _get_own_link(db, user, link_id)
    link.boosted_until = datetime.utcnow() + timedelta(days=1)
    
    await db.flush()
    return link


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
