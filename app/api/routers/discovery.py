"""Discovery router — endpoints for searching and discovering profiles."""

from __future__ import annotations

from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, rate_limit_public
from app.models.user import User
from app.schemas.profile import ExploreProfileItem, ExploreResponse
from app.services.discovery_service import DiscoveryService

router = APIRouter(prefix="/discovery", tags=["discovery"])


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
    
    # Wait, discovery_service.get_discovery_feed currently returns Profile list.
    # Let's check my latest DiscoveryService implementation.
    # It has get_discovery_feed (profile feed) and get_explore_feed (link feed).
    
    profiles, total = await service.get_discovery_feed(feed_type, category, limit, offset)
    
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


@router.get("/categories", response_model=List[str])
async def get_categories():
    """
    Returns the list of available discovery categories.
    """
    return [
        "Educación", "Tecnología", "Entretenimiento", 
        "Finanzas", "Salud", "Arte", "Otros"
    ]


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
