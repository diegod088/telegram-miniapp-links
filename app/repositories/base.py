from typing import Any, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """
        Base repository for common CRUD operations.
        
        Args:
            model: The SQLAlchemy model class.
            db: The async database session.
        """
        self.model = model
        self.db = db

    async def get(self, id: Any) -> Optional[ModelType]:
        """Fetch a single record by ID."""
        stmt = select(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(self, *, skip: int = 0, limit: int = 20) -> List[ModelType]:
        """Fetch multiple records with pagination."""
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> ModelType:
        """Create a new record."""
        obj = self.model(**kwargs)
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def update(self, id: Any, **kwargs) -> Optional[ModelType]:
        """Update an existing record."""
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**kwargs)
            .returning(self.model)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, id: Any) -> bool:
        """Delete a record by ID."""
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        return result.rowcount > 0
