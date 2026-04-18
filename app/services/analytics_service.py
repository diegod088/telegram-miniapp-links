"""Analytics service — event tracking and aggregated stats."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.user import User
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.profile_repository import ProfileRepository

logger = logging.getLogger("app")

PLAN_MAX_DAYS = {
    "free": 7,
    "pro": 90,
    "business": 365,
}


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics_repo = AnalyticsRepository(db)
        self.profile_repo = ProfileRepository(db)

    async def track_event(
        self,
        profile_id: int,
        event_type: str,
        link_id: Optional[int] = None,
        visitor_tg_id: Optional[int] = None,
        referrer: Optional[str] = None,
        client_ip: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> None:
        """Record a click/view event with anti-spam deduplication."""
        ip_hash = None
        if client_ip:
            ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()

        # ── Anti-Spam / Deduplication ────────────────────────────
        from app.core.redis import get_redis
        
        visitor_id = str(visitor_tg_id) if visitor_tg_id else (ip_hash or "unknown")
        dedup_key = f"dedup:{profile_id}:{event_type}:{visitor_id}"
        if link_id:
            dedup_key += f":{link_id}"

        try:
            r = get_redis()
            if r:
                is_new = await r.set(dedup_key, "1", ex=3600, nx=True)
                if not is_new:
                    return
        except Exception as e:
            logger.warning(f"Redis dedup failed: {e}")

        await self.analytics_repo.create(
            profile_id=profile_id,
            link_id=link_id,
            visitor_tg_id=visitor_tg_id,
            event_type=event_type,
            referrer=referrer[:256] if referrer else None,
            ip_hash=ip_hash,
            country_code=country_code,
        )

        # ── Increment Counters in ProfileLink / Profile ──────────
        from sqlalchemy import update
        from app.models.link import ProfileLink
        from app.models.profile import Profile
        
        if event_type == "link_click" and link_id:
            await self.db.execute(
                update(ProfileLink)
                .where(ProfileLink.id == link_id)
                .values(clicks=ProfileLink.clicks + 1)
            )
        elif event_type == "profile_view":
            await self.db.execute(
                update(Profile)
                .where(Profile.id == profile_id)
                .values(total_views=Profile.total_views + 1)
            )
        
        await self.db.flush()

    async def get_stats(self, user: User, period: str = "7d") -> Dict[str, Any]:
        """Get aggregated analytics for the user's profile."""
        profile = await self.profile_repo.get_by_user_id(user.id)
        if not profile:
            raise NotFoundError("Profile not found")

        days = int(period.rstrip("d"))
        max_days = PLAN_MAX_DAYS.get(profile.plan, 7)
        
        if days > max_days:
            raise ForbiddenError(
                f"Your '{profile.plan}' plan allows analytics up to {max_days} days."
            )

        since = datetime.utcnow() - timedelta(days=days)

        total_views = await self.analytics_repo.get_stats(profile.id, since, "profile_view")
        total_clicks = await self.analytics_repo.get_stats(profile.id, since, "link_click")
        unique_visitors = await self.analytics_repo.get_unique_visitors(profile.id, since)
        
        unlock_attempts = await self.analytics_repo.get_stats(profile.id, since, "unlock_attempt")
        unlock_successes = await self.analytics_repo.get_stats(profile.id, since, "unlock_success")

        top_links_raw = await self.analytics_repo.get_top_performing_links(profile.id, since)
        top_links = [{"link_id": lid, "clicks": cnt} for lid, cnt in top_links_raw]

        return {
            "period": period,
            "total_views": total_views,
            "total_clicks": total_clicks,
            "unique_visitors": unique_visitors,
            "unlock_attempts": unlock_attempts,
            "unlock_successes": unlock_successes,
            "top_links": top_links,
        }
