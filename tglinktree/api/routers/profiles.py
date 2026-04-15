"""Profile endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tglinktree.api.deps import get_db, rate_limit_auth, rate_limit_public
from tglinktree.api.auth import get_current_user, get_current_user_optional
from tglinktree.models.link import ProfileLink
from tglinktree.models.lock import ContentLock
from tglinktree.models.user import User
from tglinktree.schemas.profile import (
    ExploreProfileItem,
    ExploreResponse,
    ProfileCreate,
    ProfilePublicResponse,
    ProfileResponse,
    ProfileUpdate,
    LinkInProfile,
)
from tglinktree.services import profile_service, discovery_service
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
    user: Optional[User] = Depends(get_current_user_optional),
    _rate: None = Depends(rate_limit_public),
):
    """Get a public profile by slug. No auth required."""
    # 1. Determine viewer plan
    viewer_plan = "free"
    if user:
        # Check for active subscription or profile plan
        # We can fetch the user's profile to see their plan
        stmt = select(Profile.plan).where(Profile.user_id == user.id)
        res = await db.execute(stmt)
        viewer_plan = res.scalar_one_or_none() or "free"

    # 2. Get profile with filtered links (Discovery Service helper)
    profile = await discovery_service.get_profile_with_filtered_links(db, slug, viewer_plan)

    # Build response with lock status per link
    links = []
    for link in profile.filtered_links:
        if not link.is_active:
            continue

        # Determine lock info from eagerly-loaded locks
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
    await track_event(
        db=db,
        profile_id=profile.id,
        event_type="profile_view",
    )
    
    # Also increment the cached/aggregated counter in the profile table
    profile.total_views += 1
    await db.flush()

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
    from tglinktree.models.payment import Subscription
    
    profile = await profile_service.get_profile_by_user(db, user)
    
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
        "is_trial": False, # Future use
    }


@router.patch("/me", response_model=ProfileResponse)
async def update_my_profile(
    data: ProfileUpdate,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Update the authenticated user's profile."""
    profile = await profile_service.update_profile(db, user, data)
    return profile


@router.delete("/me", status_code=204)
async def delete_my_profile(
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Delete the authenticated user's profile."""
    profile = await profile_service.get_profile_by_user(db, user)
    await db.delete(profile)
    await db.flush()


# ── Explore endpoint ──────────────────────────────────────────

from tglinktree.models.profile import Profile


@router.get("", response_model=None)
async def explore_profiles(
    limit: int = Query(default=20, le=50, ge=1),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None, max_length=64),
    db: AsyncSession = Depends(get_db),
    _rate: None = Depends(rate_limit_public),
):
    """Public explore endpoint — discover profiles."""
    # Subquery: count active links per profile
    link_count_sq = (
        select(
            ProfileLink.profile_id,
            func.count(ProfileLink.id).label("link_count"),
        )
        .where(ProfileLink.is_active == True)
        .group_by(ProfileLink.profile_id)
        .subquery()
    )

    base_q = (
        select(Profile, link_count_sq.c.link_count)
        .outerjoin(link_count_sq, Profile.id == link_count_sq.c.profile_id)
        .where(Profile.is_public == True)
        .where(link_count_sq.c.link_count > 0)  # Exclude empty profiles
    )

    if search:
        search_term = f"%{search.lower()}%"
        base_q = base_q.where(
            (func.lower(Profile.display_name).like(search_term))
            | (func.lower(Profile.slug).like(search_term))
        )

    # Count total
    count_q = select(func.count()).select_from(base_q.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    # Fetch page, ordered by trending (views desc)
    results = await db.execute(
        base_q
        .order_by(Profile.total_views.desc(), Profile.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    profiles = []
    for row in results.all():
        profile = row[0]
        lc = row[1] or 0
        profiles.append(ExploreProfileItem(
            slug=profile.slug,
            display_name=profile.display_name,
            bio=profile.bio,
            avatar_url=profile.avatar_url,
            plan=profile.plan,
            link_count=lc,
            total_views=profile.total_views,
        ))

    return ExploreResponse(
        profiles=profiles,
        total=total,
        has_more=(offset + limit) < total,
    )
