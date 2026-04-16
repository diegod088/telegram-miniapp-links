from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Fetch a user by their Telegram ID."""
        stmt = select(self.model).where(self.model.telegram_id == telegram_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
