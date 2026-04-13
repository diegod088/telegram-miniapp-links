"""Discovery router — endpoints for searching and discovering profiles."""

from __future__ import annotations

from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from tglinktree.api.deps import get_db, rate_limit_public
from tglinktree.schemas.profile import ExploreProfileItem, ExploreResponse
from tglinktree.services import discovery_service

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
    profiles, total = await discovery_service.search_profiles(db, q, limit, offset)
    
    # Map to schema (reusing ExploreProfileItem)
    items = []
    for p in profiles:
        # We need to count links for the response (service could include this)
        # For efficiency, we'll assume the service could be optimized, 
        # but for now we'll just map the base fields.
        items.append(ExploreProfileItem(
            slug=p.slug,
            display_name=p.display_name,
            bio=p.bio,
            avatar_url=p.avatar_url,
            plan=p.plan,
            link_count=len(p.links) if hasattr(p, 'links') else 0,
            total_views=p.total_views
        ))

    return ExploreResponse(
        profiles=items,
        total=total,
        has_more=(offset + limit) < total
    )


@router.get("/feed/{feed_type}", response_model=ExploreResponse)
async def get_discovery_feed(
    feed_type: str = Path(..., regex="^(trending|top|new)$"),
    category: Optional[str] = Query(None),
    limit: int = Query(default=20, le=50, ge=1),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _rate: None = Depends(rate_limit_public),
):
    """
    Get a curated list of profiles based on ranking algorithm.
    Types: trending, top (most viewed), new (recently created).
    """
    profiles, total = await discovery_service.get_discovery_feed(
        db, feed_type, category, limit, offset
    )
    
    items = [
        ExploreProfileItem(
            slug=p.slug,
            display_name=p.display_name,
            bio=p.bio,
            avatar_url=p.avatar_url,
            plan=p.plan,
            link_count=0, # Simplified for speed
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
    db: AsyncSession = Depends(get_db),
):
    """
    Force a recalculation of trending scores.
    In production, this would be a background task.
    """
    count = await discovery_service.refresh_trending_scores(db)
    return {"status": "accepted", "updated_profiles": count}
