"""Feed router — trending, new, and top links."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, rate_limit_public
from app.schemas.social import FeedResponse, ExploreFeedItem
from app.services.discovery_service import DiscoveryService

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("/trending", response_model=FeedResponse)
async def get_trending_feed(
    category: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, le=50, ge=1),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit_public),
):
    """
    Get links ordered by current trending score.
    Pagination: page-based.
    """
    discovery = DiscoveryService(db)
    rows, next_page, has_more = await discovery.get_links_feed(
        mode="trending",
        category=category,
        query_str=q,
        page=page,
        limit=limit
    )

    items = [ExploreFeedItem.model_validate(row) for row in rows]

    return FeedResponse(
        items=items,
        next_page=next_page if isinstance(next_page, int) else None,
        has_more=has_more
    )


@router.get("/new", response_model=FeedResponse)
async def get_new_feed(
    category: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    cursor: Optional[str] = Query(None),
    limit: int = Query(default=20, le=50, ge=1),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit_public),
):
    """
    Get latest links ordered by creation time.
    Pagination: cursor-based (ISO timestamp).
    """
    discovery = DiscoveryService(db)
    rows, next_cursor, has_more = await discovery.get_links_feed(
        mode="new",
        category=category,
        query_str=q,
        cursor=cursor,
        limit=limit
    )

    items = [ExploreFeedItem.model_validate(row) for row in rows]

    return FeedResponse(
        items=items,
        next_cursor=next_cursor if isinstance(next_cursor, str) else None,
        has_more=has_more
    )


@router.get("/top", response_model=FeedResponse)
async def get_top_feed(
    category: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, le=50, ge=1),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit_public),
):
    """
    Get all-time top links ordered by likes.
    Pagination: page-based.
    """
    discovery = DiscoveryService(db)
    rows, next_page, has_more = await discovery.get_links_feed(
        mode="top",
        category=category,
        query_str=q,
        page=page,
        limit=limit
    )

    items = [ExploreFeedItem.model_validate(row) for row in rows]

    return FeedResponse(
        items=items,
        next_page=next_page if isinstance(next_page, int) else None,
        has_more=has_more
    )
