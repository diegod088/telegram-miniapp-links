"""Explore router — feed, upvotes, and redirects."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Path, BackgroundTasks
from sqlalchemy import select, desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tglinktree.api.deps import get_db, get_current_user, check_rate_limit
from tglinktree.api.auth import get_current_user_optional
from tglinktree.core.exceptions import NotFoundError, RateLimitError
from tglinktree.models.link import ProfileLink
from tglinktree.models.profile import Profile
from tglinktree.models.user import User
from tglinktree.schemas.social import ExploreFeedResponse, ExploreFeedItem, UpvoteResponse
from tglinktree.services import social_service, affiliate

router = APIRouter(prefix="/explore", tags=["explore"])

@router.get("/feed", response_model=ExploreFeedResponse)
async def get_explore_feed(
    category: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    cursor: Optional[datetime] = Query(None),
    limit: int = Query(default=20, le=50, ge=1),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the social feed of popular links.
    Ordered by a time-decaying score based on upvotes.
    """
    score_expr = social_service.get_explore_score_expr()
    
    # Base query
    stmt = (
        select(ProfileLink, Profile, User)
        .join(Profile, ProfileLink.profile_id == Profile.id)
        .join(User, Profile.user_id == User.id)
        .where(ProfileLink.is_active == True)
        .where(Profile.is_public == True)
    )
    
    # Filter by category
    if category and category != "ALL":
        stmt = stmt.where(ProfileLink.category == category)

    # Filter by Search Query
    if q and len(q) >= 2:
        search_filter = or_(
            ProfileLink.title.ilike(f"%{q}%"),
            ProfileLink.description.ilike(f"%{q}%"),
            Profile.display_name.ilike(f"%{q}%"),
            Profile.slug.ilike(f"%{q}%")
        )
        stmt = stmt.where(search_filter)
        
    # Cursor pagination (items older than cursor)
    if cursor:
        stmt = stmt.where(ProfileLink.created_at < cursor)
        
    # Order by Score DESC, then CreatedAt DESC
    stmt = stmt.order_by(desc(score_expr), desc(ProfileLink.created_at))
    
    # Limit + 1 to check if there's more
    stmt = stmt.limit(limit + 1)
    
    result = await db.execute(stmt)
    rows = result.all()
    
    items = []
    for link, profile, user in rows[:limit]:
        item = ExploreFeedItem.model_validate(link)
        item.username = user.username
        item.first_name = user.first_name
        items.append(item)
        
    next_cursor = None
    if len(rows) > limit:
        next_cursor = rows[limit-1][0].created_at.isoformat()
        
    return ExploreFeedResponse(items=items, next_cursor=next_cursor)

@router.post("/links/{link_id}/upvote", response_model=UpvoteResponse)
async def upvote_link(
    link_id: int = Path(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Toggle upvote for a link.
    Rate limit: 10 per minute per user.
    """
    # 1. Rate Limiting via Redis
    allowed = await check_rate_limit(f"upvote:{user.id}", 10, 60)
    if not allowed:
        raise RateLimitError("Máximo 10 votos por minuto.")
        
    # 2. Toggle Vote
    try:
        new_count, is_upvoted = await social_service.toggle_upvote(db, user.id, link_id)
        return UpvoteResponse(upvotes=new_count, is_upvoted=is_upvoted)
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
    Record a view and return the affiliate URL.
    Free users get a Linkvertise-monetized URL.
    Pro/Business (VIP) users get the direct affiliate URL.
    """
    stmt = select(ProfileLink).where(ProfileLink.id == link_id)
    result = await db.execute(stmt)
    link = result.scalar_one_or_none()
    
    if not link:
        raise NotFoundError("Link no encontrado")
        
    # 1. Increment views (background task to not block)
    async def increment_views(l_id: int):
        from tglinktree.core.database import async_session_factory
        async with async_session_factory() as session:
            await session.execute(
                ProfileLink.__table__.update()
                .where(ProfileLink.id == l_id)
                .values(views=ProfileLink.views + 1)
            )
            await session.commit()
            
    if background_tasks:
        background_tasks.add_task(increment_views, link.id)
    else:
        link.views += 1
        await db.flush()

    # 2. Get affiliate URL
    from tglinktree.services import affiliate
    target_url = link.canonical_url or link.url
    affiliate_url = affiliate.get_affiliate_url(target_url)

    # 3. Determine viewer plan — wrap with Linkvertise for free users
    viewer_plan = "free"
    if user:
        plan_stmt = select(Profile.plan).where(Profile.user_id == user.id)
        plan_result = await db.execute(plan_stmt)
        viewer_plan = plan_result.scalar_one_or_none() or "free"

    final_url = affiliate_url
    if viewer_plan == "free":
        from tglinktree.services.linkvertise import create_linkvertise_url
        final_url = create_linkvertise_url(affiliate_url)

    return {
        "affiliate_url": final_url,
        "title": link.title,
        "is_monetized": viewer_plan == "free",
    }
