from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.profile import Profile
from app.models.link import ProfileLink
from app.repositories.base import BaseRepository


class ProfileRepository(BaseRepository[Profile]):
    def __init__(self, db: AsyncSession):
        super().__init__(Profile, db)

    async def get_by_slug(self, slug: str, include_links: bool = False) -> Optional[Profile]:
        """Fetch a profile by slug."""
        stmt = select(self.model).where(self.model.slug == slug)
        if include_links:
            stmt = stmt.options(
                selectinload(Profile.links).selectinload(ProfileLink.locks)
            )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int, include_links: bool = False) -> Optional[Profile]:
        """Fetch the profile belonging to a specific user ID."""
        stmt = select(self.model).where(self.model.user_id == user_id)
        if include_links:
            stmt = stmt.options(
                selectinload(Profile.links).selectinload(ProfileLink.locks)
            )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_trending(self, limit: int = 20, offset: int = 0) -> List[Profile]:
        """Fetch public profiles ordered by total views and creation date."""
        stmt = (
            select(self.model)
            .where(self.model.is_public == True)
            .order_by(self.model.total_views.desc(), self.model.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_public(self) -> int:
        """Count total public profiles."""
        stmt = select(func.count()).select_from(self.model).where(self.model.is_public == True)
        result = await self.db.execute(stmt)
        return result.scalar() or 0
