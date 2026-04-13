"""Profile endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from tglinktree.api.deps import get_db, rate_limit_auth, rate_limit_public
from tglinktree.api.auth import get_current_user
from tglinktree.models.lock import ContentLock
from tglinktree.models.user import User
from tglinktree.schemas.profile import (
    ProfileCreate,
    ProfilePublicResponse,
    ProfileResponse,
    ProfileUpdate,
    LinkInProfile,
)
from tglinktree.services import profile_service
from tglinktree.services.analytics_service import track_event

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("", response_model=ProfileResponse, status_code=201)
async def create_profile(
    data: ProfileCreate,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Create a new profile (one per user)."""
    profile = await profile_service.create_profile(db, user, data)
    return profile


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the authenticated user's profile."""
    profile = await profile_service.get_profile_by_user(db, user)
    return profile


@router.get("/{slug}", response_model=ProfilePublicResponse)
async def get_public_profile(
    slug: str,
    db: AsyncSession = Depends(get_db),
    _rate: None = Depends(rate_limit_public),
):
    """Get a public profile by slug. No auth required."""
    profile = await profile_service.get_profile_by_slug(db, slug)

    # Build response with lock status per link
    links = []
    for link in profile.links:
        if not link.is_active:
            continue
        # Check if link has an active lock
        has_lock = any(
            lock.is_active for lock in link.locks
        ) if link.locks else False

        links.append(LinkInProfile(
            id=link.id,
            title=link.title,
            url=link.url if not has_lock else "",
            description=link.description,
            icon=link.icon,
            position=link.position,
            is_active=link.is_active,
            link_type=link.link_type,
            style=link.style or {},
            is_locked=has_lock,
        ))

    # Fire-and-forget view tracking (no await needed for response)
    await track_event(
        db=db,
        profile_id=profile.id,
        event_type="profile_view",
    )

    return ProfilePublicResponse(
        slug=profile.slug,
        display_name=profile.display_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        theme=profile.theme,
        total_views=profile.total_views,
        links=links,
    )


@router.patch("/me", response_model=ProfileResponse)
async def update_my_profile(
    data: ProfileUpdate,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Update the authenticated user's profile."""
    profile = await profile_service.update_profile(db, user, data)
    return profile
