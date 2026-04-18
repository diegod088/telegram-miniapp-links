"""Activity service — logic for tracking events in the Pulse feed."""

import logging
from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.activity import Activity
from app.models.user import User

logger = logging.getLogger("app")

class ActivityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_activity(
        self,
        type: str,
        message: str,
        user_id: Optional[int] = None,
        target_id: Optional[str] = None,
        target_type: Optional[str] = None,
        is_public: bool = True
    ) -> Activity:
        """Create a new activity log entry."""
        try:
            activity = Activity(
                type=type,
                message=message,
                user_id=user_id,
                target_id=target_id,
                target_type=target_type,
                is_public=is_public
            )
            self.db.add(activity)
            await self.db.flush()
            return activity
        except Exception as e:
            logger.error(f"Failed to record activity {type}: {e}")
            return None

    async def get_pulse_feed(self, limit: int = 30) -> List[Activity]:
        """Get the latest public activities."""
        stmt = (
            select(Activity)
            .where(Activity.is_public == True)
            .options(selectinload(Activity.user))
            .order_by(desc(Activity.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
