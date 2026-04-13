"""Discovery service — search, trending algorithm, and feed generation."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple

from sqlalchemy import func, select, desc, or_, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tglinktree.models.profile import Profile
from tglinktree.models.link import ProfileLink
from tglinktree.models.analytics import ClickEvent
from tglinktree.core.redis import cache_get, cache_set

logger = logging.getLogger("tglinktree")

# ── Discovery Configuration ──────────────────────────────────
TRENDING_CACHE_TTL = 1800  # 30 minutes
SEARCH_LIMIT_DEFAULT = 20


async def search_profiles(
    db: AsyncSession,
    query: str,
    limit: int = SEARCH_LIMIT_DEFAULT,
    offset: int = 0
) -> Tuple[List[Profile], int]:
    """
    Search profiles using PostgreSQL Full-Text Search.
    Ranks by relevance (ts_rank) with a boost for featured/boosted profiles.
    """
    if not query:
        return [], 0

    # PostgreSQL websearch_to_tsquery is perfect for raw user input
    # We use 'spanish' as the default dictionary given the context
    ts_query = func.websearch_to_tsquery('spanish', query)
    
    # Ranking formula: Relevancia text + Boost de Monetización + Pequeño peso de vistas totales
    rank_expr = func.ts_rank(Profile.search_vector, ts_query)
    
    # Apply boost if boosted (simple multiplier)
    boost_expr = func.case(
        (and_(Profile.boost_until.isnot(None), Profile.boost_until > datetime.utcnow()), 1.5),
        else_=1.0
    )
    
    final_rank = rank_expr * boost_expr

    # Execute search
    search_q = (
        select(Profile)
        .where(Profile.is_public == True)
        .where(Profile.search_vector.op('@@')(ts_query))
        .order_by(desc(final_rank))
        .limit(limit)
        .offset(offset)
    )

    count_q = (
        select(func.count(Profile.id))
        .where(Profile.is_public == True)
        .where(Profile.search_vector.op('@@')(ts_query))
    )

    results = await db.execute(search_q)
    total = await db.execute(count_q)
    
    return list(results.scalars().all()), total.scalar() or 0


async def get_discovery_feed(
    db: AsyncSession,
    feed_type: str = "trending",
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> Tuple[List[Profile], int]:
    """
    Unified entry point for discovery feeds.
    Types: 'trending', 'top', 'new'.
    """
    base_q = select(Profile).where(Profile.is_public == True)
    
    if category:
        base_q = base_q.where(Profile.category == category)

    if feed_type == "new":
        query = base_q.order_by(desc(Profile.created_at))
    elif feed_type == "top":
        query = base_q.order_by(desc(Profile.total_views))
    elif feed_type == "trending":
        # Trending uses the calculated trending_score
        query = base_q.order_by(desc(Profile.trending_score), desc(Profile.created_at))
    else:
        query = base_q.order_by(desc(Profile.created_at))

    # Support Featured Profiles injection
    # In a real production system, we'd interleaved featured profiles into the results
    # For now, we'll just prioritize is_featured=True in the sorting
    query = query.order_by(desc(Profile.is_featured), desc(Profile.trending_score))

    # Count total
    count_q = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    results = await db.execute(query.limit(limit).offset(offset))
    return list(results.scalars().all()), total


async def refresh_trending_scores(db: AsyncSession) -> int:
    """
    Recalculate trending_score for all active profiles.
    Score = (Points / (AgeHours + 2)^1.5) * Boost
    Points = clicks*1 + views*0.2 + unlocks*5 (last 24h)
    """
    since_24h = datetime.utcnow() - timedelta(hours=24)
    
    # Subquery for points in last 24h
    points_sq = (
        select(
            ClickEvent.profile_id,
            func.sum(
                func.case(
                    (ClickEvent.event_type == 'link_click', 1.0),
                    (ClickEvent.event_type == 'profile_view', 0.2),
                    (ClickEvent.event_type == 'unlock_success', 5.0),
                    else_=0.0
                )
            ).label("points")
        )
        .where(ClickEvent.created_at >= since_24h)
        .group_by(ClickEvent.profile_id)
        .subquery()
    )

    # Fetch profiles to update
    # We only update public profiles
    stmt = select(Profile, func.coalesce(points_sq.c.points, 0).label("recent_points")).outerjoin(
        points_sq, Profile.id == points_sq.c.profile_id
    ).where(Profile.is_public == True)
    
    results = await db.execute(stmt)
    now = datetime.utcnow()
    updated_count = 0

    for profile, points in results.all():
        # Gravity Formula
        age_hours = (now - profile.created_at).total_seconds() / 3600
        score = float(points) / (age_hours + 2)**1.5
        
        # Apply Monetization Boost (1.5x)
        if profile.boost_until and profile.boost_until > now:
            score *= 1.5
            
        profile.trending_score = score
        updated_count += 1

    await db.commit()
    return updated_count


async def update_search_vector(db: AsyncSession, profile_id: int) -> None:
    """
    Manually update the search_vector for a profile.
    Aggregates: display_name, bio, and all link titles.
    """
    # Fetch profile with links
    stmt = select(Profile).where(Profile.id == profile_id).options(selectinload(Profile.links))
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if not profile:
        return

    # Combine text
    link_titles = " ".join([l.title for l in profile.links if l.is_active])
    full_text = f"{profile.display_name} {profile.bio or ''} {link_titles}"
    
    # Update via raw SQL to use PostgreSQL to_tsvector correctly
    await db.execute(
        text("UPDATE profiles SET search_vector = to_tsvector('spanish', :text) WHERE id = :id"),
        {"text": full_text, "id": profile_id}
    )
    await db.commit()
