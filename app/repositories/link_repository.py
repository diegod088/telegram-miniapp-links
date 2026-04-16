from typing import Optional, List, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.link import ProfileLink, LinkLike, LinkDislike
from app.repositories.base import BaseRepository


class LinkRepository(BaseRepository[ProfileLink]):
    def __init__(self, db: AsyncSession):
        super().__init__(ProfileLink, db)

    async def get_by_profile_id(self, profile_id: int, include_locks: bool = True) -> List[ProfileLink]:
        """Fetch all links for a specific profile, ordered by position."""
        stmt = (
            select(self.model)
            .where(self.model.profile_id == profile_id)
            .order_by(self.model.position.asc())
        )
        if include_locks:
            stmt = stmt.options(selectinload(ProfileLink.locks))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_like(self, user_id: int, link_id: int) -> Optional[LinkLike]:
        """Check if a user has liked a link."""
        stmt = select(LinkLike).where(
            and_(LinkLike.user_id == user_id, LinkLike.link_id == link_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def add_like(self, user_id: int, link_id: int) -> LinkLike:
        """Add a like from a user to a link."""
        like = LinkLike(user_id=user_id, link_id=link_id)
        self.db.add(like)
        
        # Increment link like count
        await self.db.execute(
            ProfileLink.__table__.update()
            .where(ProfileLink.id == link_id)
            .values(likes=ProfileLink.likes + 1)
        )
        return like

    async def get_dislike(self, user_id: int, link_id: int) -> Optional[LinkDislike]:
        """Check if a user has disliked a link."""
        stmt = select(LinkDislike).where(
            and_(LinkDislike.user_id == user_id, LinkDislike.link_id == link_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def add_dislike(self, user_id: int, link_id: int) -> LinkDislike:
        """Add a dislike from a user to a link."""
        dislike = LinkDislike(user_id=user_id, link_id=link_id)
        self.db.add(dislike)
        
        # Increment link dislike count
        await self.db.execute(
            ProfileLink.__table__.update()
            .where(ProfileLink.id == link_id)
            .values(dislikes=ProfileLink.dislikes + 1)
        )
        return dislike

    async def get_top_links(self, category: Optional[str] = None, limit: int = 20) -> List[ProfileLink]:
        """Fetch top links ordered by likes."""
        stmt = (
            select(self.model)
            .where(self.model.is_active == True)
            .order_by(self.model.likes.desc(), self.model.created_at.desc())
            .limit(limit)
        )
        if category and category != "ALL":
            stmt = stmt.where(self.model.category == category)
            
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
