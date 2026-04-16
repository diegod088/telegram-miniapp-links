"""Profile endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, rate_limit_auth, rate_limit_public
from app.api.auth import get_current_user, get_current_user_optional
from app.models.link import ProfileLink
from app.models.lock import ContentLock
from app.models.user import User
from app.schemas.profile import (
    ExploreProfileItem,
    ExploreResponse,
    ProfileCreate,
    ProfilePublicResponse,
    ProfileResponse,
    ProfileUpdate,
    LinkInProfile,
)
from app.services.profile_service import ProfileService
from app.services.discovery_service import DiscoveryService
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("", response_model=ProfileResponse, status_code=201)
async def create_profile(
    data: ProfileCreate,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Create a new profile (one per user)."""
    service = ProfileService(db)
    profile = await service.create_profile(user, data)
    return profile


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the authenticated user's profile."""
    service = ProfileService(db)
    profile = await service.get_my_profile(user)
    return profile


@router.get("/{slug}", response_model=ProfilePublicResponse)
async def get_public_profile(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
    _rate: None = Depends(rate_limit_public),
):
    """Get a public profile by slug. No auth required."""
    service = ProfileService(db)
    discovery = DiscoveryService(db)
    analytics = AnalyticsService(db)
    
    # 1. Determine viewer plan
    viewer_plan = "free"
    if user:
        try:
            viewer_profile = await service.get_my_profile(user)
            viewer_plan = viewer_profile.plan
        except Exception:
            pass

    # 2. Get profile with filtered links
    profile = await discovery.get_filtered_profile(slug, viewer_plan)

    # Build response with lock status per link
    links = []
    for link in profile.filtered_links:
        if not link.is_active:
            continue

        active_lock = None
        if link.locks:
            for lock in link.locks:
                if lock.is_active:
                    active_lock = lock
                    break

        links.append(LinkInProfile(
            id=link.id,
            title=link.title,
            url=link.url if not active_lock else "",
            description=link.description,
            icon=link.icon,
            position=link.position,
            is_active=link.is_active,
            link_type=link.link_type,
            style=link.style or {},
            is_locked=active_lock is not None,
            lock_id=active_lock.id if active_lock else None,
            lock_type=active_lock.lock_type if active_lock else None,
        ))

    # Fire-and-forget view tracking
    await analytics.track_event(
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


@router.get("/me/plan")
async def get_my_plan(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get active plan and subscription info for the user."""
    from app.models.payment import Subscription
    from sqlalchemy import select
    
    service = ProfileService(db)
    profile = await service.get_my_profile(user)
    
    # Check for active subscription
    stmt = (
        select(Subscription)
        .where(Subscription.user_id == user.id, Subscription.status == "active")
        .order_by(Subscription.expires_at.desc())
        .limit(1)
    )
    res = await db.execute(stmt)
    sub = res.scalar_one_or_none()
    
    return {
        "plan": profile.plan,
        "expires_at": sub.expires_at if sub else None,
        "is_trial": False,
    }


@router.patch("/me", response_model=ProfileResponse)
async def update_my_profile(
    data: ProfileUpdate,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Update the authenticated user's profile."""
    service = ProfileService(db)
    profile = await service.update_profile(user, data)
    return profile


@router.delete("/me", status_code=204)
async def delete_my_profile(
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Delete the authenticated user's profile."""
    service = ProfileService(db)
    profile = await service.get_my_profile(user)
    await db.delete(profile)
    await db.flush()


@router.get("", response_model=ExploreResponse)
async def explore_profiles(
    limit: int = Query(default=20, le=50, ge=1),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None, max_length=64),
    db: AsyncSession = Depends(get_db),
    _rate: None = Depends(rate_limit_public),
):
    """Public explore endpoint — discover profiles."""
    discovery = DiscoveryService(db)
    
    if search:
        profiles_list, total = await discovery.search_profiles(search, limit, offset)
    else:
        profiles_list, total = await discovery.get_discovery_feed("trending", None, limit, offset)

    items = []
    for p in profiles_list:
        items.append(ExploreProfileItem(
            slug=p.slug,
            display_name=p.display_name,
            bio=p.bio,
            avatar_url=p.avatar_url,
            plan=p.plan,
            link_count=len(p.links) if hasattr(p, 'links') else 0, # Note: links might not be loaded
            total_views=p.total_views,
        ))

    return ExploreResponse(
        profiles=items,
        total=total,
        has_more=(offset + limit) < total,
    )
