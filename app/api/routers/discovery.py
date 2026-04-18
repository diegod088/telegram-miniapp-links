"""Discovery router — endpoints for searching and discovering profiles."""

from __future__ import annotations

from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, rate_limit_public, rate_limit_auth
from app.models.user import User
from app.schemas.profile import ExploreProfileItem, ExploreResponse
from app.schemas.social import ActivityResponse
from app.services.discovery_service import DiscoveryService
from app.services.activity_service import ActivityService
from app.core.constants import LINK_CATEGORIES

router = APIRouter(prefix="/discovery", tags=["discovery"], redirect_slashes=False)


@router.get("/search", response_model=ExploreResponse)
async def search_profiles(
    q: str = Query(..., min_length=2, max_length=64),
    limit: int = Query(default=20, le=50, ge=1),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _rate: None = Depends(rate_limit_public),
):
    """
    Search profiles by name, bio, or link content.
    """
    service = DiscoveryService(db)
    profiles, total = await service.search_profiles(q, limit, offset)
    
    items = [
        ExploreProfileItem(
            slug=p.slug,
            display_name=p.display_name,
            bio=p.bio,
            avatar_url=p.avatar_url,
            plan=p.plan,
            link_count=len(p.links) if hasattr(p, 'links') else 0,
            total_views=p.total_views
        )
        for p in profiles
    ]

    return ExploreResponse(
        profiles=items,
        total=total,
        has_more=(offset + limit) < total
    )


@router.get("/feed/{feed_type}", response_model=ExploreResponse)
async def get_discovery_feed(
    feed_type: str = Path(..., pattern="^(trending|top|new)$"),
    category: Optional[str] = Query(None),
    language: Optional[str] = Query(None, max_length=8),
    limit: int = Query(default=20, le=50, ge=1),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _rate: None = Depends(rate_limit_public),
):
    """
    Get a curated list of profiles based on ranking algorithm.
    """
    service = DiscoveryService(db)
    # Reusing the unified feed generator if possible, but the schemas differ slightly
    # discovery_service has get_discovery_feed returning (Profile, total)
    # whereas explore feed returns (Link, Profile, User)
    
    profiles, total = await service.get_discovery_feed(
        feed_type=feed_type, 
        category=category, 
        language=language,
        limit=limit, 
        offset=offset
    )
    
    items = [
        ExploreProfileItem(
            slug=p.slug,
            display_name=p.display_name,
            bio=p.bio,
            avatar_url=p.avatar_url,
            plan=p.plan,
            link_count=0, 
            total_views=p.total_views
        )
        for p in profiles
    ]

    return ExploreResponse(
        profiles=items,
        total=total,
        has_more=(offset + limit) < total
    )


@router.get("/ranking", response_model=ExploreResponse)
async def get_profile_ranking(
    sort_by: str = Query(default="likes", pattern="^(likes|views)$"),
    category: Optional[str] = Query(None),
    limit: int = Query(default=20, le=50, ge=1),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _rate: None = Depends(rate_limit_public),
):
    """
    Ranking / leaderboard of public profiles sorted by total likes
    or total views, with optional category filter.
    """
    service = DiscoveryService(db)
    rows, total = await service.get_profile_ranking(sort_by, category, limit, offset)

    items = [
        ExploreProfileItem(
            slug=profile.slug,
            display_name=profile.display_name,
            bio=profile.bio,
            avatar_url=profile.avatar_url,
            plan=profile.plan,
            link_count=len(profile.links) if hasattr(profile, "links") else 0,
            total_views=profile.total_views,
            total_likes=int(total_likes),
            category=profile.category,
        )
        for profile, total_likes in rows
    ]

    return ExploreResponse(
        profiles=items,
        total=total,
        has_more=(offset + limit) < total,
    )


@router.get("/languages")
async def get_available_languages(db: AsyncSession = Depends(get_db)):
    """
    Returns available languages and their profile counts.
    """
    from sqlalchemy import select, func, desc
    from app.models.profile import Profile
    
    stmt = (select(Profile.language, func.count(Profile.id).label("count"))
            .where(Profile.is_public == True, Profile.language.isnot(None))
            .group_by(Profile.language)
            .order_by(desc("count")))
    result = await db.execute(stmt)
    return [{"language": r.language, "count": r.count} for r in result.all()]


@router.get("/categories", response_model=List[str])
async def get_categories():
    """
    Returns the list of available discovery categories.
    """
    return LINK_CATEGORIES


@router.post("/refresh-trending", status_code=202)
async def trigger_trending_refresh(
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    Force a recalculation of trending scores.
    """
    service = DiscoveryService(db)
    count = await service.refresh_trending_scores()
    return {"status": "accepted", "updated_profiles": count}


@router.get("/featured", response_model=List[ExploreProfileItem])
async def get_featured_carousel(
    db: AsyncSession = Depends(get_db),
    _rate: None = Depends(rate_limit_public),
):
    """
    Get highlighted VIP and Pro profiles for the home carousel.
    """
    service = DiscoveryService(db)
    profiles = await service.get_featured_profiles(limit=10)
    
    return [
        ExploreProfileItem(
            slug=p.slug,
            display_name=p.display_name,
            bio=p.bio,
            avatar_url=p.avatar_url,
            plan=p.plan,
            link_count=len(p.links) if hasattr(p, 'links') else 0,
            total_views=p.total_views
        )
        for p in profiles
    ]


@router.get("/pulse", response_model=List[ActivityResponse])
async def get_pulse_feed(
    db: AsyncSession = Depends(get_db),
    _rate: None = Depends(rate_limit_public),
):
    """
    Get the live activity feed (Pulse).
    """
    service = ActivityService(db)
    activities = await service.get_pulse_feed(limit=30)
    
    return [
        ActivityResponse(
            id=a.id,
            user_id=a.user_id,
            type=a.type,
            message=a.message,
            target_id=a.target_id,
            target_type=a.target_type,
            created_at=a.created_at,
            username=a.user.username if a.user else None,
            first_name=a.user.first_name if a.user else None
        )
        for a in activities
    ]
