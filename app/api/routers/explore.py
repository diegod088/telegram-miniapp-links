"""Explore router — feed, upvotes, and redirects."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Path, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, rate_limit_auth, rate_limit_public, check_rate_limit
from app.api.auth import get_current_user_optional
from app.core.exceptions import NotFoundError, RateLimitError
from app.core.redis import cache_delete_pattern
from app.models.user import User
from app.schemas.social import ExploreFeedResponse, ExploreFeedItem, SocialActionResponse
from app.services.discovery_service import DiscoveryService
from app.services.social_service import SocialService
from app.services.redirect_service import RedirectService
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/explore", tags=["explore"], redirect_slashes=False)


@router.get("/feed", response_model=ExploreFeedResponse)
async def get_explore_feed(
    category: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    language: Optional[str] = Query(None, max_length=8),
    cursor: Optional[datetime] = Query(None),
    limit: int = Query(default=20, le=50, ge=1),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit_public),
):
    """
    Get the social feed of popular links.
    Ordered by a time-decaying score based on upvotes.
    """
    discovery = DiscoveryService(db)
    rows, next_cursor = await discovery.get_explore_feed(
        category=category,
        query_str=q,
        cursor=cursor,
        language=language,
        limit=limit
    )

    items = [ExploreFeedItem.model_validate(row) for row in rows]

    return ExploreFeedResponse(
        items=items,
        next_cursor=next_cursor.isoformat() if next_cursor else None
    )


@router.post("/links/{link_id}/like", response_model=SocialActionResponse)
async def like_link(
    link_id: int = Path(...),
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    Toggle like for a link.
    Rate limit: 20 per minute per user.
    """
    allowed = await check_rate_limit(f"like:{user.id}", 20, 60)
    if not allowed:
        raise RateLimitError("Máximo 20 likes por minuto.")
        
    service = SocialService(db)
    try:
        new_count, is_liked = await service.toggle_like(user.id, link_id)
        # Fetch current dislikes for response
        link = await service.link_repo.get(link_id)
        # 4. Invalidate social feeds cache
        await cache_delete_pattern("feed:trending:*")
        await cache_delete_pattern("feed:top:*")
        
        return SocialActionResponse(
            likes=new_count, 
            dislikes=link.dislikes,
            is_liked=is_liked
        )
    except ValueError as e:
        raise NotFoundError(str(e))


@router.post("/links/{link_id}/dislike", response_model=SocialActionResponse)
async def dislike_link(
    link_id: int = Path(...),
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    Toggle dislike for a link.
    Rate limit: 20 per minute per user.
    """
    allowed = await check_rate_limit(f"dislike:{user.id}", 20, 60)
    if not allowed:
        raise RateLimitError("Máximo 20 dislikes por minuto.")
        
    service = SocialService(db)
    try:
        new_count, is_disliked = await service.toggle_dislike(user.id, link_id)
        # Fetch current likes for response
        link = await service.link_repo.get(link_id)
        # 4. Invalidate social feeds cache
        await cache_delete_pattern("feed:trending:*")
        await cache_delete_pattern("feed:top:*")
        
        return SocialActionResponse(
            likes=link.likes,
            dislikes=new_count,
            is_disliked=is_disliked
        )
    except ValueError as e:
        raise NotFoundError(str(e))


@router.get("/links/{link_id}/redirect")
async def redirect_link(
    link_id: int = Path(...),
    background_tasks: BackgroundTasks = None,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Record a view and return the affiliate/monetized URL.
    """
    redirect_service = RedirectService(db)
    analytics = AnalyticsService(db)
    
    # 1. Prepare redirect info
    info = await redirect_service.get_redirect_info(
        link_id=link_id,
        viewer_user_id=user.id if user else None
    )

    # 2. Track event in background
    if background_tasks:
        background_tasks.add_task(
            analytics.track_event,
            profile_id=info["profile_id"],
            event_type="link_click",
            link_id=info["link_id"],
            visitor_tg_id=user.telegram_id if user else None
        )
    else:
        await analytics.track_event(
            profile_id=info["profile_id"],
            event_type="link_click",
            link_id=info["link_id"],
            visitor_tg_id=user.telegram_id if user else None
        )

    return {
        "affiliate_url": info["url"],
        "title": info["title"],
        "is_monetized": info["is_monetized"],
    }


@router.post("/links/{link_id}/report", status_code=202)
async def report_link(
    link_id: int = Path(...),
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Report a link as spam/inappropriate. Rate limit: 5/hour."""
    allowed = await check_rate_limit(f"report:{user.id}", 5, 3600)
    if not allowed:
        raise RateLimitError("Máximo 5 reportes por hora.")
    
    from app.repositories.link_repository import LinkRepository
    repo = LinkRepository(db)
    link = await repo.get(link_id)
    if not link:
        raise NotFoundError("Link not found")
    
    link.report_count += 1
    # Auto-hide if report_count exceeds threshold
    if link.report_count >= 10:
        link.is_active = False
    
    await db.flush()
    # Invalidate caches as the item might have been hidden
    await cache_delete_pattern("feed:trending:*")
    await cache_delete_pattern("feed:top:*")
    
    return {"status": "reported", "link_id": link_id}
