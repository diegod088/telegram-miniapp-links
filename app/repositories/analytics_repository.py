from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.analytics import ClickEvent
from app.repositories.base import BaseRepository


class AnalyticsRepository(BaseRepository[ClickEvent]):
    def __init__(self, db: AsyncSession):
        super().__init__(ClickEvent, db)

    async def get_stats(
        self, 
        profile_id: int, 
        since: datetime,
        event_type: Optional[str] = None
    ) -> int:
        """Count events for a profile since a specific date."""
        stmt = select(func.count(self.model.id)).where(
            and_(
                self.model.profile_id == profile_id,
                self.model.created_at >= since
            )
        )
        if event_type:
            stmt = stmt.where(self.model.event_type == event_type)
            
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def get_unique_visitors(self, profile_id: int, since: datetime) -> int:
        """Count unique visitors by ip_hash."""
        stmt = (
            select(func.count(func.distinct(self.model.ip_hash)))
            .where(
                and_(
                    self.model.profile_id == profile_id,
                    self.model.created_at >= since,
                    self.model.ip_hash.isnot(None)
                )
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def get_top_performing_links(self, profile_id: int, since: datetime, limit: int = 10) -> List[Tuple[int, int]]:
        """Fetch top links by click count."""
        stmt = (
            select(
                self.model.link_id,
                func.count(self.model.id).label("view_count")
            )
            .where(
                and_(
                    self.model.profile_id == profile_id,
                    self.model.event_type == "link_click",
                    self.model.link_id.isnot(None),
                    self.model.created_at >= since
                )
            )
            .group_by(self.model.link_id)
            .order_by(func.count(self.model.id).desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return [(row.link_id, row.view_count) for row in result]
