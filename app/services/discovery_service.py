"""Discovery service — search, trending algorithm, and feed generation."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple

from sqlalchemy import func, select, desc, or_, and_, text, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profile import Profile
from app.models.link import ProfileLink
from app.models.user import User
from app.models.analytics import ClickEvent
from app.core.redis import cache_get, cache_set
import json
from app.repositories.profile_repository import ProfileRepository
from app.core.exceptions import NotFoundError

logger = logging.getLogger("app")


class DiscoveryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repo = ProfileRepository(db)

    async def search_profiles(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Profile], int]:
        """Search profiles using Full-Text Search or LIKE fallback."""
        if not query:
            return [], 0

        dialect_name = self.db.bind.dialect.name.lower()
        is_sqlite = "sqlite" in dialect_name

        if is_sqlite:
            search_q = (
                select(Profile)
                .where(Profile.is_public == True)
                .where(or_(
                    Profile.display_name.ilike(f"%{query}%"),
                    Profile.slug.ilike(f"%{query}%"),
                    Profile.bio.ilike(f"%{query}%"),
                    Profile.search_vector.ilike(f"%{query}%")
                ))
                .limit(limit)
                .offset(offset)
            )
            count_q = (
                select(func.count(Profile.id))
                .where(Profile.is_public == True)
                .where(or_(
                    Profile.display_name.ilike(f"%{query}%"),
                    Profile.slug.ilike(f"%{query}%"),
                    Profile.bio.ilike(f"%{query}%"),
                    Profile.search_vector.ilike(f"%{query}%")
                ))
            )
        else:
            ts_query = func.websearch_to_tsquery('spanish', query)
            rank_expr = func.ts_rank(Profile.search_vector, ts_query)
            boost_expr = func.case(
                (and_(Profile.boost_until.isnot(None), Profile.boost_until > datetime.utcnow()), 1.5),
                else_=1.0
            )
            final_rank = rank_expr * boost_expr

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

        results = await self.db.execute(search_q)
        total = await self.db.execute(count_q)
        
        return list(results.scalars().all()), total.scalar() or 0

    async def get_links_feed(
        self,
        mode: str = "trending",
        category: Optional[str] = None,
        query_str: Optional[str] = None,
        cursor: Optional[Any] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Dict[str, Any]], Optional[Any], bool]:
        """
        Get a generalized feed of links with Redis caching.
        Modes: 'trending', 'new', 'top'.
        Returns (items, next_cursor_or_page, has_more)
        """
        # 0. Check Cache
        cache_key = f"feed:{mode}:{category or 'all'}:{query_str or ''}:{cursor or ''}:{page}:{limit}"
        cached = await cache_get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                return data["items"], data["next_val"], data["has_more"]
            except Exception as e:
                logger.warning(f"Cache parse error for {cache_key}: {e}")

        # 1. Base query
        stmt = (
            select(ProfileLink, Profile, User)
            .join(Profile, ProfileLink.profile_id == Profile.id)
            .join(User, Profile.user_id == User.id)
            .where(ProfileLink.is_active == True)
            .where(Profile.is_public == True)
        )

        # 2. Score expression (for trending/monetization)
        hours_passed = (func.extract('epoch', func.now() - ProfileLink.created_at) / 3600)
        freshness_boost = 100 / (1 + (hours_passed / 6))
        
        # Base engagement score
        base_score = (ProfileLink.clicks * 0.4) + (ProfileLink.likes * 0.6) - (ProfileLink.dislikes * 0.5) + freshness_boost
        
        # Apply multipliers (VIP boost)
        score_expr = base_score * Profile.boost_score
        
        # Temporal Link Boost (2x)
        score_expr = case(
            (and_(ProfileLink.boosted_until.is_not(None), ProfileLink.boosted_until > func.now()), score_expr * 2.0),
            else_=score_expr
        )
        
        # Featured Link Boost (1.5x)
        score_expr = case(
            (ProfileLink.is_featured == True, score_expr * 1.5),
            else_=score_expr
        )
        
        # Sponsored Link Bonus (+1,000,000) - Puts them on top effectively
        score_expr = case(
            (ProfileLink.is_sponsored == True, score_expr + 1000000),
            else_=score_expr
        )

        # 3. Filters
        if category and category != "ALL":
            stmt = stmt.where(ProfileLink.category == category)
        if query_str and len(query_str) >= 2:
            stmt = stmt.where(or_(
                ProfileLink.title.ilike(f"%{query_str}%"),
                Profile.display_name.ilike(f"%{query_str}%")
            ))

        # 4. Sorting & Pagination
        if mode == "new":
            if cursor:
                cursor_dt = datetime.fromisoformat(cursor) if isinstance(cursor, str) else cursor
                stmt = stmt.where(ProfileLink.created_at < cursor_dt)
            stmt = stmt.order_by(desc(ProfileLink.created_at))
            stmt = stmt.limit(limit + 1)
        
        elif mode == "top":
            # Simple cursor for top: page-based is easier but likes + created_at works
            # Using page-based for simplicity across all modes unless specified otherwise
            # but user asked for infinite scroll optimization. 
            # We'll use OFFSET for simplicity in 'top' and 'trending' for now.
            stmt = stmt.order_by(desc(ProfileLink.likes), desc(ProfileLink.created_at))
            stmt = stmt.limit(limit + 1).offset((page - 1) * limit)

        else: # trending
            stmt = stmt.order_by(desc(score_expr), desc(ProfileLink.created_at))
            stmt = stmt.limit(limit + 1).offset((page - 1) * limit)

        # 5. Execute
        result = await self.db.execute(stmt)
        rows = result.all()

        has_more = len(rows) > limit
        items_objs = rows[:limit]
        
        # 6. Transform to dicts for caching/consistency
        # We use a structure compatible with ExploreFeedItem schema
        items = []
        for link, profile, user in items_objs:
            items.append({
                "id": link.id,
                "title": link.title,
                "url": link.url,
                "canonical_url": link.canonical_url,
                "category": link.category,
                "likes": link.likes,
                "dislikes": link.dislikes,
                "clicks": link.clicks,
                "created_at": link.created_at.isoformat(),
                "is_sponsored": link.is_sponsored,
                "is_verified": link.is_verified,
                "is_featured": link.is_featured,
                "username": user.username,
                "first_name": user.first_name,
            })

        next_val = None
        if has_more:
            if mode == "new":
                next_val = items_objs[-1][0].created_at.isoformat()
            else:
                next_val = page + 1

        # 7. Set Cache
        ttls = {"trending": 120, "top": 300, "new": 60}
        ttl = ttls.get(mode, 120)
        
        await cache_set(
            cache_key, 
            json.dumps({"items": items, "next_val": next_val, "has_more": has_more}),
            ttl=ttl
        )

        return items, next_val, has_more

    async def get_explore_feed(
        self,
        category: Optional[str] = None,
        query_str: Optional[str] = None,
        cursor: Optional[datetime] = None,
        limit: int = 20
    ) -> Tuple[List[Tuple[ProfileLink, Profile, User]], Optional[datetime]]:
        """Deprecated: use get_links_feed. Kept for backward compatibility."""
        items, next_cursor, _ = await self.get_links_feed(
            mode="trending",
            category=category,
            query_str=query_str,
            cursor=cursor,
            limit=limit
        )
        return items, next_cursor

    async def get_filtered_profile(
        self,
        slug: str,
        viewer_plan: str = "free"
    ) -> Profile:
        """Get a profile by slug and filter its links based on the viewer's plan."""
        profile = await self.profile_repo.get_by_slug(slug, include_links=True)
        if not profile:
            raise NotFoundError(f"Profile '{slug}' not found.")

        all_links = list(profile.links)
        if viewer_plan == "free":
            filtered_links = [link for link in all_links if not link.is_premium]
        else:
            filtered_links = all_links

        filtered_links.sort(key=lambda x: (x.boosted_until or datetime.min), reverse=True)
        profile.filtered_links = filtered_links
        return profile

    async def update_search_vector(self, profile_id: int) -> None:
        """Update the search_vector for a profile."""
        profile = await self.profile_repo.get(profile_id)
        if not profile:
            return

        link_titles = " ".join([l.title for l in profile.links if l.title and l.is_active])
        full_text = f"{profile.display_name} {profile.bio or ''} {link_titles}"
        
        dialect_name = self.db.bind.dialect.name.lower()
        is_sqlite = "sqlite" in dialect_name
        
        try:
            if is_sqlite:
                await self.db.execute(
                    text("UPDATE profiles SET search_vector = :text WHERE id = :id"),
                    {"text": full_text, "id": profile_id}
                )
            else:
                await self.db.execute(
                    text("UPDATE profiles SET search_vector = to_tsvector('spanish', :text) WHERE id = :id"),
                    {"text": full_text, "id": profile_id}
                )
            await self.db.commit()
        except Exception as e:
            logger.warning(f"Failed to update search index for profile {profile_id}: {e}")
            await self.db.rollback()
