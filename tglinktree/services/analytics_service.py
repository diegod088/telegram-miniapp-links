"""Analytics service — event tracking and aggregated stats."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tglinktree.core.exceptions import ForbiddenError
from tglinktree.models.analytics import ClickEvent
from tglinktree.models.profile import Profile
from tglinktree.models.user import User


# ── Plan-based analytics period limits ────────────────────────
PLAN_MAX_DAYS = {
    "free": 7,
    "pro": 90,
    "business": 365,
}


async def track_event(
    db: AsyncSession,
    profile_id: int,
    event_type: str,
    link_id: Optional[int] = None,
    visitor_tg_id: Optional[int] = None,
    referrer: Optional[str] = None,
    client_ip: Optional[str] = None,
    country_code: Optional[str] = None,
) -> None:
    """
    Record a click/view event. Includes anti-spam deduplication via Redis.
    """
    ip_hash = None
    if client_ip:
        ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()

    # ── Anti-Spam / Deduplication ────────────────────────────
    from tglinktree.core.redis import get_redis
    
    # Identify the visitor by TG ID or Hash of IP
    visitor_id = str(visitor_tg_id) if visitor_tg_id else (ip_hash or "unknown")
    dedup_key = f"dedup:{profile_id}:{event_type}:{visitor_id}"
    if link_id:
        dedup_key += f":{link_id}"

    try:
        r = get_redis()
        # SET with NX (not exists) and EX (expire in 1 hour)
        is_new = await r.set(dedup_key, "1", ex=3600, nx=True)
        if not is_new:
            return  # Skip DB write for duplicate events within the hour
    except Exception as e:
        # Don't break tracking if Redis is down, but log it
        import logging
        logging.getLogger("tglinktree").warning(f"Redis dedup failed: {e}")

    event = ClickEvent(
        profile_id=profile_id,
        link_id=link_id,
        visitor_tg_id=visitor_tg_id,
        event_type=event_type,
        referrer=referrer[:256] if referrer else None,
        ip_hash=ip_hash,
        country_code=country_code,
    )
    db.add(event)
    await db.flush()


async def get_analytics(
    db: AsyncSession,
    user: User,
    period: str = "7d",
) -> dict:
    """
    Get aggregated analytics for the user's profile.

    Period format: '7d', '30d', '90d', '365d'
    Enforces plan limits on how far back data goes.
    """
    # Get user profile
    result = await db.execute(
        select(Profile).where(Profile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        return {"error": "No profile found"}

    # Parse period
    days = int(period.rstrip("d"))
    max_days = PLAN_MAX_DAYS.get(profile.plan, 7)
    if days > max_days:
        raise ForbiddenError(
            f"Your '{profile.plan}' plan allows analytics up to {max_days} days. "
            f"Upgrade to access longer periods."
        )

    since = datetime.utcnow() - timedelta(days=days)

    # Total profile views
    views_result = await db.execute(
        select(func.count(ClickEvent.id)).where(
            ClickEvent.profile_id == profile.id,
            ClickEvent.event_type == "profile_view",
            ClickEvent.created_at >= since,
        )
    )
    total_views = views_result.scalar() or 0

    # Total link clicks
    clicks_result = await db.execute(
        select(func.count(ClickEvent.id)).where(
            ClickEvent.profile_id == profile.id,
            ClickEvent.event_type == "link_click",
            ClickEvent.created_at >= since,
        )
    )
    total_clicks = clicks_result.scalar() or 0

    # Unique visitors (by ip_hash)
    unique_result = await db.execute(
        select(func.count(func.distinct(ClickEvent.ip_hash))).where(
            ClickEvent.profile_id == profile.id,
            ClickEvent.created_at >= since,
            ClickEvent.ip_hash.isnot(None),
        )
    )
    unique_visitors = unique_result.scalar() or 0

    # Unlock attempts vs successes
    unlock_attempts = await db.execute(
        select(func.count(ClickEvent.id)).where(
            ClickEvent.profile_id == profile.id,
            ClickEvent.event_type == "unlock_attempt",
            ClickEvent.created_at >= since,
        )
    )
    unlock_successes = await db.execute(
        select(func.count(ClickEvent.id)).where(
            ClickEvent.profile_id == profile.id,
            ClickEvent.event_type == "unlock_success",
            ClickEvent.created_at >= since,
        )
    )

    # Top links by clicks
    top_links_result = await db.execute(
        select(
            ClickEvent.link_id,
            func.count(ClickEvent.id).label("clicks"),
        )
        .where(
            ClickEvent.profile_id == profile.id,
            ClickEvent.event_type == "link_click",
            ClickEvent.link_id.isnot(None),
            ClickEvent.created_at >= since,
        )
        .group_by(ClickEvent.link_id)
        .order_by(func.count(ClickEvent.id).desc())
        .limit(10)
    )

    top_links = [
        {"link_id": row.link_id, "clicks": row.clicks}
        for row in top_links_result
    ]

    return {
        "period": period,
        "total_views": total_views,
        "total_clicks": total_clicks,
        "unique_visitors": unique_visitors,
        "unlock_attempts": unlock_attempts.scalar() or 0,
        "unlock_successes": unlock_successes.scalar() or 0,
        "top_links": top_links,
    }
